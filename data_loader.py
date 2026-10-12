"""Data loader and inventory query engine for Excel/CSV inventory analysis.

Provides robust dataset loading, column mapping, safe deterministic analysis,
and natural language query parsing without unsafe code execution.
"""

import io
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd


def load_inventory_dataset(
    file_bytes_or_buffer: Union[bytes, io.BytesIO],
    filename: str
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Safely load a CSV or Excel dataset into a pandas DataFrame.

    Returns (df, error_message).
    """
    try:
        if isinstance(file_bytes_or_buffer, bytes):
            buffer = io.BytesIO(file_bytes_or_buffer)
        else:
            buffer = file_bytes_or_buffer

        filename_lower = filename.lower()
        if filename_lower.endswith(".csv"):
            try:
                df = pd.read_csv(buffer, encoding="utf-8")
            except UnicodeDecodeError:
                buffer.seek(0)
                df = pd.read_csv(buffer, encoding="latin1")
        elif filename_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(buffer)
        else:
            return None, f"Unsupported file extension for '{filename}'. Please upload a .csv, .xlsx, or .xls file."

        # Strip whitespace from column headers
        df.columns = [str(c).strip() for c in df.columns]

        if df.empty:
            return None, "The uploaded inventory file is empty."

        return df, None
    except Exception as e:
        return None, f"Failed to parse dataset: {str(e)}"


def detect_inventory_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """Intelligently detects column roles based on header names and data types."""
    cols = list(df.columns)
    mapping = {
        "product_name": None,
        "sku": None,
        "quantity": None,
        "unit_price": None,
        "category": None,
        "reorder_level": None,
        "supplier": None,
    }

    # Helper match function
    def find_best_match(candidates: List[str], numeric_preferred: bool = False) -> Optional[str]:
        # Exact/prefix match first
        for col in cols:
            col_norm = re.sub(r"[^a-z0-9]", "", col.lower())
            for cand in candidates:
                cand_norm = re.sub(r"[^a-z0-9]", "", cand.lower())
                if col_norm == cand_norm:
                    if numeric_preferred and not pd.api.types.is_numeric_dtype(df[col]):
                        continue
                    return col
        # Substring match
        for col in cols:
            col_norm = re.sub(r"[^a-z0-9]", "", col.lower())
            for cand in candidates:
                cand_norm = re.sub(r"[^a-z0-9]", "", cand.lower())
                if cand_norm in col_norm:
                    if numeric_preferred and not pd.api.types.is_numeric_dtype(df[col]):
                        continue
                    return col
        return None

    mapping["product_name"] = find_best_match(
        ["product_name", "product", "item_name", "item", "title", "description", "name"]
    )
    mapping["sku"] = find_best_match(
        ["sku", "product_id", "item_id", "part_number", "item_code", "code", "barcode"]
    )
    mapping["quantity"] = find_best_match(
        ["quantity", "stock_quantity", "stock", "qty", "on_hand", "units", "inventory", "available_stock"],
        numeric_preferred=True
    )
    # If not found with numeric, try without strict numeric requirement (might be strings of numbers)
    if not mapping["quantity"]:
        mapping["quantity"] = find_best_match(
            ["quantity", "stock_quantity", "stock", "qty", "on_hand", "units", "inventory"]
        )

    mapping["unit_price"] = find_best_match(
        ["unit_price", "price", "cost", "unit_cost", "mrp", "rate", "selling_price"],
        numeric_preferred=True
    )
    if not mapping["unit_price"]:
        mapping["unit_price"] = find_best_match(
            ["unit_price", "price", "cost", "unit_cost", "mrp", "rate", "selling_price"]
        )

    mapping["category"] = find_best_match(
        ["category", "department", "dept", "product_type", "type", "group", "class"]
    )
    mapping["reorder_level"] = find_best_match(
        ["reorder_level", "reorder_point", "rop", "minimum_stock", "min_stock", "safety_stock", "threshold"],
        numeric_preferred=True
    )
    mapping["supplier"] = find_best_match(
        ["supplier", "vendor", "distributor", "manufacturer", "source"]
    )

    return mapping


def calculate_inventory_summary(
    df: pd.DataFrame,
    mapping: Optional[Dict[str, Optional[str]]] = None
) -> Dict[str, Any]:
    """Computes comprehensive inventory KPIs based on available columns."""
    if mapping is None:
        mapping = detect_inventory_columns(df)

    total_rows = len(df)
    qty_col = mapping.get("quantity")
    price_col = mapping.get("unit_price")
    reorder_col = mapping.get("reorder_level")
    cat_col = mapping.get("category")

    total_stock_units = 0
    total_valuation = 0.0
    low_stock_count = 0
    out_of_stock_count = 0
    avg_price = 0.0

    # Ensure quantity is numeric
    if qty_col and qty_col in df.columns:
        numeric_qty = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
        total_stock_units = int(numeric_qty.sum())
        out_of_stock_count = int((numeric_qty <= 0).sum())

        if reorder_col and reorder_col in df.columns:
            numeric_reorder = pd.to_numeric(df[reorder_col], errors="coerce").fillna(10)
            low_stock_count = int(((numeric_qty <= numeric_reorder) & (numeric_qty > 0)).sum())
        else:
            # Default low stock threshold if column absent: <= 10
            low_stock_count = int(((numeric_qty <= 10) & (numeric_qty > 0)).sum())

    # Ensure price is numeric
    if price_col and price_col in df.columns:
        numeric_price = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
        avg_price = float(numeric_price.mean()) if len(numeric_price) > 0 else 0.0

        if qty_col and qty_col in df.columns:
            numeric_qty = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
            total_valuation = float((numeric_qty * numeric_price).sum())

    # Unique categories count
    categories_count = int(df[cat_col].nunique()) if cat_col and cat_col in df.columns else None

    return {
        "total_products": total_rows,
        "total_stock_units": total_stock_units,
        "total_valuation": round(total_valuation, 2),
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "average_unit_price": round(avg_price, 2),
        "unique_categories": categories_count,
        "column_mapping": mapping
    }


def query_inventory_agent(
    df: pd.DataFrame,
    user_query: str,
    mapping: Optional[Dict[str, Optional[str]]] = None
) -> Dict[str, Any]:
    """Deterministic, safe Natural Language Query Processor for inventory data.

    Processes user questions accurately without using unsafe `eval()` or `exec()`.
    Guarantees that results are derived directly from the real dataframe.
    """
    if mapping is None:
        mapping = detect_inventory_columns(df)

    q = user_query.lower().strip()
    qty_col = mapping.get("quantity")
    price_col = mapping.get("unit_price")
    prod_col = mapping.get("product_name") or df.columns[0]
    cat_col = mapping.get("category")
    reorder_col = mapping.get("reorder_level")
    sku_col = mapping.get("sku")

    # Clean working copy with sanitized numeric values where appropriate
    work_df = df.copy()
    if qty_col and qty_col in work_df.columns:
        work_df["_numeric_qty"] = pd.to_numeric(work_df[qty_col], errors="coerce").fillna(0)
    else:
        work_df["_numeric_qty"] = 0

    if price_col and price_col in work_df.columns:
        work_df["_numeric_price"] = pd.to_numeric(work_df[price_col], errors="coerce").fillna(0)
        work_df["_total_value"] = work_df["_numeric_qty"] * work_df["_numeric_price"]
    else:
        work_df["_numeric_price"] = 0.0
        work_df["_total_value"] = 0.0

    if reorder_col and reorder_col in work_df.columns:
        work_df["_numeric_reorder"] = pd.to_numeric(work_df[reorder_col], errors="coerce").fillna(10)
    else:
        work_df["_numeric_reorder"] = 10

    # 1. TOTAL STOCK / UNITS
    if any(k in q for k in ["total stock", "total quantity", "total units", "how many items in stock", "sum of stock", "all stock"]):
        if not qty_col:
            return {
                "success": False,
                "answer": "Cannot calculate total stock because no numeric 'Quantity' or 'Stock' column was detected in the dataset.",
                "explanation": "Please ensure the dataset contains a column named 'Quantity', 'Stock', or 'Qty'.",
                "data": None
            }
        total_units = int(work_df["_numeric_qty"].sum())
        return {
            "success": True,
            "query_type": "total_stock",
            "title": "Total Stock Units",
            "metric_value": f"{total_units:,} units",
            "answer": f"The total stock quantity across all products in the inventory is **{total_units:,} units**.",
            "explanation": f"Calculated by summing all values in column '{qty_col}' across all {len(df)} inventory records.",
            "data": work_df[[prod_col, qty_col]].head(10) if prod_col in work_df.columns else None
        }

    # 2. TOTAL PRODUCTS / COUNT
    if any(k in q for k in ["how many products", "total products", "number of products", "product count", "total items"]):
        total_count = len(work_df)
        return {
            "success": True,
            "query_type": "product_count",
            "title": "Total Product Count",
            "metric_value": f"{total_count} products",
            "answer": f"There are **{total_count} distinct products** catalogued in this inventory file.",
            "explanation": f"Calculated as the total row count of the active inventory dataset.",
            "data": work_df.head(10)
        }

    # 3. TOTAL INVENTORY VALUE / VALUATION
    if any(k in q for k in ["total value", "total valuation", "worth of inventory", "asset value", "how much is the inventory worth"]):
        if not price_col or not qty_col:
            missing = []
            if not qty_col: missing.append("Quantity")
            if not price_col: missing.append("Price")
            return {
                "success": False,
                "answer": f"Cannot calculate total inventory valuation because the following required column(s) are missing: {', '.join(missing)}.",
                "explanation": "Inventory valuation requires multiplying Quantity by Unit Price for each product.",
                "data": None
            }
        total_val = float(work_df["_total_value"].sum())
        return {
            "success": True,
            "query_type": "total_valuation",
            "title": "Total Inventory Valuation",
            "metric_value": f"${total_val:,.2f}",
            "answer": f"The total monetary value of current inventory on hand is **${total_val:,.2f}**.",
            "explanation": f"Calculated as the sum of ({qty_col} × {price_col}) for all products in the dataset.",
            "data": work_df[[prod_col, qty_col, price_col, "_total_value"]].rename(columns={"_total_value": "Line Total Value"}).head(10)
        }

    # 4. LOW STOCK / REORDER ITEMS
    if any(k in q for k in ["low stock", "reorder", "running low", "critical stock", "need reorder", "below reorder"]):
        if not qty_col:
            return {
                "success": False,
                "answer": "Cannot determine low-stock items because no 'Quantity' or 'Stock' column was found.",
                "explanation": "Low stock identification requires a numeric quantity column.",
                "data": None
            }
        low_df = work_df[work_df["_numeric_qty"] <= work_df["_numeric_reorder"]]
        count = len(low_df)
        cols_to_show = [c for c in [prod_col, sku_col, qty_col, reorder_col, cat_col] if c and c in work_df.columns]
        return {
            "success": True,
            "query_type": "low_stock",
            "title": "Low Stock Alerts",
            "metric_value": f"{count} items",
            "answer": f"Found **{count} item(s)** currently at or below their reorder threshold.",
            "explanation": f"Filtered where {qty_col} is less than or equal to {reorder_col if reorder_col else 'the threshold of 10 units'}.",
            "data": low_df[cols_to_show] if not low_df.empty else pd.DataFrame({"Notice": ["All items are safely above reorder threshold."]})
        }

    # 5. OUT OF STOCK ITEMS
    if any(k in q for k in ["out of stock", "zero stock", "depleted", "no stock", "stockout"]):
        if not qty_col:
            return {
                "success": False,
                "answer": "Cannot determine out-of-stock items without a quantity column.",
                "explanation": "Out of stock identification requires checking where Quantity <= 0.",
                "data": None
            }
        oos_df = work_df[work_df["_numeric_qty"] <= 0]
        count = len(oos_df)
        cols_to_show = [c for c in [prod_col, sku_col, qty_col, cat_col] if c and c in work_df.columns]
        return {
            "success": True,
            "query_type": "out_of_stock",
            "title": "Out of Stock Items",
            "metric_value": f"{count} items",
            "answer": f"There are **{count} item(s)** completely out of stock (quantity is 0 or negative).",
            "explanation": f"Filtered records where column '{qty_col}' <= 0.",
            "data": oos_df[cols_to_show] if not oos_df.empty else pd.DataFrame({"Notice": ["No out-of-stock items found in current inventory."]})
        }

    # 6. MOST EXPENSIVE PRODUCT
    if any(k in q for k in ["most expensive", "highest price", "maximum price", "priciest", "costliest"]):
        if not price_col:
            return {
                "success": False,
                "answer": "Price information is not available in this dataset.",
                "explanation": "No numeric price column detected.",
                "data": None
            }
        idx = work_df["_numeric_price"].idxmax()
        top_row = work_df.loc[idx]
        item_name = top_row.get(prod_col, "Unknown")
        max_p = float(top_row["_numeric_price"])
        return {
            "success": True,
            "query_type": "most_expensive",
            "title": "Most Expensive Product",
            "metric_value": f"${max_p:,.2f}",
            "answer": f"The most expensive product is **{item_name}** priced at **${max_p:,.2f}**.",
            "explanation": f"Found by finding the maximum value in '{price_col}' across all inventory records.",
            "data": work_df.sort_values(by="_numeric_price", ascending=False)[[c for c in [prod_col, price_col, qty_col, cat_col] if c and c in work_df.columns]].head(5)
        }

    # 7. CHEAPEST PRODUCT
    if any(k in q for k in ["cheapest", "lowest price", "least expensive", "minimum price"]):
        if not price_col:
            return {
                "success": False,
                "answer": "Price information is not available in this dataset.",
                "explanation": "No numeric price column detected.",
                "data": None
            }
        # Filter positive prices
        pos_df = work_df[work_df["_numeric_price"] > 0]
        if pos_df.empty:
            pos_df = work_df
        idx = pos_df["_numeric_price"].idxmin()
        low_row = pos_df.loc[idx]
        item_name = low_row.get(prod_col, "Unknown")
        min_p = float(low_row["_numeric_price"])
        return {
            "success": True,
            "query_type": "cheapest",
            "title": "Cheapest Product",
            "metric_value": f"${min_p:,.2f}",
            "answer": f"The cheapest product is **{item_name}** priced at **${min_p:,.2f}**.",
            "explanation": f"Identified by locating the lowest non-zero unit price in '{price_col}'.",
            "data": pos_df.sort_values(by="_numeric_price", ascending=True)[[c for c in [prod_col, price_col, qty_col, cat_col] if c and c in pos_df.columns]].head(5)
        }

    # 8. HIGHEST STOCK / MOST STOCKED
    if any(k in q for k in ["highest stock", "most stock", "maximum stock", "most units", "highest quantity"]):
        if not qty_col:
            return {
                "success": False,
                "answer": "Quantity column not found in this dataset.",
                "explanation": "Cannot calculate highest stock without a quantity column.",
                "data": None
            }
        idx = work_df["_numeric_qty"].idxmax()
        top_row = work_df.loc[idx]
        item_name = top_row.get(prod_col, "Unknown")
        max_q = int(top_row["_numeric_qty"])
        return {
            "success": True,
            "query_type": "highest_stock",
            "title": "Most Stocked Item",
            "metric_value": f"{max_q:,} units",
            "answer": f"The product with the highest on-hand stock is **{item_name}** with **{max_q:,} units**.",
            "explanation": f"Computed by finding the peak value in '{qty_col}'.",
            "data": work_df.sort_values(by="_numeric_qty", ascending=False)[[c for c in [prod_col, qty_col, price_col, cat_col] if c and c in work_df.columns]].head(5)
        }

    # 9. CATEGORY BREAKDOWN / BREAKDOWN BY CATEGORY
    if any(k in q for k in ["category", "categories", "department", "by category", "breakdown"]):
        if not cat_col:
            return {
                "success": False,
                "answer": "Category column not found in this dataset.",
                "explanation": "No category or department column was detected to group by.",
                "data": None
            }
        grouped = work_df.groupby(cat_col).agg(
            Product_Count=(prod_col, "count"),
            Total_Units=("_numeric_qty", "sum"),
            Total_Valuation=("_total_value", "sum")
        ).reset_index().sort_values(by="Total_Units", ascending=False)

        top_cat = grouped.iloc[0][cat_col] if not grouped.empty else "None"
        return {
            "success": True,
            "query_type": "category_breakdown",
            "title": "Category Breakdown",
            "metric_value": f"{len(grouped)} categories",
            "answer": f"Inventory spans **{len(grouped)} categories**. The largest category by unit count is **{top_cat}**.",
            "explanation": f"Aggregated counts and stock quantities grouped by column '{cat_col}'.",
            "data": grouped
        }

    # 10. AVERAGE PRICE OR AVERAGE STOCK
    if "average price" in q or "avg price" in q or "mean price" in q:
        if not price_col:
            return {"success": False, "answer": "Price column not found.", "explanation": "Cannot compute average price.", "data": None}
        avg_p = float(work_df["_numeric_price"].mean())
        return {
            "success": True,
            "query_type": "average_price",
            "title": "Average Unit Price",
            "metric_value": f"${avg_p:,.2f}",
            "answer": f"The average unit price across all products is **${avg_p:,.2f}**.",
            "explanation": f"Calculated as the mean of all non-null entries in '{price_col}'.",
            "data": work_df[[c for c in [prod_col, price_col] if c in work_df.columns]].describe().reset_index()
        }

    # 11. SEARCH FOR SPECIFIC PRODUCT OR KEYWORD
    # Check if user mentioned an exact product or SKU
    found_matches = []
    # Search in product name and sku
    for _, row in work_df.iterrows():
        prod_val = str(row.get(prod_col, "")).lower()
        sku_val = str(row.get(sku_col, "")).lower() if sku_col else ""
        # Check tokens of user query
        tokens = [t for t in re.findall(r"\b\w+\b", q) if len(t) > 3 and t not in ["what", "show", "tell", "much", "many", "does", "have", "about", "product", "item", "stock"]]
        for t in tokens:
            if t in prod_val or (sku_val and t in sku_val):
                found_matches.append(row)
                break

    if found_matches:
        match_df = pd.DataFrame(found_matches).drop(columns=["_numeric_qty", "_numeric_price", "_total_value", "_numeric_reorder"], errors="ignore").drop_duplicates()
        first_row = match_df.iloc[0]
        prod_name = first_row.get(prod_col, "Item")
        qty_val = first_row.get(qty_col, "N/A") if qty_col else "N/A"
        price_val = first_row.get(price_col, "N/A") if price_col else "N/A"
        return {
            "success": True,
            "query_type": "product_search",
            "title": f"Search Results for '{prod_name}'",
            "metric_value": f"{len(match_df)} matching item(s)",
            "answer": f"Found **{len(match_df)} matching item(s)**. Top match is **{prod_name}** with **{qty_val} units** in stock at **${price_val}** each.",
            "explanation": f"Searched product catalog records matching query terms.",
            "data": match_df
        }

    # Fallback / General overview
    summary = calculate_inventory_summary(df, mapping)
    return {
        "success": True,
        "query_type": "general_overview",
        "title": "General Inventory Overview",
        "metric_value": f"{summary['total_products']} products",
        "answer": (
            f"Here is the summary of your inventory dataset:\n\n"
            f"- **Total Products Catalogued:** {summary['total_products']}\n"
            f"- **Total Units in Stock:** {summary['total_stock_units']:,}\n"
            f"- **Estimated Inventory Valuation:** ${summary['total_valuation']:,.2f}\n"
            f"- **Items Requiring Reorder (Low Stock):** {summary['low_stock_count']}\n"
            f"- **Depleted Items (Out of Stock):** {summary['out_of_stock_count']}"
        ),
        "explanation": "Showing comprehensive inventory overview. Try asking: 'What is the total stock?', 'Which item is most expensive?', 'Show low stock items', or 'Breakdown by category'.",
        "data": work_df[[c for c in [prod_col, qty_col, price_col, cat_col] if c and c in work_df.columns]].head(10)
    }
