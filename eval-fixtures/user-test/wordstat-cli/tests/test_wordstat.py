import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import wordstat  # noqa: E402


class WordstatTests(unittest.TestCase):
    def test_count_words_single_spaces(self):
        self.assertEqual(wordstat.count_words("hello big world"), 3)

    def test_top_words_orders_by_frequency(self):
        self.assertEqual(wordstat.top_words("b a b c b a", 2), [("b", 3), ("a", 2)])

    def test_top_words_is_case_insensitive(self):
        self.assertEqual(wordstat.top_words("Go go GO", 1), [("go", 3)])


if __name__ == "__main__":
    unittest.main()
