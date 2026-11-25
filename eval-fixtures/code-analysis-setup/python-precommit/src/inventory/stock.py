from dataclasses import dataclass


@dataclass
class Item:
    sku: str
    quantity: int


def restock(item: Item, amount: int) -> Item:
    if amount <= 0:
        raise ValueError("amount must be positive")
    return Item(item.sku, item.quantity + amount)


def total_units(items: list[Item]) -> int:
    return sum(item.quantity for item in items)
