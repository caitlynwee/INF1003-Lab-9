"""One location for creating concrete products (simple Factory pattern)."""

from digital_product import DigitalProduct
from physical_product import PhysicalProduct
from product import Product
from supplier import Supplier


class ProductFactory:
    @staticmethod
    def create(
        product_type: str,
        product_id: str,
        name: str,
        price: float,
        stock_quantity: int,
        supplier: Supplier,
        *,
        weight: float = 0.0,
        download_size: float = 0.0,
    ) -> Product:
        """Create a product. CSV rows use 0 for an unspecified extra attribute.

        The optional keyword-only fields preserve the Lab 8 constructors' specific
        weight (physical) and download size (digital) attributes.
        """
        if product_type == "physical":
            return PhysicalProduct(product_id, name, price, stock_quantity, weight, supplier)
        elif product_type == "digital":
            return DigitalProduct(product_id, name, price, stock_quantity, download_size, supplier)
        else:
            raise ValueError(f"Unknown product type: {product_type}")
