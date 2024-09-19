from enum import Enum


class ForgeProbe(Enum):
    DEFAULT_INTERVAL = 5
    MAX_WAIT_TIME = 600
    MAX_INTERWAL = 60
    MIN_INTERVAL = 1


DEPENDENCIES_WAIT_TIMEOUT = 600


class BuiltInArg(Enum):
    SPLUNK_CLIENT = "splunk_client"
    VENDOR_CLIENT = "vendor_client"


class ForgeScope(Enum):
    FUNCTION = "function"
    MODULE = "module"
    SESSION = "session"
