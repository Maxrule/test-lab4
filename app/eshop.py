"""
Модуль для логіки інтернет-магазину.
Містить класи товарів, кошика та замовлення.
"""
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from services import ShippingService


class Product:
    """Клас, що описує товар."""
    def __init__(self, name, price, available_amount):
        self.name = name
        self.price = price
        self.available_amount = available_amount

    def is_available(self, requested_amount):
        """Перевірка наявності товару."""
        return self.available_amount >= requested_amount

    def buy(self, requested_amount):
        """Процес купівлі товару (зменшення залишку)."""
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
    """Клас, що описує кошик покупця."""
    def __init__(self):
        self.products = {}

    def contains_product(self, product):
        """Чи є товар у кошику."""
        return product in self.products

    def calculate_total(self):
        """Розрахунок загальної вартості замовлення."""
        return sum(p.price * count for p, count in self.products.items())

    def add_product(self, product: Product, amount: int):
        """Додавання товару в кошик."""
        if not product.is_available(amount):
            raise ValueError(f"Product {product} has only {product.available_amount} items")
        self.products[product] = amount

    def remove_product(self, product):
        """Видалення товару з кошика."""
        if product in self.products:
            del self.products[product]

    def submit_cart_order(self):
        """Підготовка списку ID товарів та очищення кошика."""
        product_ids = []
        for product, count in self.products.items():
            product.buy(count)
            product_ids.append(str(product))
        self.products.clear()
        return product_ids


@dataclass
class Order:
    """Клас для оформлення замовлення."""
    cart: ShoppingCart
    shipping_service: ShippingService
    order_id: str = None

    def __post_init__(self):
        if self.order_id is None:
            self.order_id = str(uuid.uuid4())

    def place_order(self, shipping_type, due_date: datetime = None):
        """Оформлення доставки замовлення."""
        if not due_date:
            due_date = datetime.now(timezone.utc) + timedelta(seconds=3)
        product_ids = self.cart.submit_cart_order()
        print(due_date)
        return self.shipping_service.create_shipping(
            shipping_type,
            product_ids,
            self.order_id,
            due_date
        )


@dataclass()
class Shipment:
    """Клас для перевірки статусу відправлення."""
    shipping_id: str
    shipping_service: ShippingService

    def check_shipping_status(self):
        """Перевірка поточного статусу."""
        return self.shipping_service.check_status(self.shipping_id)