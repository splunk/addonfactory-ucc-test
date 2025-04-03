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
import time
import random
import string
from enum import Enum


class IdentifierType(Enum):
    NUMERIC = 1
    ALPHA = 2
    ALPHANUM = 3
    HEX = 4


def _convert_to_anybase(number: int, base: str) -> str:
    size = len(base)
    if number == 0:
        return base[0]

    code = []
    while number > 0:
        number, r = divmod(number, size)
        code.append(base[r])

    return "".join(code)


def create_identifier(
    *,
    id_type: IdentifierType = IdentifierType.ALPHANUM,
    in_uppercase: bool = False
) -> str:
    time_based = int(time.time() * 10**5) % 10**10
    identifier = time_based * 10**3 + random.randint(0, 10**3)
    if id_type == IdentifierType.NUMERIC:
        return str(identifier)

    if id_type == IdentifierType.HEX:
        hex_identifier = hex(identifier)
        return (
            hex_identifier.upper() if in_uppercase else hex_identifier.lower()
        )

    if id_type == IdentifierType.ALPHA:
        base = string.ascii_lowercase
    elif id_type == IdentifierType.ALPHANUM:
        base = string.digits + string.ascii_lowercase

    other = _convert_to_anybase(identifier, base)
    return other.upper() if in_uppercase else other.lower()
