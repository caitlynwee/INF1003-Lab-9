"""Automated Lab 9 checks, suitable for local runs, Docker, and CI."""

import ast
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from csv_loader import load_products
from digital_product import DigitalProduct
from discount_strategy import (
    BulkDiscount, DiscountStrategy, NoDiscount, PercentageDiscount, StudentDiscount,
)
from file_handling import load_inventory, save_inventory
from input_helpers import get_positive_float
from inventory import Inventory
from order import Order
from order_line import OrderLine
from physical_product import PhysicalProduct
from product_factory import ProductFactory
from supplier import Supplier


class Lab9Tests(TestCase):
    def setUp(self) -> None:
        self.supplier = Supplier("S001", "Tech Supplier", "tech@example.com")
        self.product = ProductFactory.create("physical", "P500", "Test Item", 125, 10,
                                             self.supplier, weight=2.5)

    def make_250_order(self, discount=None) -> Order:
        order = Order("O001", discount)
        order.add_order_line(self.product, 2)
        return order

    def test_default_no_discount(self) -> None:
        order = self.make_250_order()
        self.assertIsInstance(order.discount, NoDiscount)
        self.assertEqual(order.calculate_total(), 250)

    def test_explicit_no_discount(self) -> None:
        self.assertEqual(self.make_250_order(NoDiscount()).calculate_total(), 250)

    def test_percentage_discount(self) -> None:
        self.assertAlmostEqual(self.make_250_order(PercentageDiscount(10)).calculate_total(), 225)

    def test_bulk_discount_above_threshold(self) -> None:
        self.assertAlmostEqual(self.make_250_order(BulkDiscount(200, 20)).calculate_total(), 230)

    def test_bulk_discount_below_threshold(self) -> None:
        self.assertAlmostEqual(self.make_250_order(BulkDiscount(300, 20)).calculate_total(), 250)

    def test_bulk_discount_never_negative(self) -> None:
        self.assertEqual(BulkDiscount(0, 999).apply(100), 0)

    def test_strategy_can_be_changed_later(self) -> None:
        order = self.make_250_order(BulkDiscount(200, 20))
        self.assertEqual(order.calculate_total(), 230)
        order.set_discount(PercentageDiscount(10))
        self.assertEqual(order.calculate_total(), 225)

    def test_fourth_strategy_student(self) -> None:
        self.assertAlmostEqual(self.make_250_order(StudentDiscount()).calculate_total(), 237.5)

    def test_custom_strategy_works_without_changing_order(self) -> None:
        class FixedDiscount(DiscountStrategy):
            def apply(self, total: float) -> float:
                return total - 5

        self.assertEqual(self.make_250_order(FixedDiscount()).calculate_total(), 245)

    def test_shared_strategy_is_association(self) -> None:
        shared = PercentageDiscount(10)
        first, second = Order("O1", shared), Order("O2", shared)
        self.assertIs(first.discount, second.discount)

    def test_rejects_invalid_discount_object(self) -> None:
        with self.assertRaises(TypeError):
            Order("O1", "percentage")
        with self.assertRaises(TypeError):
            Order("O2").set_discount(None)

    def test_discount_parameter_validation(self) -> None:
        for invalid in (-5, 101, float("nan"), float("inf"), "ten", True):
            with self.subTest(value=repr(invalid)), self.assertRaises(ValueError):
                PercentageDiscount(invalid)
        for invalid in (-1, float("nan"), float("inf"), True):
            with self.subTest(value=repr(invalid)), self.assertRaises(ValueError):
                BulkDiscount(invalid, 20)
            with self.subTest(amount=repr(invalid)), self.assertRaises(ValueError):
                BulkDiscount(200, invalid)

    def test_product_factory_creates_correct_subclass(self) -> None:
        physical = ProductFactory.create("physical", "P001", "Lamp", 25, 10,
                                         self.supplier, weight=1.3)
        digital = ProductFactory.create("digital", "D001", "App", 49.90, 100,
                                        self.supplier, download_size=15.2)
        self.assertIsInstance(physical, PhysicalProduct)
        self.assertIsInstance(digital, DigitalProduct)
        self.assertEqual(physical.weight, 1.3)
        self.assertEqual(digital.download_size, 15.2)
        self.assertIs(physical.supplier, digital.supplier)

    def test_factory_defaults_extra_attributes_to_zero_for_csv(self) -> None:
        self.assertEqual(ProductFactory.create("physical", "P001", "Lamp", 25, 10,
                                               self.supplier).weight, 0)
        self.assertEqual(ProductFactory.create("digital", "D001", "App", 25, 10,
                                               self.supplier).download_size, 0)

    def test_unknown_product_type_raises_clear_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown product type: service"):
            ProductFactory.create("service", "S001", "Installation", 30, 5, self.supplier)

    def test_price_must_be_strictly_positive(self) -> None:
        for invalid in (0, -1, float("nan"), float("inf"), "abc", True):
            with self.subTest(price=repr(invalid)), self.assertRaises(ValueError):
                ProductFactory.create("digital", "D001", "App", invalid, 1, self.supplier)

    def test_stock_must_be_non_negative_integer(self) -> None:
        for invalid in (-1, 1.5, "5", True):
            with self.subTest(stock=repr(invalid)), self.assertRaises(ValueError):
                ProductFactory.create("physical", "P001", "Lamp", 5, invalid, self.supplier)
        with self.assertRaises(ValueError):
            self.product.update_stock(-1)

    def test_order_line_quantity_must_be_positive_integer(self) -> None:
        for invalid in (0, -1, 1.5, "2", True):
            with self.subTest(quantity=repr(invalid)), self.assertRaises(ValueError):
                OrderLine(self.product, invalid)

    def test_positive_price_helper_retries_three_inputs(self) -> None:
        captured = StringIO()
        with patch("builtins.input", side_effect=["abc", "-5", "12.50"]):
            with redirect_stdout(captured):
                result = get_positive_float("Price: ")
        self.assertEqual(result, 12.5)
        self.assertEqual(captured.getvalue().splitlines(), [
            "Please enter a valid number, e.g. 12.50",
            "Please enter a number greater than zero.",
        ])

    def test_positive_price_helper_rejects_nan_inf_and_zero(self) -> None:
        with patch("builtins.input", side_effect=["nan", "inf", "0", "5"]):
            with redirect_stdout(StringIO()) as captured:
                value = get_positive_float("Price: ")
        self.assertEqual(value, 5.0)
        self.assertEqual(captured.getvalue().count("Please enter a number greater than zero."), 3)

    def test_csv_sample_skips_two_invalid_rows_and_loads_three(self) -> None:
        inventory = Inventory()
        sample = Path(__file__).resolve().parent.parent / "products.csv"
        with redirect_stdout(StringIO()) as captured:
            load_products(str(sample), inventory, self.supplier)
        text = captured.getvalue()
        self.assertEqual([p.product_id for p in inventory.products], ["P001", "D001", "P003"])
        self.assertIn("Skipping row 4: Unknown product type: service", text)
        self.assertIn("Skipping row 5: could not convert string to float", text)
        self.assertTrue(text.endswith("3 products loaded.\nLoad attempt finished.\n"))

    def test_csv_missing_file_catches_file_not_found_and_runs_finally(self) -> None:
        with TemporaryDirectory() as folder:
            location = Path(folder) / "missing.csv"
            with redirect_stdout(StringIO()) as captured:
                load_products(str(location), Inventory(), self.supplier)
        self.assertEqual(captured.getvalue().splitlines(), [
            f"Products file not found: {location}",
            "Load attempt finished.",
        ])

    def test_csv_duplicate_bad_stock_bad_price_and_short_row(self) -> None:
        data = """product_type,product_id,name,price,stock_quantity
physical,P1,Lamp,10,1
physical,P1,Duplicate,20,3
digital,D2,Bad Stock,20,-1
digital,D3,Bad Price,0,1
physical,P9,Too Few,25
physical,P4,Valid,30,0
"""
        with TemporaryDirectory() as folder:
            path = Path(folder) / "mixed.csv"
            path.write_text(data, encoding="utf-8")
            inventory = Inventory()
            with redirect_stdout(StringIO()) as captured:
                load_products(str(path), inventory, self.supplier)
        self.assertEqual([p.product_id for p in inventory.products], ["P1", "P4"])
        self.assertEqual(captured.getvalue().count("Skipping row"), 4)
        self.assertIn("2 products loaded.", captured.getvalue())

    def test_json_loading_uses_factory_and_preserves_extra_fields(self) -> None:
        stock = Inventory()
        stock.add_product(self.product)
        stock.add_product(ProductFactory.create("digital", "D500", "App", 50, 100,
                                                 self.supplier, download_size=99))
        with TemporaryDirectory() as folder:
            path = Path(folder) / "inventory.json"
            save_inventory(stock, path)
            loaded = load_inventory(path)
        self.assertEqual(loaded.find_product("P500").weight, 2.5)
        self.assertEqual(loaded.find_product("D500").download_size, 99)
        self.assertIs(loaded.find_product("P500").supplier, loaded.find_product("D500").supplier)

    def test_json_loading_rejects_unknown_factory_type(self) -> None:
        record = {
            "product_id": "S1", "name": "service", "price": 20, "stock": 1,
            "type": "service", "supplier": self.supplier.to_dict(),
        }
        with TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text(json.dumps([record]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unknown product type: service"):
                load_inventory(path)

    def test_order_has_no_discount_selection_branches(self) -> None:
        """Enforce the lab's open/closed design rule in the Order source."""
        source = (Path(__file__).resolve().parent.parent / "order.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        method = next(node for cls in tree.body if isinstance(cls, ast.ClassDef)
                      and cls.name == "Order" for node in cls.body
                      if isinstance(node, ast.FunctionDef) and node.name == "calculate_total")
        self.assertFalse(any(isinstance(node, (ast.If, ast.IfExp)) for node in ast.walk(method)))
        self.assertIn("self.discount.apply(total)", source)


if __name__ == "__main__":
    import unittest
    unittest.main()
