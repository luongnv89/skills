from inventory import needs_reorder, parse_sku


def test_needs_reorder_counts_negative_stock_as_zero():
    assert needs_reorder({"qty": -3}) is True


def test_parse_sku_upper_cases_and_trims():
    assert parse_sku(" ab-12 ") == "AB-12"
