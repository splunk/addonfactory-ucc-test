from enum import Enum


class ForgeProbe(Enum):
    DEFAULT_INTERVAL = 5
    MAX_WAIT_TIME = 300
    MAX_INTERVAL = 60
    MIN_INTERVAL = 1


class TasksWait(Enum):
    TIMEOUT = 1000
    CHECK_FREQUENCY = 5


class BuiltInArg(Enum):
    SPLUNK_CLIENT = "splunk_client"
    VENDOR_CLIENT = "vendor_client"
    SESSION_ID = "session_id"
    TEST_ID = "test_id"


class ForgeScope(Enum):
    FUNCTION = "function"
    MODULE = "module"
    SESSION = "session"
