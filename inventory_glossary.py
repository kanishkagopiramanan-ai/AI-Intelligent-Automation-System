"""Inventory and Supply Chain Knowledge Glossary & Search Engine.

Supports definitions, business formulas, inventory health metrics, and column
context search for the Excel Inventory AI Agent (Module 1).
"""

from typing import Any, Dict, List

GLOSSARY_ITEMS: List[Dict[str, Any]] = [
    {
        "term": "Safety Stock",
        "category": "Risk Management",
        "definition": "A buffer of surplus stock kept on hand to mitigate the risk of stockouts caused by uncertainties in supply or surges in customer demand.",
        "formula": "(Maximum Daily Usage × Maximum Lead Time) - (Average Daily Usage × Average Lead Time)",
        "importance": "Prevents lost sales and maintains customer satisfaction during supply delays.",
        "example": "If daily sales average 10 units but peak at 25, keeping 50 units in safety stock protects against stockouts."
    },
    {
        "term": "Reorder Point (ROP)",
        "category": "Replenishment",
        "definition": "The specific inventory level that triggers the placement of a new purchase order to replenish stock before depletion.",
        "formula": "Reorder Point = (Lead Time Demand) + Safety Stock = (Average Daily Usage × Lead Time in Days) + Safety Stock",
        "importance": "Automates replenishment timing so stock arrives right as on-hand units approach safety stock.",
        "example": "If daily sales are 5 units, supplier lead time is 7 days, and safety stock is 10, ROP is (5 × 7) + 10 = 45 units."
    },
    {
        "term": "Economic Order Quantity (EOQ)",
        "category": "Optimization",
        "definition": "The ideal order quantity a company should purchase to minimize total inventory costs (ordering costs and holding costs).",
        "formula": "EOQ = √[(2 × Demand × Order Cost) / Holding Cost per Unit]",
        "importance": "Balances bulk purchase ordering discounts against high warehouse storage and carrying expenses.",
        "example": "Calculates whether ordering 500 units twice a year is cheaper than ordering 100 units ten times a year."
    },
    {
        "term": "Inventory Turnover Ratio",
        "category": "Performance Metrics",
        "definition": "A measurement of how many times inventory is sold and replaced over a defined period (usually a fiscal year or quarter).",
        "formula": "Inventory Turnover = Cost of Goods Sold (COGS) / Average Inventory Value",
        "importance": "Higher turnover signifies efficient inventory management and strong sales velocity; low turnover indicates overstocking.",
        "example": "A turnover of 6 means the business cycles through its full inventory value every 2 months."
    },
    {
        "term": "Days Sales of Inventory (DSI)",
        "category": "Performance Metrics",
        "definition": "The average number of days required for a business to turn its inventory into sales.",
        "formula": "DSI = (Average Inventory / COGS) × 365 days",
        "importance": "Also called Average Age of Inventory. Shorter DSI implies greater liquidity and lower storage costs.",
        "example": "A DSI of 30 days means products sit on shelves for approximately one month before being sold."
    },
    {
        "term": "Dead Stock / Obsolete Inventory",
        "category": "Inventory Health",
        "definition": "Goods stored in the warehouse that have not sold over an extended duration and are unlikely to sell at full price in the future.",
        "formula": "Items with 0 sales over > 90-180 days with remaining positive stock quantity.",
        "importance": "Ties up working capital and consumes physical shelf space; requires liquidation or write-offs.",
        "example": "Unsold previous-generation phone cases or expired seasonal items."
    },
    {
        "term": "Carrying Cost / Holding Cost",
        "category": "Cost Accounting",
        "definition": "The total cost of holding inventory over time, including warehousing, insurance, handling, taxes, depreciation, and opportunity cost of capital.",
        "formula": "Carrying Cost = (Total Carrying Expenses / Total Inventory Value) × 100% (typically 20% to 30% annually)",
        "importance": "Highlights the hidden expenses of keeping excess stock in storage.",
        "example": "Holding $100,000 of stock at 25% carrying cost equals $25,000 per year in overhead."
    },
    {
        "term": "ABC Analysis",
        "category": "Classification",
        "definition": "An inventory categorisation technique based on the Pareto Principle (80/20 rule) ranking items by consumption value.",
        "formula": "Category A: Top 70-80% of value (10-20% items); Category B: 15-25% of value (30% items); Category C: 5% of value (50% items).",
        "importance": "Helps inventory managers focus monitoring and security on high-value Tier A assets.",
        "example": "High-end smartphones are Category A, charging cables and screen guards are Category C."
    },
    {
        "term": "SKU (Stock Keeping Unit)",
        "category": "Identification",
        "definition": "A unique scannable alphanumeric code assigned to each distinct product item to track stock levels, variants, and locations internally.",
        "formula": "Custom internal code structure, e.g., 'ELEC-LAP-APL-001' (Category-Subcategory-Brand-ID).",
        "importance": "Eliminates ambiguity between product variants such as different sizes, colours, or specifications.",
        "example": "'SHIRT-BLU-M' vs 'SHIRT-RED-L'."
    },
    {
        "term": "Stockout / Out-of-Stock",
        "category": "Inventory Health",
        "definition": "An event where customer demand for an inventory item cannot be fulfilled because available on-hand stock has dropped to zero.",
        "formula": "Available Quantity == 0 while Demand > 0.",
        "importance": "Causes immediate revenue loss, poor customer ratings, and potentially permanent loss of clients to competitors.",
        "example": "A customer attempting to buy an item when the quantity on hand is 0."
    },
    {
        "term": "Lead Time",
        "category": "Supply Chain",
        "definition": "The total latency elapsed between placing a purchase order with a vendor and having the merchandise physically received and ready for sale.",
        "formula": "Lead Time = Order Processing Time + Supplier Production Time + Shipping Transit + Receiving/Inspection.",
        "importance": "Directly dictates necessary safety stock levels and reorder frequency.",
        "example": "A domestic supplier might have a 3-day lead time, while overseas shipping may require 45 days."
    },
    {
        "term": "Minimum Order Quantity (MOQ)",
        "category": "Procurement",
        "definition": "The lowest number of units a supplier or manufacturer is willing to sell in a single order transaction.",
        "formula": "Fixed threshold set by supplier contracts (e.g., MOQ = 100 units).",
        "importance": "Must be considered when calculating reorder quantities and warehouse capacity.",
        "example": "You need 25 items, but the factory will only manufacture and ship a minimum batch of 100."
    },
    {
        "term": "Shrinkage",
        "category": "Loss & Loss Prevention",
        "definition": "The difference between recorded inventory in the database and the actual physical stock verified during a physical audit.",
        "formula": "Shrinkage Rate = [(Book Value - Physical Value) / Book Value] × 100%",
        "importance": "Identifies losses stemming from shoplifting, employee theft, damage, supplier fraud, or administrative recording errors.",
        "example": "Your system records 100 headphones, but a physical count only discovers 94 (6 units lost)."
    },
    {
        "term": "FIFO (First-In, First-Out)",
        "category": "Valuation & Accounting",
        "definition": "An inventory valuation method assuming the oldest purchased goods are sold or used first.",
        "formula": "Cost of goods sold is assigned from the earliest acquired inventory batches.",
        "importance": "Mandatory or preferred for perishable goods, food, medicines, and in most IFRS/GAAP accounting standards.",
        "example": "Milk cartons bought on Monday are sold before milk cartons delivered on Thursday."
    },
    {
        "term": "Gross Margin Return on Investment (GMROI)",
        "category": "Financial Performance",
        "definition": "An inventory profitability ratio that analyzes a firm's ability to turn inventory into cash above the cost of the inventory.",
        "formula": "GMROI = Gross Margin $ / Average Inventory Cost $",
        "importance": "Determines whether an inventory investment produces adequate gross margin return.",
        "example": "A GMROI of 1.75 indicates $1.75 in gross margin produced for every $1.00 invested in stock."
    }
]


