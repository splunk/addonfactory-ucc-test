import os
import time
import datetime
from functools import lru_cache
import pytz
import logging

global logger
logger = logging.getLogger("tests_modinput")


def get_from_environment_variable(environment_variable: str) -> str:
    if environment_variable not in os.environ:
        logger.critical(40 * "*")
        logger.critical(f"{environment_variable} environment variable not set")
        logger.critical("run below in terminal:")
        logger.critical(f"export {environment_variable}=[your value]")
        logger.critical(40 * "*")
        exit(1)
    return os.environ[environment_variable]


def get_epoch_timestamp() -> float:
    return time.time()


@lru_cache(maxsize=32)
def convert_to_utc(epoch_timestamp: float, format: str = "%Y%m%d%H%M%S") -> str:
    return datetime.datetime.fromtimestamp(
        epoch_timestamp, pytz.timezone("UTC")
    ).strftime(format)


class Common(object):
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not Common.__instance:
            Common.__instance = object.__new__(cls)
            Common.__instance._start_timestamp = get_epoch_timestamp()
            logger.info(
                f"Test timestamp set to: {convert_to_utc(Common.__instance._start_timestamp)}"
            )
        return Common.__instance

    def __init__(self):
        pass

    @property
    def start_timestamp(self) -> float:
        return self._start_timestamp

    @property
    def sufix(self) -> str:
        return f"mit_{convert_to_utc(self.start_timestamp)}"
        # MIT from "MODULARINPUT TEST"
