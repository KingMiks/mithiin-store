import pytest

def add(a, b):
    return a + b

def test_add_two_numbers():
    assert add(2, 3) == 5

@pytest.fixture          # setup helper: NOT a test
def basket():
    return ["apple", "pear"]

def test_basket_has_two_items():
    basket = ["apple", "pear"]      # setup repeated here
    assert len(basket) == 2

def test_basket_contains_apple():
    basket = ["apple", "pear"]      # and again here
    assert "apple" in basket