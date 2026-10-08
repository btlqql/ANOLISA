# Copyright 2026 Alibaba Cloud
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""mcp_mock_services._start_service must coerce env values to strings.

YAML parses ``RETRY: 3`` as an int; the tasks/ prefix check called
.startswith() on the raw value and crashed with AttributeError before
the service process could launch — the same defect parallel.py had.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import ce_runner.mcp_mock_services as mms  # noqa: E402
from ce_runner.mcp_mock_services import MockServiceManager  # noqa: E402


def _manager_with_env(tmpdir: str, env_block: str) -> MockServiceManager:
    ty = Path(tmpdir) / "task.yaml"
    ty.write_text(
        "services:\n"
        "  - name: mail\n"
        "    port: 9100\n"
        "    command: python3 -m http.server\n"
        f"    env:\n{env_block}"
    )
    return MockServiceManager(ty)


def _spawn_with_env(mgr: MockServiceManager):
    spawned = []
    with mock.patch.object(
        mms.subprocess, "Popen",
        side_effect=lambda *a, **k: spawned.append((a, k)) or mock.MagicMock(),
    ), mock.patch.object(mms.time, "sleep"), mock.patch.object(
        mgr, "_is_healthy", return_value=False,
    ), mock.patch.object(
        mgr, "_wait_health", return_value=True,
    ):
        mgr.start_all()
    return spawned


class TestEnvValueCoercion(unittest.TestCase):
    def test_integer_env_value_is_stringified(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = _manager_with_env(tmp, "      RETRY: 3\n")
            spawned = _spawn_with_env(mgr)
            self.assertEqual(spawned[0][1]["env"]["RETRY"], "3")

    def test_boolean_env_value_is_stringified(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = _manager_with_env(tmp, "      DEBUG: true\n")
            spawned = _spawn_with_env(mgr)
            self.assertEqual(spawned[0][1]["env"]["DEBUG"], str(True))

    def test_string_env_value_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = _manager_with_env(tmp, "      GREETING: hello\n")
            spawned = _spawn_with_env(mgr)
            self.assertEqual(spawned[0][1]["env"]["GREETING"], "hello")


if __name__ == "__main__":
    unittest.main()
