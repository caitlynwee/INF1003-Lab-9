"""CSV import with row-level recovery and try/except/else/finally."""

import csv

from inventory import Inventory
from product_factory import ProductFactory
from supplier import Supplier


def load_products(path: str, inventory: Inventory, supplier: Supplier) -> None:
    """Import valid CSV products and skip bad rows without discarding others."""
    loaded = 0
    try:
        file = open(path, newline="", encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"Products file not found: {path}")
    else:
        with file:
            reader = csv.reader(file)
            next(reader, None)  # Header: product_type, product_id, name, price, stock_quantity
            for row_number, row in enumerate(reader, start=2):
                if not row:  # Blank lines are not product records.
                    continue
                try:
                    if len(row) != 5:
                        raise ValueError("Expected five CSV columns.")
                    product_type, product_id, name, price_text, stock_text = (
                        value.strip() for value in row
                    )
                    product = ProductFactory.create(
                        product_type,
                        product_id,
                        name,
                        float(price_text),
                        int(stock_text),
                        supplier,
                    )
                    inventory.add_product(product)
                except ValueError as error:
                    print(f"Skipping row {row_number}: {error}")
                    continue
                loaded += 1
        print(f"{loaded} products loaded.")
    finally:
        print("Load attempt finished.")
