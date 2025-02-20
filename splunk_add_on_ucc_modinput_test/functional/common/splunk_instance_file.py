#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import requests
import tempfile
from splunk_add_on_ucc_modinput_test.functional import logger


class SplunkInstanceFileHelper:
    """Class for Test file helper."""

    class OperationError(Exception):
        pass

    class FileReadError(OperationError):
        pass

    class ExecuteCommandError(OperationError):
        pass

    def __init__(
        self, splunk_url: str, username: str, password: str, base_dir: str = ""
    ):
        self.file_set = set()
        self.splunk_url = splunk_url
        self.username = username
        self.password = password
        self.base_dir = base_dir

    def perform_api_operations(
        self, operation, payload={}
    ):  # pylint: disable=dangerous-default-value
        """Performs API operations."""
        endpoint = (
            "/servicesNS/nobody/Splunk_TA_Modinput_Test/"
            "Splunk_TA_Modinput_Test_perform_crd_operation/<entry>/"
        )
        api_url = self.splunk_url + endpoint + operation

        payload.update({"output_mode": "json"})

        response = requests.request(
            "POST",
            api_url,
            auth=(self.username, self.password),
            data=payload,
            verify=False,
        )
        if response.status_code > 299:
            raise SplunkInstanceFileHelper.OperationError(
                f"Operation: {operation}, failed. \
                    Response Code:{response.status_code}"
            )
        return response.json()

    def _make_path(self, filepath):
        """Makes path."""
        if self.base_dir == "":
            return filepath
        return f"{self.base_dir}/{filepath}"

    def isfile(self, filepath):
        """Checks if file."""
        full_path = self._make_path(filepath)
        payload = {"file_path": full_path}
        json_response = self.perform_api_operations("is_file", payload)
        logger.debug(
            f"Checking file object is a file {full_path}: {json_response}"
        )
        entry = json_response["entry"][0]
        if entry["name"] == "success_message":
            return True
        return False

    def isdir(self, dirpath):
        """Checks if directory."""
        full_path = self._make_path(dirpath)
        payload = {"dir_path": full_path}
        json_response = self.perform_api_operations("is_dir", payload)
        logger.debug(
            f"Checking file object is a folder {full_path}: {json_response}"
        )
        entry = json_response["entry"][0]
        if entry["name"] == "success_message":
            return True
        return False

    def create_file(self, filepath, content=""):
        """Creates file."""
        payload = {"file_path": self._make_path(filepath), "data": content}
        self.perform_api_operations("create", payload)

    def overwrite_file(self, filepath, content=""):
        """Overwrites file."""
        self.create_file(filepath, content)

    def read_file(self, filepath):
        """Reads file."""
        full_path = self._make_path(filepath)
        payload = {"file_path": full_path}
        json_response = self.perform_api_operations("read", payload)
        logger.debug(f"Read file {full_path} status: {json_response}")
        entry = json_response["entry"][0]
        if entry["name"] != "error_message":
            return entry["content"]["file_content"]

        logger.error(f"Error reading file {full_path}: {json_response}")
        raise SplunkInstanceFileHelper.FileReadError(
            entry["content"]["read_error_message"]
        )

    def append_file(self, filepath, content=""):
        """Updates file."""
        payload = {"file_path": self._make_path(filepath), "data": content}
        self.perform_api_operations("update", payload)

    def delete_file(self, filepath):
        """Deletes file."""
        full_path = self._make_path(filepath)
        payload = {"file_path": full_path}
        json_response = self.perform_api_operations("delete", payload)
        logger.debug(f"Delete file {full_path} status: {json_response}")
        entry = json_response["entry"][0]
        if entry["name"] == "success_message":
            return True
        return False

    def remove_dir(self, dirpath):
        """Removes directory."""
        full_path = self._make_path(dirpath)
        payload = {"dir_path": full_path}
        json_response = self.perform_api_operations("delete_dir", payload)
        logger.debug(f"Delete folder {full_path} status: {json_response}")
        entry = json_response["entry"][0]
        if entry["name"] == "success_message":
            return True
        return False

    def execute(self, command):
        """Executes shell command."""
        payload = {"command": command}
        json_response = self.perform_api_operations("execute", payload)
        entry = json_response["entry"][0]
        if entry["name"] == "success_message":
            return entry["content"]["output"]

        logger.error(f"Error executiong command {command}: {json_response}")
        raise SplunkInstanceFileHelper.ExecuteCommandError(
            entry["content"]["read_error_message"]
        )

    def clean(self):
        """Clean method."""
        for temp in self.file_set:
            temp.close()

    def retrieve(self, path):
        """
        if remote, then copy the remote file to local
        if not remot, then return the path itself
        :param path: the file that want to get
        :return: local_path the copied file path
        """
        temp = (
            tempfile.NamedTemporaryFile(  # pylint: disable=consider-using-with
                mode="w+"
            )
        )
        self.file_set.add(temp)
        temp_path = temp.name
        data = self.read_file(path)
        temp.write(data)
        return temp_path
