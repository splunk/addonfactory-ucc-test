from enum import Enum


class ForgeProbe(Enum):
    DEFAULT_INTERVAL = 5
    MAX_INTERVAL = 60
    MIN_INTERVAL = 1
    DEFAILT_WAIT_TIME = 300
    MIN_WAIT_TIME = 60
    MAX_WAIT_TIME = 600


class TasksWait(Enum):
    DEFAULT_BOOTSTRAP_TIMEOUT = 1800
    MIN_BOOTSTRAP_TIMEOUT = 300
    MAX_BOOTSTRAP_TIMEOUT = 3600
    DEFAULT_ATTACHED_TIMEOUT = 600
    MIN_ATTACHED_TIMEOUT = 60
    MAX_ATTACHED_TIMEOUT = 1200
    DEFAULT_CHECK_FREQUENCY = 5
    MIN_CHECK_FREQUENCY = 1
    MAX_CHECK_FREQUENCY = 30


class BuiltInArg(Enum):
    SPLUNK_CLIENT = "splunk_client"
    VENDOR_CLIENT = "vendor_client"
    SESSION_ID = "session_id"
    TEST_ID = "test_id"


class ForgeScope(Enum):
    FUNCTION = "function"
    MODULE = "module"
    SESSION = "session"

class Executor(Enum):
    DEFAULT_THREAD_NUMBER = 10
    MIN_THREAD_NUMBER = 10
    MAX_THREAD_NUMBER = 20
