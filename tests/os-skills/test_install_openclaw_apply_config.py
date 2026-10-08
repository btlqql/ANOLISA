#!/usr/bin/env python3
"""Regression tests for install_openclaw.py apply_config().

A pre-existing ~/.openclaw/openclaw.json that is not a JSON object (a
list, a bare string, or null) crashed the installer inside deep_merge
with a raw TypeError/ValueError traceback. apply_config must fail with
a clean, actionable SystemExit instead.
"""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "src", "os-skills", "ai", "install-openclaw", "scripts",
    "install_openclaw.py",
)


def _load_module():
    spec = importlib.util.spec_from_file_location("install_openclaw_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestApplyConfigExistingShapes(unittest.TestCase):
    def _assert_clean_exit(self, existing_content):
        mod = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "openclaw.json"
            cfg.write_text(existing_content)
            with self.assertRaises(SystemExit) as cm:
                mod.apply_config({"models": {}}, cfg)
            self.assertNotEqual(cm.exception.code, 0)
            self.assertIn("JSON object", str(cm.exception))

    def test_list_config_fails_cleanly(self):
        self._assert_clean_exit("[1, 2, 3]")

    def test_null_config_fails_cleanly(self):
        self._assert_clean_exit("null")

    def test_string_config_fails_cleanly(self):
        self._assert_clean_exit('"hello"')

    def test_corrupt_json_still_fails_cleanly(self):
        mod = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "openclaw.json"
            cfg.write_text("{oops")
            with self.assertRaises(SystemExit) as cm:
                mod.apply_config({"models": {}}, cfg)
            self.assertIn("Invalid JSON", str(cm.exception))

    def test_object_config_merges(self):
        mod = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "openclaw.json"
            cfg.write_text('{"keep": {"a": 1}}')
            mod.apply_config({"models": {"m": {"id": "m"}}}, cfg)
            merged = __import__("json").loads(cfg.read_text())
            self.assertEqual(merged["keep"], {"a": 1})
            self.assertIn("m", merged["models"])


if __name__ == "__main__":
    unittest.main()
