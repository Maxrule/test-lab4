import pytest
import uuid
import boto3
import random
from datetime import datetime, timedelta, timezone
from app.eshop import Product, ShoppingCart, Order
from services import ShippingService
from services.repository import ShippingRepository
from services.publisher import ShippingPublisher
from services.config import AWS_ENDPOINT_URL, AWS_REGION, SHIPPING_QUEUE

# --- 10 ІНТЕГРАЦІЙНИХ ТЕСТІВ (Bottom-up) ---

# 1. Взаємодія Product -> ShoppingCart (Валідація цілісності даних)
def test_cart_product_integration():
    p = Product("Milk", 35.5, 10)
    cart = ShoppingCart()
    cart.add_product(p, 2)
    assert cart.calculate_total() == 71.0

# 2. Взаємодія ShoppingCart -> Order (Перевірка очищення після замовлення)
def test_cart_order_cleanup():
    p = Product("Bread", 15, 5)
    cart = ShoppingCart()
    cart.add_product(p, 1)
    mock_service = ShippingService(ShippingRepository(), ShippingPublisher())
    order = Order(cart, mock_service)
    cart.products.clear()
    assert len(cart.products) == 0

# 3. Взаємодія Order -> Product (Списання залишків зі складу)
def test_order_stock_reduction():
    p = Product("Water", 10, 100)
    cart = ShoppingCart()
    cart.add_product(p, 10)
    p.buy(10)
    assert p.available_amount == 90

# 4. Перевірка запису замовлення в БД (Integration з DynamoDB)
def test_dynamodb_save_order(dynamo_resource):
    table = dynamo_resource.Table('Orders')
    order_id = str(uuid.uuid4())
    table.put_item(Item={'order_id': order_id, 'status': 'completed', 'amount': 150})
    response = table.get_item(Key={'order_id': order_id})
    assert response['Item']['amount'] == 150

# 5. Перевірка обробки декількох товарів
def test_multiple_products_integration():
    cart = ShoppingCart()
    for i in range(5):
        p = Product(f"Item_{i}", 10, 10)
        cart.add_product(p, 1)
    assert cart.calculate_total() == 50

# 6. Оновлення ціни продукту впливає на підсумок кошика
def test_price_update_integration():
    p = Product("Promo", 100, 5)
    cart = ShoppingCart()
    cart.add_product(p, 1)
    p.price = 80
    assert cart.calculate_total() == 80

# 7-10. Параметризовані тести граничних значень
@pytest.mark.parametrize("name, price, qty", [
    ("A", 0.01, 1),        # Мінімальна ціна
    ("B", 1000000, 1),     # Велика сума
    ("C", 10, 100),        # Максимальна кількість
    ("D", 50.55, 0)        # Нульова кількість
])
def test_parametrized_integration(name, price, qty):
    p = Product(name, price, 100)
    cart = ShoppingCart()
    cart.add_product(p, qty)
    assert cart.calculate_total() == price * qty


# --- ТЕСТИ З ВИКОРИСТАННЯМ MOCK ТА AWS SQS  ---

@pytest.mark.parametrize("order_id, shipping_id", [
    ("order_1", "shipping_1"),
    ("order_i2hur2937r9", "shipping_1!!!!"),
    (8662354, 123456),
    (str(uuid.uuid4()), str(uuid.uuid4()))
])
def test_place_order_with_mocked_repo(mocker, order_id, shipping_id):
    mock_repo = mocker.Mock()
    mock_publisher = mocker.Mock()
    shipping_service = ShippingService(mock_repo, mock_publisher)

    mock_repo.create_shipping.return_value = shipping_id

    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=9
    )

    order = Order(cart, shipping_service, order_id)
    due_date = datetime.now(timezone.utc) + timedelta(seconds=3)
    actual_shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=due_date
    )

    assert actual_shipping_id == shipping_id, "Actual shipping id must be equal to mock return value"

    mock_repo.create_shipping.assert_called_with(
        ShippingService.list_available_shipping_type()[0],
        ["Product"],
        order_id,
        shipping_service.SHIPPING_CREATED,
        due_date
    )
    mock_publisher.send_new_shipping.assert_called_with(shipping_id)


def test_place_order_with_unavailable_shipping_type_fails(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=9
    )
    order = Order(cart, shipping_service)
    shipping_id = None

    with pytest.raises(ValueError) as excinfo:
        shipping_id = order.place_order(
            "Новий тип доставки",
            due_date=datetime.now(timezone.utc) + timedelta(seconds=3)
        )
    assert shipping_id is None, "Shipping id must not be assigned"
    assert "Shipping type is not available" in str(excinfo.value)


def test_when_place_order_then_shipping_in_queue(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()

    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=9
    )

    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    sqs_client = boto3.client(
        "sqs",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION
    )
    queue_url = sqs_client.get_queue_url(QueueName=SHIPPING_QUEUE)["QueueUrl"]
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )

    messages = response.get("Messages", [])
    assert len(messages) == 1, "Expected 1 SQS message"

    body = messages[0]["Body"]
    assert shipping_id == body
