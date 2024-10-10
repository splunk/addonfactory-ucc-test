from enum import Enum


class ForgeProbe(Enum):
    DEFAULT_INTERVAL = 5
    MAX_WAIT_TIME = 300
    MAX_INTERWAL = 60
    MIN_INTERVAL = 1


class TasksWait(Enum):
    TIMEOUT = 1000
    CHECK_FREQUENCY = 1

class BuiltInArg(Enum):
    SPLUNK_CLIENT = "splunk_client"
    VENDOR_CLIENT = "vendor_client"


class ForgeScope(Enum):
    FUNCTION = "function"
    MODULE = "module"
    SESSION = "session"
