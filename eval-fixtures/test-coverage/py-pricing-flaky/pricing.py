"""Price calculation for orders."""


class InvalidQuantity(ValueError):
    """Raised when an order quantity is below 1."""


def unit_price(base: float, quantity: int) -> float:
    """Return the unit price after volume discounts.

    10 or more items get 10% off, 100 or more get 20% off.
    Raises InvalidQuantity when quantity is below 1.
    """
    if quantity < 1:
        raise InvalidQuantity(quantity)
    if quantity >= 100:
        return round(base * 0.8, 2)
    if quantity >= 10:
        return round(base * 0.9, 2)
    return base


def total(base: float, quantity: int, coupon: str | None = None) -> float:
    """Return the order total. The coupon "HALF" halves it."""
    amount = unit_price(base, quantity) * quantity
    if coupon == "HALF":
        amount /= 2
    return round(amount, 2)
