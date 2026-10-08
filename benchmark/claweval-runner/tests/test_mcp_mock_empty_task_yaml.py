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

"""MockServiceManager must treat an empty task.yaml as no services.

It keeps its own yaml.safe_load call; an empty document returned None
and __init__ crashed on task.get("services") before the MCP facade
could even start, taking the whole mock-service bridge down.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ce_runner.mcp_mock_services import MockServiceManager  # noqa: E402


class TestMockServiceManagerEmptyYaml(unittest.TestCase):
    def test_empty_task_yaml_initialises_with_no_services(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "task.yaml"
            p.write_text("")
            mgr = MockServiceManager(p)
            self.assertEqual(mgr.services, [])
            self.assertEqual(mgr.tool_endpoints, [])

    def test_comment_only_task_yaml_initialises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "task.yaml"
            p.write_text("# TODO: add services\n")
            mgr = MockServiceManager(p)
            self.assertEqual(mgr.services, [])


if __name__ == "__main__":
    unittest.main()
