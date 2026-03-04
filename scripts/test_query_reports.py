#!/usr/bin/env python3
import unittest
import scripts.query_reports as qr


class TestQueryReportsTagFilter(unittest.TestCase):
    def test_filter_rows_by_single_tag(self):
        rows = [
            {"id": 1, "tags": ["lulu", "beauty"]},
            {"id": 2, "tags": ["beauty"]},
            {"id": 3, "tags": "lulu"},
        ]
        out = qr.filter_rows_by_tags(rows, ["lulu"])
        self.assertEqual([r["id"] for r in out], [1, 3])

    def test_filter_rows_by_multiple_tags_or_logic(self):
        rows = [
            {"id": 1, "tags": ["lulu"]},
            {"id": 2, "tags": ["sport"]},
            {"id": 3, "tags": ["other"]},
        ]
        out = qr.filter_rows_by_tags(rows, ["lulu", "sport"])
        self.assertEqual([r["id"] for r in out], [1, 2])


if __name__ == "__main__":
    unittest.main()
