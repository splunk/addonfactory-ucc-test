#
# Copyright 2021 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from pathlib import Path
import base64

def base64encode(
    text_file: Path
) -> str:
    string = text_file.read_text()
    _bytes = string.encode('utf-8')
    base64_encoded = base64.b64encode(_bytes)
    base64_string = base64_encoded.decode('utf-8')
    return base64_encoded

def base64decode(
    base64_string: str
) -> str:
    base64_bytes = base64_string.encode('utf-8')
    decoded_bytes = base64.b64decode(base64_bytes)
    string = decoded_bytes.decode('utf-8')
    return string