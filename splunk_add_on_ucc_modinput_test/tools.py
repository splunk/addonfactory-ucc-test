#
# Copyright 2025 Splunk Inc.
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
#
from pathlib import Path
from splunk_add_on_ucc_modinput_test.common import utils
import json


def base64encode(
    text_file: Path,
    string: str,
) -> str:
    if string is None:
        string = text_file.read_text()
    return utils.Base64.encode(string=string)


def base64decode(base64_string: str) -> str:
    return utils.Base64.decode(base64_string=base64_string)


def get_rest_root(*, openapi: Path) -> str:
    with openapi.open() as f:
        data = json.load(f)
    paths = list(data.get("paths", {}).keys())
    common_prefix = utils.find_common_prefix(paths)
    if (
        common_prefix is None
        or common_prefix == ""
        or common_prefix[0] != "/"
        or common_prefix[-1] != "_"
    ):
        raise ValueError("Invalid common prefix")
        return ""
    return common_prefix[1:-1]
