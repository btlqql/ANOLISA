#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Tests for xlsx_add_column.py sheetData row ordering.

Rows missing from sheetData (gaps in the stored sheet) were appended at
the END of sheetData, after any higher existing row. The OOXML spec
requires <row> elements in ascending order, so a sheet holding rows
1, 2, 10 that gains formula rows 3-9 ended up ordered
1, 2, 10, 3, 4, ... — an xlsx Excel repairs (or drops) on open.
"""

import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ADD_COLUMN = os.path.join(SCRIPTS_DIR, "xlsx_add_column.py")

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _build_work_dir(tmpdir: str, last_rows: str) -> str:
    work = os.path.join(tmpdir, "work")
    os.makedirs(os.path.join(work, "xl", "worksheets"))
    os.makedirs(os.path.join(work, "xl", "_rels"))
    with open(os.path.join(work, "xl", "worksheets", "sheet1.xml"), "w") as f:
        f.write(
            '<?xml version="1.0"?>'
            f'<worksheet xmlns="{NS}"><dimension ref="A1:F10"/>'
            f"<sheetData>{last_rows}</sheetData></worksheet>"
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
        f.write(
            '<?xml version="1.0"?>'
            f'<sst xmlns="{NS}" count="1" uniqueCount="1"><si><t>H</t></si></sst>'
        )
    with open(os.path.join(work, "xl", "styles.xml"), "w") as f:
        f.write(
            '<?xml version="1.0"?>'
            f'<styleSheet xmlns="{NS}"><fonts count="1"><font/></fonts>'
            '<fills count="2"><fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill></fills>'
            '<borders count="1"><border/></borders>'
            '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
            '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellXfs>'
            "</styleSheet>"
        )
    with open(os.path.join(work, "[Content_Types].xml"), "w") as f:
        f.write(
            '<?xml version="1.0"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            "</Types>"
        )
    return work


def _row_numbers(work: str) -> list[int]:
    root = ET.parse(os.path.join(work, "xl", "worksheets", "sheet1.xml")).getroot()
    return [int(r.get("r")) for r in root.find(f"{{{NS}}}sheetData")]


GAPPED_ROWS = (
    '<row r="1"><c r="A1" t="s"><v>0</v></c></row>'
    '<row r="2"><c r="A2"><v>1</v></c></row>'
    '<row r="10"><c r="A10"><v>9</v></c></row>'
)


class TestSheetDataRowOrder(unittest.TestCase):
    def test_formula_rows_fill_gaps_in_order(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            work = _build_work_dir(tmpdir, GAPPED_ROWS)
            r = subprocess.run(
                [sys.executable, ADD_COLUMN, work, "--col", "B", "--header", "New",
                 "--formula", "A{row}*2", "--formula-rows", "3:9"],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(_row_numbers(work), list(range(1, 11)))

    def test_total_row_inserts_in_order(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rows = (
                '<row r="1"><c r="A1" t="s"><v>0</v></c></row>'
                '<row r="12"><c r="A12"><v>11</v></c></row>'
            )
            work = _build_work_dir(tmpdir, rows)
            r = subprocess.run(
                [sys.executable, ADD_COLUMN, work, "--col", "B", "--header", "New",
                 "--total-row", "5", "--total-formula", "=SUM(B2:B4)"],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(_row_numbers(work), [1, 5, 12])


if __name__ == "__main__":
    unittest.main()
