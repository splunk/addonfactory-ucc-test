class SplTaFwkBaseException(Exception):
    pass


class SplTaFwkWaitForProbeTimeout(SplTaFwkBaseException):
    pass


class SplTaFwkWaitForDependenciesTimeout(SplTaFwkBaseException):
    pass


class SplTaFwkDependencyExecutionError(SplTaFwkBaseException):
    pass
