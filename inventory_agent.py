"""Module 1: Excel Inventory AI Agent.

Features:
- Excel (.xlsx, .xls) and CSV inventory file upload.
- Automated column role detection (Product, SKU, Quantity, Price, Category, Reorder Level).
- Executive KPI summary cards (Total stock, Valuation, Low-stock alerts).
- Natural Language Question Answering grounded in real Pandas operations.
- Dynamic charts (Stock distribution, Category breakdown, Valuation).
- Supply Chain Knowledge Glossary & Column Context Search Tool.
- Safe, deterministic execution without arbitrary code execution (no eval/exec).
"""

import os
import pandas as pd
import streamlit as st
import altair as alt

from utils.data_loader import (
    load_inventory_dataset,
    detect_inventory_columns,
    calculate_inventory_summary,
    query_inventory_agent,
)
from utils.inventory_glossary import (
    search_glossary,
    get_all_categories,
    get_column_context,
)


def render_inventory_agent_tab():
    """Streamlit UI renderer for Module 1."""
    st.markdown("## 📊 Excel Inventory AI Agent")
    st.markdown(
        "Upload your inventory spreadsheet (Excel or CSV) to analyse stock levels, compute asset valuations, "
        "identify low-stock risks, and query the dataset in plain English."
    )

    # 1. File Upload Section
    col_up1, col_up2 = st.columns([3, 1])
    with col_up1:
        uploaded_file = st.file_uploader(
            "Upload Inventory Spreadsheet (.csv, .xlsx, .xls):",
            type=["csv", "xlsx", "xls"],
            key="inventory_file_uploader"
        )
    with col_up2:
        st.write("")
        st.write("")
        load_demo = st.button("📁 Load Demo Inventory Data", use_container_width=True)

    df: pd.DataFrame = None
    file_label = ""

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        df, err = load_inventory_dataset(file_bytes, uploaded_file.name)
        if err:
            st.error(f"Error loading file: {err}")
            return
        file_label = uploaded_file.name
    elif load_demo or st.session_state.get("use_demo_inventory", False):
        st.session_state["use_demo_inventory"] = True
        demo_path = os.path.join(os.path.dirname(__file__), "..", "demo_data", "sample_inventory.csv")
        if os.path.exists(demo_path):
            with open(demo_path, "rb") as f:
                df, err = load_inventory_dataset(f.read(), "sample_inventory.csv")
            file_label = "sample_inventory.csv (Synthetic Demo Dataset)"
        else:
            st.error("Demo dataset file not found.")
            return

    if df is None:
        st.info("👆 Please upload an inventory spreadsheet or click **'Load Demo Inventory Data'** to get started.")
        # Show glossary search tool even before file upload
        render_glossary_section()
        return

    # 2. Dataset Overview & Column Mapping
    st.success(f"Loaded **{file_label}** ({len(df)} rows, {len(df.columns)} columns)")

    mapping = detect_inventory_columns(df)
    summary = calculate_inventory_summary(df, mapping)

    # Top KPI Metrics Cards
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Products", f"{summary['total_products']:,}")
    k2.metric("Total Stock Units", f"{summary['total_stock_units']:,}")
    k3.metric("Inventory Valuation", f"${summary['total_valuation']:,.2f}")
    k4.metric("Low Stock Items", f"{summary['low_stock_count']}", delta="-Attention" if summary['low_stock_count'] > 0 else "Normal")
    k5.metric("Out of Stock", f"{summary['out_of_stock_count']}", delta="-Critical" if summary['out_of_stock_count'] > 0 else "Normal")

    # Column Mapping Inspector
    with st.expander("🔍 Detected Column Roles & Schema Mapping"):
        st.write("The AI Agent automatically identified the following operational roles:")
        map_cols = st.columns(len(mapping))
        for idx, (role, col_name) in enumerate(mapping.items()):
            role_label = role.replace("_", " ").title()
            val_display = f"`{col_name}`" if col_name else "*Not Found*"
            map_cols[idx % len(map_cols)].markdown(f"**{role_label}:**\n{val_display}")

    # Tabs inside Module 1: Ask Questions, Data Visuals, Raw Data, Glossary Search
    tab_query, tab_visuals, tab_data, tab_glossary = st.tabs([
        "💬 Plain English Query Assistant",
        "📈 Visual Analytics",
        "📋 Dataset Explorer",
        "📖 Inventory Knowledge & Glossary"
    ])

    # TAB 1: PLAIN ENGLISH QUERY ASSISTANT
    with tab_query:
        st.markdown("### Ask Questions About Your Inventory")
        st.markdown(
            "Type any question in natural language. The agent analyses the actual dataframe "
            "using verified, deterministic Pandas operations without executing arbitrary unsafe code."
        )

        # Quick Suggestion Chips
        st.caption("Quick question suggestions:")
        q_cols = st.columns(4)
        sample_questions = [
            "What is the total stock across all products?",
            "Which items are low in stock and need reorder?",
            "What is the most expensive product?",
            "Show breakdown of stock by category",
        ]

        preset_query = None
        for i, sample_q in enumerate(sample_questions):
            if q_cols[i].button(sample_q, key=f"sample_q_{i}", use_container_width=True):
                preset_query = sample_q

        user_query = st.text_input(
            "Enter your question:",
            value=preset_query if preset_query else "",
            placeholder="e.g., Which product has the highest stock? or Show low stock items",
            key="inventory_query_input"
        )

        if st.button("Analyse & Answer", type="primary", use_container_width=True) or user_query:
            if user_query.strip():
                with st.spinner("Analyzing dataset with Pandas..."):
                    result = query_inventory_agent(df, user_query, mapping)

                if result.get("success"):
                    st.markdown("---")
                    res_col1, res_col2 = st.columns([2, 1])

                    with res_col1:
                        st.markdown(f"#### 💡 {result.get('title', 'Analysis Result')}")
                        st.markdown(result["answer"])
                        st.info(f"**Explanation:** {result['explanation']}")

                    with res_col2:
                        if result.get("metric_value"):
                            st.metric(
                                label="Computed Metric",
                                value=result["metric_value"]
                            )

                    if result.get("data") is not None and isinstance(result["data"], pd.DataFrame):
                        st.markdown("##### 🔍 Supporting Dataset Records")
                        st.dataframe(result["data"], use_container_width=True)
                else:
                    st.warning(result.get("answer"))
                    st.info(result.get("explanation"))
            else:
                st.warning("Please type a question or select one of the suggestions above.")

    # TAB 2: VISUAL ANALYTICS
    with tab_visuals:
        st.markdown("### Inventory Distribution and Health")
        qty_col = mapping.get("quantity")
        cat_col = mapping.get("category")
        prod_col = mapping.get("product_name") or df.columns[0]
        price_col = mapping.get("unit_price")

        col_v1, col_v2 = st.columns(2)

        with col_v1:
            if cat_col and qty_col and cat_col in df.columns and qty_col in df.columns:
                st.markdown("#### Stock by Category")
                cat_summary = df.groupby(cat_col)[qty_col].sum().reset_index()
                st.bar_chart(cat_summary.set_index(cat_col), use_container_width=True)
            else:
                st.info("Category and Quantity columns required for category chart.")

        with col_v2:
            if prod_col and qty_col and prod_col in df.columns and qty_col in df.columns:
                st.markdown("#### Top 8 Products by Available Units")
                top_items = df.sort_values(by=qty_col, ascending=False).head(8)
                st.bar_chart(top_items.set_index(prod_col)[qty_col], use_container_width=True)
            else:
                st.info("Product name and Quantity columns required for top items chart.")

        if price_col and qty_col and price_col in df.columns and qty_col in df.columns:
            st.markdown("#### Price vs. Stock Scatter")
            chart_data = df[[prod_col, qty_col, price_col]].copy()
            chart = alt.Chart(chart_data).mark_circle(size=70).encode(
                x=alt.X(price_col, title="Unit Price ($)"),
                y=alt.Y(qty_col, title="Stock Quantity (Units)"),
                tooltip=[prod_col, qty_col, price_col]
            ).interactive()
            st.altair_chart(chart, use_container_width=True)

    # TAB 3: DATASET EXPLORER
    with tab_data:
        st.markdown("### Browse & Filter Records")
        filter_col1, filter_col2 = st.columns([2, 1])

        cat_col = mapping.get("category")
        selected_category = "All"
        if cat_col and cat_col in df.columns:
            categories = ["All"] + sorted([str(x) for x in df[cat_col].dropna().unique()])
            selected_category = filter_col1.selectbox("Filter by Category:", categories)

        search_kw = filter_col2.text_input("Search Keyword:", "")

        filtered_df = df.copy()
        if selected_category != "All" and cat_col:
            filtered_df = filtered_df[filtered_df[cat_col].astype(str) == selected_category]

        if search_kw.strip():
            kw = search_kw.strip().lower()
            mask = filtered_df.astype(str).apply(lambda row: row.str.lower().str.contains(kw).any(), axis=1)
            filtered_df = filtered_df[mask]

        st.caption(f"Showing {len(filtered_df)} of {len(df)} total rows")
        st.dataframe(filtered_df, use_container_width=True)

    # TAB 4: GLOSSARY SEARCH
    with tab_glossary:
        render_glossary_section(df=df)


