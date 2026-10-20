import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server  # noqa: E402

TODOS = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Call mom", "done": True},
    {"id": 3, "title": "Buy bread", "done": False},
]


class FilterTodosTests(unittest.TestCase):
    def test_all_returns_everything(self):
        self.assertEqual(len(server.filter_todos(TODOS)), 3)

    def test_active_and_done(self):
        self.assertEqual([t["id"] for t in server.filter_todos(TODOS, status="active")], [1, 3])
        self.assertEqual([t["id"] for t in server.filter_todos(TODOS, status="done")], [2])

    def test_query_is_case_insensitive(self):
        self.assertEqual([t["id"] for t in server.filter_todos(TODOS, query="buy")], [1, 3])


class StatsTests(unittest.TestCase):
    def test_counts(self):
        with mock.patch.object(server.time, "sleep"):
            stats = server.compute_stats(TODOS)
        self.assertEqual((stats["total"], stats["done"], stats["open"]), (3, 1, 2))
        self.assertEqual(stats["by_owner"], {"you": 3})


class CreateTodoTests(unittest.TestCase):
    def test_create_assigns_increasing_ids(self):
        first = server.create_todo("One")
        second = server.create_todo("Two")
        self.assertEqual(second["id"], first["id"] + 1)
        self.assertFalse(first["done"])


if __name__ == "__main__":
    unittest.main()
