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
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from splunk_add_on_ucc_modinput_test.typing import (
        ExecutableKeyType,
        ProbeFnType,
        ForgeFnType,
        TestFnType,
    )
import inspect
from typing import Any


class ExecutableBase:
    def __init__(
        self,
        function: ProbeFnType | ForgeFnType | TestFnType,
    ) -> None:
        assert callable(function)
        self._function = function
        self._inspect()

    @property
    def source_file(self) -> str:
        return self._fn_source_file

    @property
    def key(self) -> ExecutableKeyType:
        return (self._fn_source_file, self.fn_full_name)

    @property
    def original_key(self) -> ExecutableKeyType:
        return (self._fn_source_file, self.fn_original_full_name)

    @property
    def original_name(self) -> str:
        if self._original_name == "__call__":
            return (
                self._fn_bound_class.lower()
                if self._fn_bound_class
                else "__call__"
            )
        return self._original_name

    @property
    def fn_full_name(self) -> str:
        if self._fn_bound_class:
            return f"{self._fn_bound_class}::{self._fn_name}"
        else:
            return self._fn_name

    @property
    def fn_original_full_name(self) -> str:
        if self._fn_bound_class:
            return f"{self._fn_bound_class}::{self._original_name}"
        else:
            return self._original_name

    def _inspect(self) -> None:
        self._fn_bound_class: str | None = None
        if inspect.ismethod(self._function):
            self._fn_bound_class = self._function.__self__.__class__.__name__
            self._fn_name = self._function.__name__
            self._fn_source_file = inspect.getfile(self._function)
        elif inspect.isfunction(self._function):
            self._fn_bound_class = None
            res = repr(self._function).split(" ")[1].split(".")
            if len(res) > 1:
                self._fn_bound_class = res[0]
                self._fn_name = res[1]
            else:
                self._fn_name = res[0]
            self._fn_source_file = inspect.getfile(self._function)
        else:
            self._fn_name = "__call__"
            self._fn_bound_class = self._function.__class__.__name__
            self._fn_source_file = inspect.getfile(self._function.__class__)

        self._original_name = self._fn_name
        self._is_generatorfunction = inspect.isgeneratorfunction(
            self._function
        )

        sig = inspect.signature(self._function)
        self._required_args = list(sig.parameters.keys())

    @property
    def required_args_names(self) -> tuple[str, ...]:
        return tuple(self._required_args)

    def filter_requied_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in kwargs.items() if k in self._required_args}