def search_glossary(query: str, category_filter: str = "All") -> List[Dict[str, Any]]:
    """Search inventory terminology by term, definition, category, or formula."""
    if not query and (category_filter == "All" or not category_filter):
        return GLOSSARY_ITEMS

    query_lower = query.lower().strip() if query else ""
    results = []

    for item in GLOSSARY_ITEMS:
        # Category filter check
        if category_filter and category_filter != "All" and item["category"] != category_filter:
            continue

        if not query_lower:
            results.append(item)
            continue

        # Text matching
        match_score = 0
        if query_lower in item["term"].lower():
            match_score += 10
        if query_lower in item["definition"].lower():
            match_score += 5
        if query_lower in item["category"].lower():
            match_score += 3
        if "formula" in item and query_lower in item["formula"].lower():
            match_score += 4
        if "importance" in item and query_lower in item["importance"].lower():
            match_score += 2

        # Token overlap check
        query_tokens = query_lower.split()
        for token in query_tokens:
            if len(token) > 2 and (
                token in item["term"].lower() or token in item["definition"].lower()
            ):
                match_score += 2

        if match_score > 0:
            item_copy = dict(item)
            item_copy["_match_score"] = match_score
            results.append(item_copy)

    # Sort by relevance score
    results.sort(key=lambda x: x.get("_match_score", 0), reverse=True)
    return results


