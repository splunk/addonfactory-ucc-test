#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import logging
import traceback
import requests
from requests import Response

from splunktaucclib.rest_handler.error import RestError
from solnlib import conf_manager, log

ADDON_NAME = "demo_addon_for_splunk"

def set_logger(session_key, filename):
    """
    This function sets up a logger with configured log level.
    :param filename: Name of the log file
    :return logger: logger object
    """
    logger = log.Logs().get_logger(filename)
    log_level = conf_manager.get_log_level(
        logger=logger,
        session_key=session_key,
        app_name=ADDON_NAME,
        conf_name=f"{ADDON_NAME.lower()}_settings",
    )
    logger.setLevel(log_level)
    return logger

def set_logger_for_input(session_key, input_name) -> logging.Logger:
    return set_logger(session_key, f"{ADDON_NAME.lower()}_{input_name}")

class Connect:
    def __init__(self, *, logger) -> None:
        self.logger = logger

    @staticmethod
    def status_code(response: Response) -> int:
        return response.status_code if response and response.status_code else 400

    def get(
        self,
        *,
        uri,
    ):
        try:
            r = requests.get(uri)
            if r:
                self.logger.debug(f"Successfully get {uri}")
                return r
            else:
                msg = f"Failed to get {uri}"
                self.logger.warning(msg + traceback.format_exc())
                raise RestError(Connect.status_code(r), msg)
        except Exception:
            msg = f"Failed to connect to {uri} and get data"
            self.logger.error(msg + traceback.format_exc())
            raise RestError(400, msg)

class Validator:
    def __init__(self, *, session_key) -> None:
        self.connect = Connect(
            logger=set_logger(session_key, ADDON_NAME.lower())
        )

    def validate(self, *, uri):
        self.connect.get(
            uri=uri,
        )
