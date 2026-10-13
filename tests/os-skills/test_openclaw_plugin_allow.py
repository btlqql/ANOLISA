"""Regression tests for existing OpenClaw plugin configuration shapes."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


INSTALLER = (
    Path(__file__).resolve().parents[2]
    / "src/os-skills/ai/install-openclaw/scripts/install_openclaw.py"
)
spec = importlib.util.spec_from_file_location("install_openclaw", INSTALLER)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class PluginAllowShapeTests(unittest.TestCase):
    def test_nonobject_plugins_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "openclaw.json"
            original = '{"plugins": null, "custom": 42}\n'
            config_path.write_text(original, encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "plugins must be an object"):
                installer.apply_config({"models": {}}, config_path)
            self.assertEqual(config_path.read_text(encoding="utf-8"), original)
            self.assertFalse(config_path.with_name("openclaw.json.bak").exists())

    def test_string_allow_is_not_split_into_characters(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "openclaw.json"
            original = '{"plugins": {"allow": "existing"}}\n'
            config_path.write_text(original, encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "plugins.allow must be a list"):
                installer.apply_config(
                    {"plugins": {"allow": ["dingtalk"]}}, config_path
                )
            self.assertEqual(config_path.read_text(encoding="utf-8"), original)

    def test_valid_allowlist_preserves_order_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "openclaw.json"
            config_path.write_text(
                json.dumps({"plugins": {"allow": ["existing", "dingtalk"]}}),
                encoding="utf-8",
            )
            installer.apply_config(
                {"plugins": {"allow": ["dingtalk", "new"]}}, config_path
            )
            result = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(result["plugins"]["allow"], ["existing", "dingtalk", "new"])


if __name__ == "__main__":
    unittest.main()
