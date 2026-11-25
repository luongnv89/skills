import pytest

from inventory.stock import Item, restock, total_units


def test_restock_adds_units():
    assert restock(Item("A1", 2), 3) == Item("A1", 5)


def test_restock_rejects_zero():
    with pytest.raises(ValueError):
        restock(Item("A1", 2), 0)


def test_total_units():
    assert total_units([Item("A1", 2), Item("B2", 4)]) == 6
