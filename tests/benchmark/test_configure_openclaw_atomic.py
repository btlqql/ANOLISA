"""The benchmark OpenClaw helper must not truncate a working config."""

import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "benchmark/claweval-runner/scripts/configure_openclaw.py"
)
spec = importlib.util.spec_from_file_location("configure_openclaw", SCRIPT)
configure_openclaw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(configure_openclaw)


def test_write_failure_keeps_original_bytes(tmp_path, monkeypatch):
    config_path = tmp_path / "openclaw.json"
    original = b'{"custom": "keep", "gateway": {"port": 19000}}\n'
    config_path.write_bytes(original)
    monkeypatch.setattr(configure_openclaw, "OPENCLAW_CONFIG", config_path)

    def fail_after_partial_write(_config, stream, **_kwargs):
        stream.write('{"partial":')
        raise OSError("simulated write failure")

    monkeypatch.setattr(configure_openclaw.json, "dump", fail_after_partial_write)
    with pytest.raises(OSError, match="simulated write failure"):
        configure_openclaw.main()

    assert config_path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [config_path]


def test_successful_write_keeps_config_content(tmp_path, monkeypatch):
    config_path = tmp_path / "openclaw.json"
    config_path.write_text('{"custom": "keep"}', encoding="utf-8")
    monkeypatch.setattr(configure_openclaw, "OPENCLAW_CONFIG", config_path)

    configure_openclaw.main()

    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["custom"] == "keep"
    assert config["gateway"]["port"] == 18789
    assert config["agents"]["defaults"]["skipBootstrap"] is True
    assert list(tmp_path.iterdir()) == [config_path]
