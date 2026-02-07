from behave import given, when, then
from app.eshop import Product

# Використовуємо {availability}, щоб приймати будь-яке число з лапок або без
@given('The product with name "{name}" has availability of {availability}')
def step_create_product(context, name, availability):
    context.product = Product(name=name, price=100, available_amount=int(availability))

@when('I check if product is available in amount {amount}')
def step_check_availability(context, amount):
    context.check_result = context.product.is_available(int(amount))

@then("Product is available")
def step_product_available(context):
    assert context.check_result is True

@then("Product is not available")
def step_product_not_available(context):
    assert context.check_result is False