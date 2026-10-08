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

"""Mock-service env values from task.yaml may be non-strings.

YAML parses ``RETRY: 3`` as an int. start_mock_services_with_offset()
called ``.startswith('tasks/')`` on the raw value and crashed with an
AttributeError before the service process could even launch. Values are
stringified before the tasks/ prefix check (and subprocess env vars must
be strings anyway).
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ce_runner import parallel  # noqa: E402


class TestMockServiceEnvValues(unittest.TestCase):
    def _run_with_yaml(self, tmpdir: str, env_block: str):
        ty = Path(tmpdir) / "task.yaml"
        ty.write_text(
            "services:\n"
            "  - name: mail\n"
            "    port: 9100\n"
            "    command: python3 -m http.server\n"
            "    ready_timeout: 1\n"
            f"    env:\n{env_block}"
        )
        spawned = []
        with mock.patch.object(
            parallel.subprocess, "Popen",
            side_effect=lambda *a, **k: spawned.append((a, k)) or mock.MagicMock(),
        ), mock.patch.object(
            parallel.httpx, "post", side_effect=OSError("service down"),
        ):
            parallel.start_mock_services_with_offset(str(ty), tmpdir, 0)
        return spawned

    def test_integer_env_value_is_stringified(self):
        with tempfile.TemporaryDirectory() as tmp:
            spawned = self._run_with_yaml(tmp, "      RETRY: 3\n")
            self.assertEqual(len(spawned), 1)
            self.assertEqual(spawned[0][1]["env"]["RETRY"], "3")

    def test_boolean_env_value_is_stringified(self):
        with tempfile.TemporaryDirectory() as tmp:
            spawned = self._run_with_yaml(tmp, "      DEBUG: true\n")
            self.assertEqual(spawned[0][1]["env"]["DEBUG"], str(True))

    def test_tasks_prefix_still_resolves(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            spawned = self._run_with_yaml(tmp, "      DATA: tasks/fixtures/mail.json\n")
            env = spawned[0][1]["env"]
            project_root = os.path.abspath(os.path.join(tmp, "..", ".."))
            self.assertEqual(env["DATA"],
                             os.path.join(project_root, "tasks/fixtures/mail.json"))

    def test_plain_string_env_value_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            spawned = self._run_with_yaml(tmp, "      GREETING: hello\n")
            self.assertEqual(spawned[0][1]["env"]["GREETING"], "hello")


if __name__ == "__main__":
    unittest.main()
