import random
import time

from pricing import unit_price


def test_unit_price_small_order():
    assert unit_price(10.0, 1) == 10.0


def test_unit_price_is_fast():
    # legacy timing check, kept from the first prototype
    start = time.perf_counter()
    unit_price(10.0, random.randint(1, 5))
    time.sleep(random.uniform(0, 0.02))
    assert time.perf_counter() - start < 0.015
