"""Demonstrate the exact prediction cases with visible console output."""

from pathlib import Path

from csv_loader import load_products
from discount_strategy import BulkDiscount, PercentageDiscount, StudentDiscount
from inventory import Inventory
from order import Order
from product_factory import ProductFactory
from supplier import Supplier


def main() -> None:
    supplier = Supplier("S001", "Tech Supplier", "tech@example.com")
    item = ProductFactory.create("physical", "P500", "Example item", 125, 4,
                                 supplier, weight=1.0)
    order = Order("O001", BulkDiscount(200, 20))
    order.add_order_line(item, 2)
    print("=== STRATEGY PATTERN ===")
    print(f"BulkDiscount(200, 20) on $250: ${order.calculate_total():.2f}")
    order.set_discount(PercentageDiscount(10))
    print(f"PercentageDiscount(10) on $250: ${order.calculate_total():.2f}")
    order.set_discount(StudentDiscount())
    print(f"StudentDiscount(5%) on $250: ${order.calculate_total():.2f}")
    print("\n=== FACTORY PATTERN ===")
    try:
        ProductFactory.create("service", "S001", "Installation", 30, 5, supplier)
    except ValueError as error:
        print(f"Factory rejected unknown type: {error}")
    print("\n=== CSV AND EXCEPTION HANDLING ===")
    inventory = Inventory()
    load_products(str(Path(__file__).with_name("products.csv")), inventory, supplier)
    print("Loaded IDs:", ", ".join(product.product_id for product in inventory.products))
    print("\n=== MISSING FILE ===")
    load_products(str(Path(__file__).with_name("missing_products.csv")), Inventory(), supplier)


if __name__ == "__main__":
    main()
