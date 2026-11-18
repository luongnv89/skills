from slugkit import slugify


def test_basic_title():
    assert slugify("Hello, World!") == "hello-world"


def test_accents_are_folded():
    assert slugify("Crème brûlée recipes") == "creme-brulee-recipes"


def test_custom_separator():
    assert slugify("Hello World", separator="_") == "hello_world"


def test_max_length_drops_trailing_separator():
    assert slugify("A very long title indeed", max_length=10) == "a-very-lon"
