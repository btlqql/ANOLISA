#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Tests for formula_check.py --sheet with an unknown sheet name.

A typo'd --sheet value matched no worksheet, zero sheets were checked,
and the run reported PASS (exit 0) — a false green light for a file the
caller meant to audit. The failure must be reported as an error.
"""

import os
import sys
import tempfile
import unittest
import zipfile

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from formula_check import check  # noqa: E402

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _build_xlsx(tmpdir: str) -> str:
    path = os.path.join(tmpdir, "book.xlsx")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "xl/workbook.xml",
            f'<?xml version="1.0"?><workbook xmlns="{NS}" xmlns:r="{NS_REL}">'
            '<sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets></workbook>',
        )
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet1.xml"/></Relationships>',
        )
        z.writestr(
            "xl/worksheets/sheet1.xml",
            f'<?xml version="1.0"?><worksheet xmlns="{NS}">'
            '<sheetData><row r="1"><c r="A1"><f>B9</f></c></row></sheetData></worksheet>',
        )
    return path


class TestUnknownSheetFilter(unittest.TestCase):
    def test_unknown_sheet_filter_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results = check(_build_xlsx(tmpdir), sheet_filter="NotThere")
            self.assertEqual(results["error_count"], 1)
            self.assertEqual(results["errors"][0]["type"], "unknown_sheet_filter")
            self.assertIn("NotThere", results["errors"][0]["message"])

    def test_known_sheet_filter_still_checks_the_sheet(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results = check(_build_xlsx(tmpdir), sheet_filter="Data")
            self.assertEqual(results["sheets_checked"], ["Data"])
            self.assertEqual(results["error_count"], 0)
            self.assertEqual(results["formula_count"], 1)

    def test_no_filter_checks_all_sheets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results = check(_build_xlsx(tmpdir))
            self.assertEqual(results["sheets_checked"], ["Data"])


if __name__ == "__main__":
    unittest.main()
