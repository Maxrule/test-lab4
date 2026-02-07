"""
Модуль для логіки інтернет-магазину: товари, кошик та замовлення.
"""
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from services import ShippingService


class Product:
    """Клас, що представляє товар у магазині."""

    def __init__(self, name, price, available_amount):
        self.name = name
        self.price = price
        self.available_amount = available_amount

    def is_available(self, requested_amount):
        """Перевіряє, чи достатньо товару на складі."""
        return self.available_amount >= requested_amount

    def buy(self, requested_amount):
        """Зменшує кількість товару на складі."""
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
    """Клас кошика для покупок."""

    def __init__(self):
        self.products = {}

    def contains_product(self, product):
        """Перевіряє наявність товару в кошику."""
        return product in self.products

    def calculate_total(self):
        """Рахує загальну вартість товарів."""
        return sum(p.price * count for p, count in self.products.items())

    def add_product(self, product: Product, amount: int):
        """Додає товар до кошика з перевіркою залишків."""
        if not product.is_available(amount):
            raise ValueError(f"Product {product} has only {product.available_amount} items")
        self.products[product] = amount

    def remove_product(self, product):
        """Видаляє товар з кошика."""
        if product in self.products:
            del self.products[product]

    def submit_cart_order(self):
        """Оформлює товари з кошика та очищує його."""
        product_ids = []
        for product, count in self.products.items():
            product.buy(count)
            product_ids.append(str(product))
        self.products.clear()
        return product_ids


@dataclass
class Order:
    """Клас, що представляє замовлення клієнта."""
    cart: ShoppingCart
    shipping_service: ShippingService
    order_id: str = None

    def __post_init__(self):
        if self.order_id is None:
            self.order_id = str(uuid.uuid4())

    def place_order(self, shipping_type, due_date: datetime = None):
        """Створює відправку на основі замовлення."""
        if not due_date:
            due_date = datetime.now(timezone.utc) + timedelta(seconds=3)
        product_ids = self.cart.submit_cart_order()
        print(due_date)
        return self.shipping_service.create_shipping(
            shipping_type, product_ids, self.order_id, due_date
        )


@dataclass
class Shipment:
    """Клас для відстеження статусу доставки."""
    shipping_id: str
    shipping_service: ShippingService

    def check_shipping_status(self):
        """Отримує поточний статус доставки."""
        return self.shipping_service.check_status(self.shipping_id)