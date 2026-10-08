#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Tests for shared_strings_builder.py control-character handling.

XML 1.0 forbids most C0 control characters, but html.escape() passes
them through — a string like "bad\x01char" produced a sharedStrings.xml
that no XML parser (including xlsx_pack's validator) accepts. The
builder must strip characters XML cannot represent.
"""

import os
import sys
import unittest
import xml.etree.ElementTree as ET

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from shared_strings_builder import build_xml, build_index_table, deduplicate  # noqa: E402


class TestControlCharacters(unittest.TestCase):
    def test_c0_controls_are_stripped_and_xml_parses(self):
        xml = build_xml(["bad\x01char", "tab\tok", "line\nok"])
        root = ET.fromstring(xml)
        texts = [t.text for t in root.iter(
            "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")]
        self.assertEqual(texts[0], "badchar")
        self.assertEqual(texts[1], "tab\tok")
        self.assertEqual(texts[2], "line\nok")

    def test_all_controls_string_yields_parseable_xml(self):
        xml = build_xml(["\x00\x01\x02"])
        ET.fromstring(xml)  # must not raise

    def test_allowed_whitespace_preserved_flag_unchanged(self):
        xml = build_xml(["  padded  "])
        root = ET.fromstring(xml)
        t = list(root.iter(
            "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))[0]
        self.assertEqual(t.text, "  padded  ")
        self.assertEqual(t.get("{http://www.w3.org/XML/1998/namespace}space"),
                         "preserve")

    def test_index_table_shows_stripped_text(self):
        table = build_index_table(deduplicate(["bad\x01char"]))
        self.assertIn("badchar", table)


if __name__ == "__main__":
    unittest.main()
