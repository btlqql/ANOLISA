#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Tests for xlsx_insert_row.py with no cell payloads.

Inserting a blank row (--at only, no --text/--values/--formula) is a
legitimate operation, but the dimension update ran
max(col_number(c) for c in all_cols) over an empty sequence and died
with "ValueError: max() arg is an empty sequence".
"""

import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
INSERT_ROW = os.path.join(SCRIPTS_DIR, "xlsx_insert_row.py")

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _build_work_dir(tmpdir: str) -> str:
    work = os.path.join(tmpdir, "work")
    os.makedirs(os.path.join(work, "xl", "worksheets"))
    os.makedirs(os.path.join(work, "xl", "_rels"))
    with open(os.path.join(work, "xl", "worksheets", "sheet1.xml"), "w") as f:
        f.write(
            '<?xml version="1.0"?>'
            f'<worksheet xmlns="{NS}"><dimension ref="A1:A3"/>'
            '<sheetData><row r="1"><c r="A1"><v>1</v></c></row>'
            '<row r="2"><c r="A2"><v>2</v></c></row></sheetData></worksheet>'
        )
    with open(os.path.join(work, "xl", "workbook.xml"), "w") as f:
        f.write(
            '<?xml version="1.0"?>'
            f'<workbook xmlns="{NS}" xmlns:r="{REL_NS}">'
            '<sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets></workbook>'
        )
    with open(os.path.join(work, "xl", "_rels", "workbook.xml.rels"), "w") as f:
        f.write(
            '<?xml version="1.0"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="xl/worksheets/sheet1.xml"/></Relationships>'
        )
    with open(os.path.join(work, "xl", "sharedStrings.xml"), "w") as f:
        f.write(f'<?xml version="1.0"?><sst xmlns="{NS}" count="0" uniqueCount="0"></sst>')
    with open(os.path.join(work, "xl", "styles.xml"), "w") as f:
        f.write(
            f'<?xml version="1.0"?><styleSheet xmlns="{NS}">'
            '<fonts count="1"><font/></fonts>'
            '<fills count="2"><fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill></fills>'
            '<borders count="1"><border/></borders>'
            '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
            '<cellXfs count="1"><xf/></cellXfs></styleSheet>'
        )
    with open(os.path.join(work, "[Content_Types].xml"), "w") as f:
        f.write(
            '<?xml version="1.0"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            "</Types>"
        )
    return work


def _row_numbers(work: str) -> list[str]:
    root = ET.parse(os.path.join(work, "xl", "worksheets", "sheet1.xml")).getroot()
    return [r.get("r") for r in root.find(f"{{{NS}}}sheetData")]


class TestBlankRowInsert(unittest.TestCase):
    def test_insert_blank_row_succeeds(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            work = _build_work_dir(tmpdir)
            r = subprocess.run(
                [sys.executable, INSERT_ROW, work, "--at", "2"],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            # Rows 2..3 shifted down and a blank row 2 exists.
            self.assertEqual(_row_numbers(work), ["1", "2", "3"])

    def test_dimension_grows_for_blank_row(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            work = _build_work_dir(tmpdir)
            subprocess.run(
                [sys.executable, INSERT_ROW, work, "--at", "2"],
                capture_output=True, text=True,
            )
            root = ET.parse(os.path.join(work, "xl", "worksheets", "sheet1.xml")).getroot()
            dim = root.find(f"{{{NS}}}dimension")
            self.assertEqual(dim.get("ref"), "A1:A4")


if __name__ == "__main__":
    unittest.main()
