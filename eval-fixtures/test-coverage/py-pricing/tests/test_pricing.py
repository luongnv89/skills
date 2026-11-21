from pricing import unit_price


def test_unit_price_small_order():
    assert unit_price(10.0, 1) == 10.0


def test_unit_price_keeps_base_below_ten():
    assert unit_price(4.5, 3) == 4.5