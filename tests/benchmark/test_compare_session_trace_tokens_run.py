"""Selected-run input checks for the standalone token audit script."""

import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "benchmark/claweval-runner/scripts/compare_session_trace_tokens.py"


def invoke(root: Path, run: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--run", run],
        capture_output=True,
        text=True,
    )


def test_missing_run_is_not_reported_as_success(tmp_path):
    result = invoke(tmp_path, "missing")
    assert result.returncode != 0
    assert "no such run dir" in result.stderr
    assert "total_pairs: 0" not in result.stdout


def test_empty_selected_run_is_not_reported_as_success(tmp_path):
    (tmp_path / "empty").mkdir()
    result = invoke(tmp_path, "empty")
    assert result.returncode != 0
    assert "no session traces" in result.stderr


def test_run_must_name_a_direct_child(tmp_path):
    result = invoke(tmp_path, "../elsewhere")
    assert result.returncode != 0
    assert "directly under --root" in result.stderr


def test_selected_run_with_session_is_compared(tmp_path):
    sessions = tmp_path / "valid" / "sessions"
    sessions.mkdir(parents=True)
    (sessions / "trial.session.jsonl").write_text(
        '{"message":{"role":"assistant","usage":{"input":2,"output":3}}}\n',
        encoding="utf-8",
    )
    (tmp_path / "valid" / "trial.jsonl").write_text(
        '{"type":"message","message":{"role":"assistant"},'
        '"usage":{"input_tokens":2,"output_tokens":3}}\n',
        encoding="utf-8",
    )
    result = invoke(tmp_path, "valid")
    assert result.returncode == 0, result.stderr
    assert "total_pairs: 1" in result.stdout
    assert "matched: 1" in result.stdout
