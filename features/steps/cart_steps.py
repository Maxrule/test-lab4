from behave import given, when, then
from eshop import Product, ShoppingCart
@given("The product has availability of {availability}")
def create_product_for_cart(context, availability):
    context.product = Product(name="any", price=123, available_amount=int(availability))
@given('An empty shopping cart')
def empty_cart(context):
    context.cart = ShoppingCart()
@when("I add product to the cart in amount {product_amount}")
def add_product(context, product_amount):
    try:
        context.cart.add_product(context.product, int(product_amount))
        context.add_successfully = True
    except ValueError:
        context.add_successfully = False
@then("Product is added to the cart successfully")
def add_successful(context):
    assert context.add_successfully == True
@then("Product is not added to cart successfully")
def add_failed(context):
    assert context.add_successfully == False
