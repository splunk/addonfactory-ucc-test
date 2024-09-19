import os
from splunk_add_on_ucc_modinput_test.functional import logger


class SplunkClientBase:
    def __init__(self, *args, **kwargs):
        self._auto_config()

    def _auto_config(self):
        self.splunk_version = os.environ.get("SPLUNK_VERSION", "latest")
        self.splunk_app_version = os.environ.get("SPLUNK_APP_VERSION", "latest")
        self.splunk_app_id = os.environ.get("SPLUNK_APP_ID", "")
        self.splunk_home = os.environ.get("SPLUNK_HOME", "/opt/splunk")
        self.splunk_host = os.environ.get("SPLUNK_HOST", "")
        self.splunk_user = os.environ.get("SPLUNK_USER", "admin")
        self.splunk_password = os.environ.get("SPLUNK_PASSWORD", "")
        self.splunk_hec_token = os.environ.get("SPLUNK_HEC_TOKEN", "")
        self.custom_config()

        # logger.debug(f"self.splunk_version: {self.splunk_version}")
        # logger.debug(f"self.splunk_app_version: {self.splunk_app_version}")
        # logger.debug(f"self.splunk_app_id: {self.splunk_app_id}")
        # logger.debug(f"self.splunk_home: {self.splunk_home}")
        # logger.debug(f"self.splunk_host: {self.splunk_host}")
        # logger.debug(f"self.splunk_user: {self.splunk_user}")
        # logger.debug(f"self.splunk_password: {self.splunk_password}")
        # logger.debug(f"self.splunk_hec_token: {self.splunk_hec_token}")

    def custom_config(self):
        pass