def render_glossary_section(df: Optional[pd.DataFrame] = None):
    """Renders the Supply Chain Glossary & Column Context Search Tool."""
    st.markdown("### 📖 Inventory & Supply Chain Knowledge Tool")
    st.markdown(
        "Search definitions, mathematical formulas, and operational best practices for key "
        "inventory management concepts and column attributes."
    )

    g_col1, g_col2 = st.columns([2, 1])
    with g_col1:
        glossary_search = st.text_input(
            "Search inventory terms (e.g., 'Safety Stock', 'EOQ', 'Turnover', 'Reorder'):",
            key="glossary_search_input"
        )
    with g_col2:
        categories = get_all_categories()
        selected_cat = st.selectbox("Filter Category:", categories, key="glossary_cat_filter")

    results = search_glossary(glossary_search, selected_cat)

    st.markdown(f"**Found {len(results)} relevant term(s):**")
    for item in results:
        with st.expander(f"📌 {item['term']} ({item['category']})", expanded=bool(glossary_search)):
            st.markdown(f"**Definition:** {item['definition']}")
            if "formula" in item:
                st.markdown(f"**Formula / Calculation:** `{item['formula']}`")
            if "importance" in item:
                st.markdown(f"**Operational Importance:** {item['importance']}")
            if "example" in item:
                st.markdown(f"**Real-world Example:** {item['example']}")

    # If a dataset is loaded, provide column context lookup
    if df is not None:
        st.markdown("---")
        st.markdown("#### 🎯 Active Dataset Column Context Inspector")
        st.markdown("Select any column from your uploaded spreadsheet to view its operational role:")

        selected_col = st.selectbox("Inspect Column:", list(df.columns), key="col_inspector_select")
        if selected_col:
            context = get_column_context(selected_col)
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown(f"**Concept:** `{context['concept']}`")
                st.markdown(f"**Business Meaning:** {context['business_meaning']}")
            with c2:
                st.markdown(f"**Operational Advice:** {context['operational_advice']}")
