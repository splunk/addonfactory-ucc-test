#
# Copyright 2025 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from typing import Any, Dict, Set
import tempfile
from splunk_add_on_ucc_modinput_test.functional import logger
from typing import IO
import json
from base64 import b64encode
import ssl
import urllib.request
import urllib.parse


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
    ) -> None:
        self.file_set: Set[IO[str]] = set()
        self.splunk_url = splunk_url
        self.username = username
        self.password = password
        self.base_dir = base_dir

    def perform_api_operations(
        self, operation: str, payload: Dict[str, str] = {}
    ) -> Any:  # pylint: disable=dangerous-default-value
        """Performs API operations."""

        endpoint = (
            "/servicesNS/nobody/Splunk_TA_Modinput_Test/"
            "Splunk_TA_Modinput_Test_perform_crd_operation/<entry>/"
        )
        api_url = self.splunk_url + endpoint + operation

        payload.update({"output_mode": "json"})
        data = urllib.parse.urlencode(payload).encode("utf-8")

        # Create a request object
        request = urllib.request.Request(api_url, data=data, method="POST")

        # Add basic authentication header
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = b64encode(credentials.encode("utf-8")).decode(
            "utf-8"
        )
        request.add_header("Authorization", f"Basic {encoded_credentials}")

        # Disable SSL verification
        context = ssl._create_unverified_context()

        try:
            with urllib.request.urlopen(request, context=context) as response:
                if response.status > 299:
                    raise SplunkInstanceFileHelper.OperationError(
                        f"Operation: {operation}, failed. \
                            Response Code: {response.status}"
                    )
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise SplunkInstanceFileHelper.OperationError(
                f"Operation: {operation}, failed. \
                    Response Code: {e.code}, Message: {e.reason}"
            )

    def _make_path(self, filepath: str) -> str:
        """Makes path."""
        if self.base_dir == "":
            return filepath
        return f"{self.base_dir}/{filepath}"

    def isfile(self, filepath: str) -> bool:
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

    def isdir(self, dirpath: str) -> bool:
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

    def create_file(self, filepath: str, content: str = "") -> None:
        """Creates file."""
        payload = {"file_path": self._make_path(filepath), "data": content}
        self.perform_api_operations("create", payload)

    def overwrite_file(self, filepath: str, content: str = "") -> None:
        """Overwrites file."""
        self.create_file(filepath, content)

    def read_file(self, filepath: str) -> str:
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

    def append_file(self, filepath: str, content: str = "") -> None:
        """Updates file."""
        payload = {"file_path": self._make_path(filepath), "data": content}
        self.perform_api_operations("update", payload)

    def delete_file(self, filepath: str) -> bool:
        """Deletes file."""
        full_path = self._make_path(filepath)
        payload = {"file_path": full_path}
        json_response = self.perform_api_operations("delete", payload)
        logger.debug(f"Delete file {full_path} status: {json_response}")
        entry = json_response["entry"][0]
        if entry["name"] == "success_message":
            return True
        return False

    def remove_dir(self, dirpath: str) -> bool:
        """Removes directory."""
        full_path = self._make_path(dirpath)
        payload = {"dir_path": full_path}
        json_response = self.perform_api_operations("delete_dir", payload)
        logger.debug(f"Delete folder {full_path} status: {json_response}")
        entry = json_response["entry"][0]
        if entry["name"] == "success_message":
            return True
        return False

    def execute(self, command: str) -> str:
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

    def clean(self) -> None:
        """Clean method."""
        for temp in self.file_set:
            temp.close()

    def retrieve(self, path: str) -> str:
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
