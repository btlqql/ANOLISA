"""Model setup must preserve settings it does not edit."""

import importlib.util
from pathlib import Path

import yaml


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "benchmark/claweval-runner/scripts/configure_model.py"
)
spec = importlib.util.spec_from_file_location("configure_model", SCRIPT)
configure_model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(configure_model)

MODEL = {"api_key": "new-key", "base_url": "https://new.example", "model_id": "new-model"}
JUDGE = {"api_key": "judge-key", "base_url": "https://judge.example", "model_id": "judge-model"}
USER_AGENT = {"api_key": "agent-key", "base_url": "https://agent.example", "model_id": "agent-model"}


def test_existing_role_settings_are_preserved(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(
        yaml.safe_dump({
            "model": {"api_key": "old", "temperature": 0.2, "custom": {"retry": 2}},
            "judge": {"enabled": False, "timeout": 30},
            "user_agent_model": {"request_limit": 4},
            "defaults": {"trials": 3},
        }),
        encoding="utf-8",
    )

    configure_model.update_config_file(config, MODEL, JUDGE, USER_AGENT)
    result = yaml.safe_load(config.read_text(encoding="utf-8"))

    assert result["model"]["api_key"] == "new-key"
    assert result["model"]["temperature"] == 0.2
    assert result["model"]["custom"] == {"retry": 2}
    assert result["model"]["input_modalities"] == ["text", "image"]
    assert result["judge"]["enabled"] is False
    assert result["judge"]["timeout"] == 30
    assert result["user_agent_model"]["request_limit"] == 4
    assert result["defaults"] == {"trials": 3}


def test_new_config_keeps_existing_defaults(tmp_path):
    config = tmp_path / "config.yaml"
    configure_model.update_config_file(config, MODEL, JUDGE, USER_AGENT)
    result = yaml.safe_load(config.read_text(encoding="utf-8"))
    assert result["model"]["input_modalities"] == ["text", "image"]
    assert result["judge"]["enabled"] is True
    assert result["user_agent_model"]["model_id"] == "agent-model"