def get_all_categories() -> List[str]:
    """Retrieve all unique glossary categories."""
    categories = sorted(list({item["category"] for item in GLOSSARY_ITEMS}))
    return ["All"] + categories


def get_column_context(column_name: str) -> Dict[str, str]:
    """Provides business context and best-practice advice for a given inventory column."""
    col_clean = column_name.lower().replace("_", " ").replace("-", " ")

    if any(k in col_clean for k in ["stock", "qty", "quantity", "on hand", "units"]):
        return {
            "concept": "Available Inventory Quantity",
            "business_meaning": "Current physical units available for immediate fulfillment in the warehouse or store.",
            "operational_advice": "Check against Reorder Point. If quantity <= Reorder Level, place a replenishment order immediately."
        }
    elif any(k in col_clean for k in ["price", "unit price", "cost", "mrp", "rate"]):
        return {
            "concept": "Unit Pricing / Valuation",
            "business_meaning": "Selling price or acquisition cost per single unit.",
            "operational_advice": "Multiplying Unit Price by Stock Quantity yields Total Inventory Asset Valuation."
        }
    elif any(k in col_clean for k in ["reorder", "rop", "safety", "min stock"]):
        return {
            "concept": "Replenishment Threshold",
            "business_meaning": "The trigger point beneath which inventory is classified as 'Low Stock'.",
            "operational_advice": "Ensure this number includes supplier lead-time demand plus safety buffer."
        }
    elif any(k in col_clean for k in ["category", "dept", "department", "type"]):
        return {
            "concept": "Inventory Classification / Department",
            "business_meaning": "Higher-level group organizing similar products for segmentation and ABC analysis.",
            "operational_advice": "Use category grouping to identify which product divisions tie up the highest capital."
        }
    elif any(k in col_clean for k in ["sku", "code", "id", "barcode"]):
        return {
            "concept": "Unique Stock Identification",
            "business_meaning": "Unique internal key preventing cross-item confusion.",
            "operational_advice": "Must remain unique per item variant across the supply chain."
        }
    elif any(k in col_clean for k in ["supplier", "vendor", "manufacturer"]):
        return {
            "concept": "Vendor Attribution",
            "business_meaning": "Source vendor responsible for supplying this stock batch.",
            "operational_advice": "Track vendor reliability, lead times, and aggregate order volumes for volume discounts."
        }
    else:
        return {
            "concept": "General Inventory Attribute",
            "business_meaning": f"Attribute field '{column_name}' containing product-specific operational metadata.",
            "operational_advice": "Inspect distribution and missing values during dataset health analysis."
        }
