from csv_loader import load_products
from discount_strategy import BulkDiscount, NoDiscount, PercentageDiscount, StudentDiscount
from file_handling import load_inventory, save_inventory
from input_helpers import get_positive_float
from inventory import Inventory
from order import Order
from product import Product
from product_factory import ProductFactory
from supplier import Supplier


def read_non_negative_float(message: str) -> float:
    while True:
        try:
            value = float(input(message))
            if value >= 0 and value != float("inf") and value == value:
                return value
        except ValueError:
            pass
        print("Please enter a valid non-negative number.")


def read_non_negative_int(message: str) -> int:
    while True:
        try:
            value = int(input(message))
            if value >= 0:
                return value
        except ValueError:
            pass
        print("Please enter a non-negative whole number.")


def read_positive_int(message: str) -> int:
    while True:
        try:
            value = int(input(message))
            if value > 0:
                return value
        except ValueError:
            pass
        print("Please enter a positive whole number.")


def choose_discount():
    """Choose a strategy in the UI; Order itself never branches on type."""
    options = {
        "1": NoDiscount(),
        "2": PercentageDiscount(10),
        "3": BulkDiscount(200, 20),
        "4": StudentDiscount(),
    }
    print("Discount: 1=None  2=10%  3=$20 off orders >= $200  4=Student 5%")
    while True:
        choice = input("Choose discount (1-4): ").strip()
        if choice in options:
            return options[choice]
        print("Please select a discount from 1 to 4.")


def read_product_type() -> str:
    while True:
        product_type = input("Enter product type (physical/digital): ").strip().lower()
        if product_type in ("physical", "digital"):
            return product_type
        print("Please enter physical or digital.")


def read_supplier(inventory: Inventory) -> Supplier:
    supplier_id = input("Enter supplier ID: ").strip()
    for product in inventory.products:
        if product.supplier.supplier_id.lower() == supplier_id.lower():
            print("Using existing supplier:")
            product.supplier.display_information()
            return product.supplier
    supplier_name = input("Enter supplier name: ").strip()
    supplier_email = input("Enter supplier contact email: ").strip()
    return Supplier(supplier_id, supplier_name, supplier_email)


def show_product_details(product: Product) -> None:
    product.display_information()
    print(f"           Fulfilment: {product.get_fulfilment_info()}")


def demonstrate_polymorphism(inventory: Inventory) -> None:
    if not inventory.products:
        print("No products to demonstrate polymorphism.")
        return
    print("\n--- Lab 8: One Product collection, multiple subclasses ---")
    for product in inventory.products:
        show_product_details(product)
        print()


def create_order(inventory: Inventory, orders: list[Order]) -> None:
    order_id = input("Enter new order ID: ").strip()
    if any(order.order_id.lower() == order_id.lower() for order in orders):
        print("Order ID already exists.")
        return
    try:
        order = Order(order_id)
    except ValueError as error:
        print(f"Could not create order: {error}")
        return
    while True:
        product_id = input("Enter product ID (blank to finish order): ").strip()
        if not product_id:
            break
        product = inventory.find_product(product_id)
        if product is None:
            print("Product not found.")
            continue
        quantity = read_positive_int("Enter quantity: ")
        try:
            order.add_order_line(product, quantity)
            print("Order line added.")
        except (ValueError, TypeError) as error:
            print(f"Could not add order line: {error}")
    if order.order_lines:
        order.set_discount(choose_discount())
        orders.append(order)
        order.display_information()
    else:
        print("Empty order discarded.")


def main() -> None:
    try:
        inventory = load_inventory()
        print("Inventory loaded successfully.")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Unable to load inventory: {error}")
        print("Starting with an empty inventory. Existing file will not be changed unless you save.")
        inventory = Inventory()
    orders: list[Order] = []  # examples are kept in memory, not saved to JSON

    while True:
        print("\n===== INVENTORY MANAGEMENT SYSTEM =====")
        print("1. Display all products")
        print("2. Add a product")
        print("3. Update stock")
        print("4. Search for a product")
        print("5. Save inventory")
        print("6. Remove a product (aggregation)")
        print("7. Create an order (composition)")
        print("8. Demonstrate polymorphism and LSP")
        print("9. Load products from CSV (Lab 9)")
        print("10. Exit")
        choice = input("Enter your choice (1-10): ").strip()

        if choice == "1":
            inventory.display_all()

        elif choice == "2":
            product_id = input("Enter product ID: ").strip()
            name = input("Enter product name: ").strip()
            price = get_positive_float("Enter price: $")
            stock = read_non_negative_int("Enter stock quantity: ")
            product_type = read_product_type()
            extra_message = "Enter weight (kg): " if product_type == "physical" else "Enter download size (MB): "
            extra_value = read_non_negative_float(extra_message)
            try:
                supplier = read_supplier(inventory)
                product = ProductFactory.create(
                    product_type, product_id, name, price, stock, supplier,
                    weight=extra_value if product_type == "physical" else 0.0,
                    download_size=extra_value if product_type == "digital" else 0.0,
                )
                inventory.add_product(product)
                print("Product added successfully!")
            except (ValueError, TypeError) as error:
                print(f"Could not add product: {error}")

        elif choice == "3":
            product_id = input("Enter product ID to update: ").strip()
            product = inventory.search_product(product_id)
            if product is None:
                print("Product not found.")
            else:
                quantity = read_non_negative_int("Enter new total stock quantity: ")
                product.update_stock(quantity)
                print("Stock updated successfully!")

        elif choice == "4":
            product_id = input("Enter product ID to search: ").strip()
            product = inventory.search_product(product_id)
            if product is None:
                print("Product not found.")
            else:
                print(f"{'ID':<10} {'Name':<20} {'Price':>11} {'Stock':>8}")
                print("-" * 53)
                show_product_details(product)
                print("           Supplier contact:")
                product.supplier.display_information()

        elif choice == "5":
            try:
                save_inventory(inventory)
                print("Inventory saved successfully!")
            except OSError as error:
                print(f"Could not save inventory: {error}")

        elif choice == "6":
            product_id = input("Enter product ID to remove: ").strip()
            if inventory.remove_product(product_id):
                print("Product reference removed from this inventory.")
            else:
                print("Product not found.")

        elif choice == "7":
            create_order(inventory, orders)

        elif choice == "8":
            demonstrate_polymorphism(inventory)

        elif choice == "9":
            path = input("CSV file path (default: products.csv): ").strip() or "products.csv"
            try:
                supplier = read_supplier(inventory)
                load_products(path, inventory, supplier)
            except (ValueError, TypeError) as error:
                print(f"Could not load products: {error}")

        elif choice == "10":
            print("Goodbye! Save first using option 5 if you want to keep changes.")
            break

        else:
            print("Invalid option. Please enter a number from 1 to 10.")


if __name__ == "__main__":
    main()
