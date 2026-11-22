from codec import rle_encode


def test_rle_encode_groups_repeated_characters():
    assert rle_encode("aab") == [("a", 2), ("b", 1)]
