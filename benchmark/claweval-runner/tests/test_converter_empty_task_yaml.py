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

"""The converter has its own load_task_yaml; empty files crash it.

ce_runner.session_trace_converter is spawned as a subprocess and parses
task.yaml independently of _common.load_task_yaml. yaml.safe_load
returns None for an empty document and convert_session_to_trace called
task.get() on it, failing the phase_convert step of every trial with an
AttributeError.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ce_runner.session_trace_converter import (  # noqa: E402
    convert_session_to_trace,
    load_task_yaml,
)


class TestConverterEmptyTaskYaml(unittest.TestCase):
    def test_load_empty_yaml_returns_empty_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "task.yaml"
            p.write_text("")
            self.assertEqual(load_task_yaml(str(p)), {})

    def test_convert_with_empty_task_yaml_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = Path(tmp) / "session.jsonl"
            session.write_text(
                '{"type": "message", "timestamp": "2026-01-01T00:00:00+00:00",'
                ' "message": {"role": "user", "parts": [{"type": "text", "content": "hi"}]}}\n'
            )
            task_yaml = Path(tmp) / "task.yaml"
            task_yaml.write_text("")
            out = Path(tmp) / "trace.jsonl"
            meta = convert_session_to_trace(str(session), load_task_yaml(str(task_yaml)), str(out))
            # Conversion completes with audit_services=[] and a written trace.
            self.assertEqual(meta["audit_services"], [])
            self.assertEqual(meta["turns"], 0)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
