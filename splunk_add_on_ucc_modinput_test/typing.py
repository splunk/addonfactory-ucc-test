# from __future__ import annotations
# from typing import TYPE_CHECKING
from typing import Any, Callable, Dict, Generator, List, Tuple, Union

# if TYPE_CHECKING:
#     from splunk_add_on_ucc_modinput_test.functional.entities.task import (
#         FrameworkTask,
#     )


ProbeGenType = Union[Callable[..., Generator[int, None, None]]]
ProbeFnType = Union[ProbeGenType, Callable[..., Any]]
ForgeType = Union[
    Callable[..., Generator[Any, None, None]], Callable[..., Any]
]
ArtifactsType = Dict[str, Any]
ExecutableKeyType = Tuple[str, ...]
# TaskSetListType = List[List[FrameworkTask]]
