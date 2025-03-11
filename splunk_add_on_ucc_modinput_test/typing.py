
from typing import Any, Callable, Generator, Union


ProbeGenType = Union[Callable[..., Generator[int, None, None]]]
ProbeFnType = Union[ProbeGenType, Callable[..., Any]]
ForgeType = Union[ Callable[..., Generator[Any, None, None]], Callable[..., Any]]