from typing import Any, Callable, Dict, Generator, Tuple, Union, Optional

ProbeGenType = Generator[int, None, Optional[bool]]
ProbeGenFnType = Callable[..., ProbeGenType]
ProbeRegularFnType = Callable[..., Any]
ProbeFnType = Union[ProbeGenFnType, ProbeRegularFnType]

ForgeGenType = Generator[Any, None, None]
ForgeGenFnType = Callable[..., ForgeGenType]
ForgeRegularFnType = Callable[..., Any]
ForgeFnType = Union[ForgeGenFnType, ForgeRegularFnType]

TestFnType = Callable[..., Any]

ArtifactsType = Dict[str, Any]
ExecutableKeyType = Tuple[str, ...]
