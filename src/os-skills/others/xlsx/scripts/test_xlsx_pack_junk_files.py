#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Tests for xlsx_pack.py OS junk-file exclusion.

On macOS, Finder drops .DS_Store (and ._* AppleDouble files) into any
directory it opens; Windows adds Thumbs.db. xlsx_pack zipped them into
the archive as undeclared package parts, which Excel flags for repair
exactly like any other unknown part.
"""

import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(SCRIPTS_DIR, "xlsx_pack.py")

CT = (
    '<?xml version="1.0"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>'
)


class TestJunkFileExclusion(unittest.TestCase):
    def _pack(self, tmpdir: str, extra_names: list[str]) -> list[str]:
        with open(os.path.join(tmpdir, "[Content_Types].xml"), "w") as f:
            f.write(CT)
        for name in extra_names:
            path = os.path.join(tmpdir, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            body = "<workbook/>" if name.endswith(".xml") else "junk"
            with open(path, "w") as f:
                f.write(body)
        out = os.path.join(tmpdir, "..", "out.xlsx")
        r = subprocess.run([sys.executable, PACK, tmpdir, out],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        with zipfile.ZipFile(out) as z:
            return z.namelist()

    def test_ds_store_not_packed(self):
        with tempfile.TemporaryDirectory() as tmp:
            names = self._pack(tmp, [".DS_Store"])
            self.assertNotIn(".DS_Store", names)

    def test_appledouble_and_thumbs_not_packed(self):
        with tempfile.TemporaryDirectory() as tmp:
            names = self._pack(tmp, ["._sheet1.xml", "Thumbs.db"])
            self.assertNotIn("._sheet1.xml", names)
            self.assertNotIn("Thumbs.db", names)

    def test_macosx_directory_not_packed(self):
        with tempfile.TemporaryDirectory() as tmp:
            names = self._pack(tmp, [os.path.join("__MACOSX", "x")])
            self.assertFalse(any(n.startswith("__MACOSX") for n in names))

    def test_real_parts_still_packed(self):
        with tempfile.TemporaryDirectory() as tmp:
            names = self._pack(tmp, [os.path.join("xl", "workbook.xml")])
            self.assertIn("[Content_Types].xml", names)
            self.assertIn("xl/workbook.xml", names)


if __name__ == "__main__":
    unittest.main()
