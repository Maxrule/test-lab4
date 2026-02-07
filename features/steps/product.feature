Feature: Product
  We want to test that product availability functionality works correctly

  Scenario: Product is available
    Given The product with name "Product1" has availability of 123
    When I check if product is available in amount 123
    Then Product is available

  Scenario: Product is not available
    Given The product with name "Product1" has availability of 123
    When I check if product is available in amount 124
    Then Product is not available