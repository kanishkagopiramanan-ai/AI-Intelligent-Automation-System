"""Unit tests for Module 1: Excel Inventory AI Agent."""

import os
import sys
import unittest
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.data_loader import (
    detect_inventory_columns,
    calculate_inventory_summary,
    query_inventory_agent,
)
from utils.inventory_glossary import search_glossary


class TestInventoryAgent(unittest.TestCase):
    def setUp(self):
        # Create a sample DataFrame
        self.df = pd.DataFrame({
            "SKU": ["SKU-001", "SKU-002", "SKU-003", "SKU-004"],
            "Product_Name": ["Wireless Mouse", "Mechanical Keyboard", "USB-C Cable", "4K Monitor"],
            "Category": ["Accessories", "Accessories", "Cables", "Displays"],
            "Stock_Quantity": [50, 5, 100, 0],
            "Unit_Price": [25.0, 80.0, 10.0, 300.0],
            "Reorder_Level": [15, 10, 20, 5],
            "Supplier": ["LogiCorp", "KeyBrand", "CableCo", "ScreenTech"]
        })
        self.mapping = detect_inventory_columns(self.df)

    def test_column_detection(self):
        self.assertEqual(self.mapping["product_name"], "Product_Name")
        self.assertEqual(self.mapping["sku"], "SKU")
        self.assertEqual(self.mapping["quantity"], "Stock_Quantity")
        self.assertEqual(self.mapping["unit_price"], "Unit_Price")
        self.assertEqual(self.mapping["category"], "Category")
        self.assertEqual(self.mapping["reorder_level"], "Reorder_Level")

    def test_summary_calculation(self):
        summary = calculate_inventory_summary(self.df, self.mapping)
        self.assertEqual(summary["total_products"], 4)
        self.assertEqual(summary["total_stock_units"], 155)  # 50 + 5 + 100 + 0
        # Total value: (50*25) + (5*80) + (100*10) + (0*300) = 1250 + 400 + 1000 + 0 = 2650.0
        self.assertEqual(summary["total_valuation"], 2650.0)
        # Low stock: SKU-002 (stock 5 <= reorder 10)
        self.assertEqual(summary["low_stock_count"], 1)
        # Out of stock: SKU-004 (stock 0)
        self.assertEqual(summary["out_of_stock_count"], 1)

    def test_query_total_stock(self):
        res = query_inventory_agent(self.df, "What is the total stock?", self.mapping)
        self.assertTrue(res["success"])
        self.assertEqual(res["query_type"], "total_stock")
        self.assertIn("155", res["metric_value"])

    def test_query_most_expensive(self):
        res = query_inventory_agent(self.df, "Which item is the most expensive product?", self.mapping)
        self.assertTrue(res["success"])
        self.assertEqual(res["query_type"], "most_expensive")
        self.assertIn("4K Monitor", res["answer"])

    def test_query_low_stock(self):
        res = query_inventory_agent(self.df, "Show low stock items", self.mapping)
        self.assertTrue(res["success"])
        self.assertEqual(res["query_type"], "low_stock")
        self.assertIn("Mechanical Keyboard", str(res["data"]))

    def test_glossary_search(self):
        results = search_glossary("Safety Stock")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["term"], "Safety Stock")


if __name__ == "__main__":
    unittest.main()
