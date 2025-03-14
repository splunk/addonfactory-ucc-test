from typing import Any, Callable, Dict, Generator, Tuple, Union

ProbeGenType = Union[Callable[..., Generator[int, None, None]]]
ProbeFnType = Union[ProbeGenType, Callable[..., Any]]
ForgeType = Union[
    Callable[..., Generator[Any, None, None]], Callable[..., Any]
]
TestFnType = Callable[..., Any]

ArtifactsType = Dict[str, Any]
ExecutableKeyType = Tuple[str, ...]
