#!/usr/bin/env python3
"""Regression tests for xlsx_reader.py year-column detection.

A float column named 'year' that is entirely NaN was flagged as
year_as_float: the between(1900, 2200).all() check passed vacuously on
the empty series. Empty columns carry no year evidence and must not be
flagged (the suggested astype(int) fix would even crash on all-NaN).
"""

import importlib.util
import os
import unittest

import pandas as pd

SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "src", "os-skills", "others", "xlsx", "scripts",
    "xlsx_reader.py",
)


def _load_module():
    spec = importlib.util.spec_from_file_location("xlsx_reader_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestYearColumnDetection(unittest.TestCase):
    def setUp(self):
        self.mod = _load_module()

    def _types(self, df):
        findings = self.mod.audit_quality({"S": df})["S"]
        return [f["type"] for f in findings]

    def test_all_nan_year_column_is_not_flagged(self):
        df = pd.DataFrame({"year": [float("nan")] * 3, "name": ["a", "b", "c"]})
        self.assertNotIn("year_as_float", self._types(df))

    def test_real_float_year_column_still_flagged(self):
        df = pd.DataFrame({"year": [2024.0, 2023.0]})
        self.assertIn("year_as_float", self._types(df))

    def test_non_year_floats_not_flagged(self):
        df = pd.DataFrame({"year": [1.5, 2.5]})
        self.assertNotIn("year_as_float", self._types(df))


if __name__ == "__main__":
    unittest.main()
