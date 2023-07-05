import os
import time
import datetime
from functools import lru_cache
import pytz
import logging
import base64
import re
from pathlib import Path
from collections.abc import Callable

global logger
def init_logger():
    """
    Configure file based logger for the plugin
    """
    fh = logging.FileHandler("ucc_modinput_test.log")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(process)d - %(filename)s - %(funcName)s - %(message)s"
    )
    fh.setFormatter(formatter)
    logger = logging.getLogger("ucc-modinput-test")
    logger.addHandler(fh)
    logging.root.propagate = False
    logger.setLevel(logging.DEBUG)
    return logger

init_logger()
logger = logging.getLogger("ucc-modinput-test")
logger.debug("Logger set")

def get_from_environment_variable(
    environment_variable: str,
    *,
    string_function = None,
    # alternative_environment_variable = None,
    # alternative_string_function = None,
    is_optional: bool=False,
) -> str:
    def use_string_function_if_needed(*,variable,function):
        return variable if function == None else function(variable)
    # if environment_variable not in os.environ and alternative_environment_variable != None and alternative_environment_variable in os.environ:
    #     return use_string_function_if_needed(variable=os.environ[alternative_environment_variable],function=alternative_string_function)
    # el
    if environment_variable not in os.environ and is_optional:  return None
    if environment_variable not in os.environ:
        logger.critical(40 * "*")
        logger.critical(f"{environment_variable} environment variable not set")
        logger.critical("run below in terminal:")
        logger.critical(f"export {environment_variable}=[your value]")
        logger.critical(40 * "*")
        exit(1)
    return use_string_function_if_needed(variable=os.environ[environment_variable],function=string_function)


class Base64:
    
    @staticmethod
    def encode(string: str) -> str:
        _bytes = string.encode('utf-8')
        base64_encoded = base64.b64encode(_bytes)
        base64_string = base64_encoded.decode('utf-8')
        return base64_string
    
    @staticmethod
    def decode(
        base64_string: str
    ) -> str:
        base64_bytes = base64_string.encode('utf-8')
        decoded_bytes = base64.b64decode(base64_bytes)
        string = decoded_bytes.decode('utf-8').replace('\n', '')
        return string


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

def replace_line(
    *,
    file: Path,
    pattern: str,
    replacement: str,
    ):
    logger.debug(f"replace_line(file_path:{file},pattern:{pattern},replacement{replacement})")

    with file.open() as f:
        lines = f.readlines()

    found = False
    modified_lines = []
    for line in lines:
        if re.match(pattern, line):
            logger.debug(f"Found a line ({line}) that will be replaced")
            found = True
            line = re.sub(pattern, replacement, line)
        modified_lines.append(line)

    if found:
        with open(file, 'w') as file:
            file.writelines(modified_lines)
        logger.debug("Pattern found and replaced successfully. Leaving replace_line.")
    else:
        logger.debug("Pattern not found in the file. Leaving replace_line.")

