#!/usr/bin/env python3
"""Regression tests for xlsx_reader.py --sheet on CSV/TSV files.

CSV files load as a single sheet keyed by the file stem. --sheet was
silently ignored for them, so `xlsx_reader.py data.csv --sheet Sales`
analyzed (and reported) data the caller never asked for. A mismatched
sheet name must fail loudly like it does for workbooks.
"""

import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "src", "os-skills", "others", "xlsx", "scripts",
    "xlsx_reader.py",
)


class TestCsvSheetFilter(unittest.TestCase):
    def _run(self, *args):
        return subprocess.run([sys.executable, SCRIPT, *args],
                              capture_output=True, text=True)

    def test_wrong_sheet_name_fails_loudly(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv = os.path.join(tmp, "sales.csv")
            with open(csv, "w") as f:
                f.write("a,b\n1,2\n")
            r = self._run(csv, "--sheet", "Budget")
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("ERROR", r.stderr)
            self.assertIn("Budget", r.stderr)

    def test_matching_sheet_name_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv = os.path.join(tmp, "sales.csv")
            with open(csv, "w") as f:
                f.write("a,b\n1,2\n")
            r = self._run(csv, "--sheet", "sales")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("ANALYSIS REPORT", r.stdout)

    def test_no_sheet_flag_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv = os.path.join(tmp, "sales.csv")
            with open(csv, "w") as f:
                f.write("a,b\n1,2\n")
            r = self._run(csv)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("ANALYSIS REPORT", r.stdout)


if __name__ == "__main__":
    unittest.main()
