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

"""A typo'd --filter must fail validation, not crash in filter_instances().

``--filter '[unclosed'`` passed construction and exploded later inside
filter_instances with a raw ``re.error`` traceback — after the dataset
download. Compile the pattern at the pydantic boundary instead.
"""

import pytest
from pydantic import ValidationError

from swe_runner.common.models import DatasetConfig


class TestFilterRegexValidation:
    def test_valid_regex_constructs(self) -> None:
        assert DatasetConfig(filter_regex="^astropy.*").filter_regex == "^astropy.*"

    def test_none_regex_constructs(self) -> None:
        assert DatasetConfig(filter_regex=None).filter_regex is None

    def test_unterminated_class_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DatasetConfig(filter_regex="[unclosed")

    def test_stray_group_paren_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DatasetConfig(filter_regex="(oops")

    def test_error_message_names_the_field(self) -> None:
        with pytest.raises(ValidationError) as excinfo:
            DatasetConfig(filter_regex="[unclosed")
        assert "filter_regex" in str(excinfo.value)
