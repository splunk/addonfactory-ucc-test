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
# mypy: disable-error-code="attr-defined"

import os
import time
import datetime
from functools import lru_cache
import pytz  # type: ignore
import base64
from pathlib import Path
from typing import Callable, List, Optional
import hashlib
import logging

logger = logging.getLogger("ucc-modinput-test")


class SplunkClientConfigurationException(Exception):
    pass


def get_from_environment_variable(
    environment_variable: str,
    *,
    default_value: Optional[str] = None,
    is_optional: bool = False,
    string_function: Optional[Callable[[str], str]] = None,
) -> Optional[str]:
    def use_string_function_if_needed(
        *, variable: str, function: Optional[Callable[[str], str]] = None
    ) -> str:
        return variable if function is None else function(variable)

    if environment_variable in os.environ:
        return use_string_function_if_needed(
            variable=os.environ[environment_variable],
            function=string_function,
        )
    elif default_value is not None:
        return use_string_function_if_needed(
            variable=default_value,
            function=string_function,
        )
    elif is_optional:
        return None
    else:
        logger.critical(40 * "*")
        logger.critical(f"{environment_variable} environment variable not set")
        logger.critical("run below in terminal:")
        logger.critical(f"export {environment_variable}=[your value]")
        logger.critical(40 * "*")

        error = f"Mandatory environment variable {environment_variable} is \
            missing and does not have a default value specified."
        raise SplunkClientConfigurationException(error)


class Base64:
    @staticmethod
    def _remove_ending_chars(string: str) -> str:
        if len(string) == 0:
            return string
        CHARS_TO_BE_REMOVED = ["\n"]
        for i in range(len(string), -1, -1):
            if string[i - 1] not in CHARS_TO_BE_REMOVED:
                break
        return string[:i]

    @staticmethod
    def encode(string: str) -> str:
        _bytes = Base64._remove_ending_chars(string=string).encode("utf-8")
        base64_encoded = base64.b64encode(_bytes)
        base64_string = base64_encoded.decode("utf-8")
        return base64_string

    @staticmethod
    def decode(base64_string: str) -> str:
        base64_bytes = base64_string.encode("utf-8")
        decoded_bytes = base64.b64decode(base64_bytes)
        string = decoded_bytes.decode("utf-8")
        return Base64._remove_ending_chars(string=string)


def get_epoch_timestamp() -> float:
    return time.time()


@lru_cache(maxsize=32)
def convert_to_utc(
    epoch_timestamp: float, format: str = "%Y%m%d%H%M%S"
) -> str:
    return datetime.datetime.fromtimestamp(
        epoch_timestamp, pytz.timezone("UTC")
    ).strftime(format)


class Common:
    __instance = None

    def __new__(cls, *args, **kwargs):  # type: ignore
        if not Common.__instance:
            Common.__instance = object.__new__(cls)
            Common.__instance._start_timestamp = get_epoch_timestamp()
            logger.info(
                f"Test timestamp set to: \
                    {convert_to_utc(Common.__instance._start_timestamp)}"
            )
        return Common.__instance

    def __init__(self) -> None:
        pass

    @property
    def start_timestamp(self) -> float:
        return self._start_timestamp

    @start_timestamp.setter
    def start_timestamp(self, value: float) -> None:
        self._start_timestamp = value

    @property
    def sufix(self) -> str:
        return f"mit_{convert_to_utc(self.start_timestamp)}"
        # MIT from "MODULARINPUT TEST"


def find_common_prefix(strings: List[str]) -> Optional[str]:
    if strings is None or len(strings) == 0 or len(strings) == 1:
        return None
    elif len(strings) == 2:
        s0len = len(strings[0])
        s1len = len(strings[1])
        min_len = s0len if s0len < s1len else s1len
        for i in range(min_len):
            if strings[0][i] != strings[1][i]:
                return strings[0][:i]
        return strings[0][:min_len]
    else:
        common = find_common_prefix(strings[:2])
        if common is None or common == "":
            return common
        return find_common_prefix([common] + strings[2:])


def md5(*, file_path: Path, chunk_size: int = 8192) -> str:
    hash_md5 = hashlib.md5()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
