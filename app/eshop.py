"""
Module for E-shop logic including Product, ShoppingCart, and Order.
"""
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from services import ShippingService


class Product:
    """Represents a product in the store."""

    def __init__(self, name, price, available_amount):
        self.name = name
        self.price = price
        self.available_amount = available_amount

    def is_available(self, requested_amount):
        """Checks if requested amount is available."""
        return self.available_amount >= requested_amount

    def buy(self, requested_amount):
        """Reduces the stock of the product."""
        self.available_amount -= requested_amount

    def __eq__(self, other):
        if not isinstance(other, Product):
            return False
        return self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name


class ShoppingCart:
    """Represents a customer's shopping cart."""

    def __init__(self):
        self.products = {}

    def contains_product(self, product):
        """Checks if product is in cart."""
        return product in self.products

    def calculate_total(self):
        """Calculates total price."""
        return sum(p.price * count for p, count in self.products.items())

    def add_product(self, product: Product, amount: int):
        """Adds product to cart."""
        if not product.is_available(amount):
            raise ValueError(f"Not enough items of {product}")
        self.products[product] = amount

    def remove_product(self, product):
        """Removes product from cart."""
        if product in self.products:
            del self.products[product]

    def submit_cart_order(self):
        """Clears cart and returns product names."""
        product_ids = []
        for product, count in self.products.items():
            product.buy(count)
            product_ids.append(str(product))
        self.products.clear()
        return product_ids


@dataclass
class Order:
    """Represents a customer order with shipping."""
    cart: ShoppingCart
    shipping_service: ShippingService
    order_id: str = None

    def __post_init__(self):
        if self.order_id is None:
            self.order_id = str(uuid.uuid4())

    def place_order(self, shipping_type, due_date: datetime = None):
        """Creates a shipping request."""
        if not due_date:
            due_date = datetime.now(timezone.utc) + timedelta(seconds=3)
        product_ids = self.cart.submit_cart_order()
        return self.shipping_service.create_shipping(
            shipping_type, product_ids, self.order_id, due_date
        )


@dataclass
class Shipment:
    """Represents a shipment status checker."""
    shipping_id: str
    shipping_service: ShippingService

    def check_shipping_status(self):
        """Returns the status from the service."""
        return self.shipping_service.check_status(self.shipping_id)