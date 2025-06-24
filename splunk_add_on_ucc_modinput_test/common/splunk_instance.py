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
from __future__ import annotations

# mypy: disable-error-code="attr-defined,arg-type"

import time
import pytest
from splunklib.client import Service
from splunklib.client import Job
from splunklib.client import Index
import splunklib.results as results
from splunk_add_on_ucc_modinput_test.common import utils
from .splunk_service_pool import SplunkServicePool
import json
from urllib import request, error
import ssl
import certifi
import logging
import re

logger = logging.getLogger("ucc-modinput-test")

MODINPUT_TEST_SPLUNK_DEDICATED_INDEX = "MODINPUT_TEST_SPLUNK_DEDICATED_INDEX"


class Configuration:
    @staticmethod
    def get_index(
        index_name: str, client_service: SplunkServicePool
    ) -> Index | None:
        if any(i.name == index_name for i in client_service.indexes):
            return client_service.indexes[index_name]
        else:
            return None

    @staticmethod
    def _validate_index_name(index_name: str) -> None:
        """
        Validate the index name according to Splunk's naming conventions.
        """
        if not index_name:
            reason = "Index name must not be empty"
            logger.error(reason)
            raise ValueError(reason)
        if not re.fullmatch(r"[a-z0-9_-]+", index_name):
            reason = (
                "Index name must consist of only numbers, "
                "lowercase letters, underscores, and hyphens."
            )
            logger.error(reason)
            raise ValueError(reason)
        if index_name.startswith(("_", "-")):
            reason = "Index name cannot begin with an underscore or hyphen."
            logger.error(reason)
            raise ValueError(reason)

    @staticmethod
    def _victoria_create_index(
        index_name: str, *, acs_stack: str, acs_server: str, splunk_token: str
    ) -> None:
        index_name = index_name.lower()
        Configuration._validate_index_name(index_name)
        url = f"{acs_server}/{acs_stack}/adminconfig/v2/indexes"
        data = json.dumps(
            {
                "datatype": "event",
                "maxDataSizeMB": 0,
                "name": index_name,
                "searchableDays": 365,
                "splunkArchivalRetentionDays": 366,
                "totalEventCount": "0",
                "totalRawSizeMB": "0",
            }
        ).encode("utf-8")
        headers = {
            "Authorization": "Bearer " + splunk_token,
            "Content-Type": "application/json",
        }
        idx_not_created_msg = f"Index {index_name} was not created on stack \
            {acs_stack} controlled by {acs_server}"

        req = request.Request(url, data=data, headers=headers, method="POST")

        context = ssl.create_default_context(cafile=certifi.where())

        retries_http_errors = 6
        for attempt_http in range(retries_http_errors):
            try:
                with request.urlopen(req, context=context) as response:
                    if response.status == 202:
                        retries = 25
                        backoff_factor = 1
                        for attempt in range(retries):
                            try:
                                get_req = request.Request(
                                    f"{url}/{index_name}",
                                    headers=headers,
                                    method="GET",
                                )
                                with request.urlopen(
                                    get_req, context=context
                                ) as get_response:
                                    if get_response.status == 200:
                                        return
                            except error.HTTPError as e:
                                if e.code == 404:
                                    time.sleep(backoff_factor * (2**attempt))
                                else:
                                    raise
                        idx_not_created_msg += (
                            " or creation time exceeded timeout"
                        )
                        break
            except error.HTTPError as e:
                # Retry logic for specific HTTP error codes:
                # 424: Failed Dependency - indicates a temporary issue with a required resource. # noqa: E501
                # 503: Service Unavailable - suggests the server is temporarily overloaded or down. # noqa: E501
                if e.code in (424, 503):
                    if attempt_http < retries_http_errors:
                        logger.info(
                            f"HTTP Response status {e.code}, retrying to "
                            f"create index {index_name}... "
                            f"{attempt_http + 1}/{retries_http_errors}"
                        )
                        time.sleep(2**attempt_http)
                        continue
                else:
                    # In case of HTTP errors other than 424 and 503
                    raise

            except Exception as e:
                idx_not_created_msg += f"\nException raised:\n{e}"
                break

        logger.critical(idx_not_created_msg)
        pytest.exit(idx_not_created_msg)

    @staticmethod
    def _enterprise_create_index(
        index_name: str, client_service: Service
    ) -> Index:
        idx_not_created_msg = f"Index {index_name} was not created on \
            instance {client_service.host}"
        try:
            new_index = client_service.indexes.create(index_name)
        except Exception as e:
            reason = f"{idx_not_created_msg}\nException raised:\n{e}"
            logger.critical(reason)
            pytest.exit(reason)
        if new_index:
            return new_index
        else:
            logger.critical(idx_not_created_msg)
            pytest.exit(idx_not_created_msg)

    @staticmethod
    def create_index(
        index_name: str,
        client_service: SplunkServicePool,
        *,
        is_cloud: bool = False,
        acs_stack: str | None = None,
        acs_server: str | None = None,
        splunk_token: str | None = None,
    ) -> Index:
        if Configuration.get_index(index_name, client_service):
            reason = f"Index {index_name} already exists"
            logger.critical(reason)
            pytest.exit(reason)
        if is_cloud:
            Configuration._victoria_create_index(
                index_name,
                acs_stack=acs_stack,
                acs_server=acs_server,
                splunk_token=splunk_token,
            )
            created_index = Configuration.get_index(
                index_name,
                client_service,
            )
        else:
            created_index = Configuration._enterprise_create_index(
                index_name,
                client_service,
            )
        logger.debug(f"Index {index_name} has just been created")
        return created_index

    __instances: dict[tuple[str, str, str], Configuration] = {}

    @classmethod
    def collect_host(cls) -> str | None:
        return utils.get_from_environment_variable("MODINPUT_TEST_SPLUNK_HOST")

    @classmethod
    def collect_port(cls) -> str | None:
        return utils.get_from_environment_variable("MODINPUT_TEST_SPLUNK_PORT")

    @classmethod
    def collect_username(cls) -> str | None:
        return utils.get_from_environment_variable(
            "MODINPUT_TEST_SPLUNK_USERNAME"
        )

    @classmethod
    def collect_password(cls) -> str | None:
        return utils.get_from_environment_variable(
            "MODINPUT_TEST_SPLUNK_PASSWORD_BASE64",
            string_function=utils.Base64.decode,
        )

    @classmethod
    def collect_splunk_dedicated_index(cls) -> str | None:
        return utils.get_from_environment_variable(
            MODINPUT_TEST_SPLUNK_DEDICATED_INDEX,
            is_optional=True,
        )

    @classmethod
    def collect_splunk_token(cls, is_optional: bool) -> str | None:
        return utils.get_from_environment_variable(
            "MODINPUT_TEST_SPLUNK_TOKEN_BASE64",
            string_function=utils.Base64.decode,
            is_optional=is_optional,
        )

    @classmethod
    def collect_acs_server(cls, is_optional: bool) -> str | None:
        return utils.get_from_environment_variable(
            "MODINPUT_TEST_ACS_SERVER",
            is_optional=is_optional,
        )

    @classmethod
    def collect_acs_stack(cls, is_optional: bool) -> str | None:
        return utils.get_from_environment_variable(
            "MODINPUT_TEST_ACS_STACK",
            is_optional=is_optional,
        )

    def __new__(cls, *args, **kwargs):  # type: ignore
        host = cls.collect_host()
        port = cls.collect_port()
        username = cls.collect_username()

        if host is None or port is None or username is None:
            raise ValueError("Host, port, and username must not be None")

        connection_key = (host, port, username)
        if connection_key in cls.__instances:
            return cls.__instances[connection_key]

        instance = object.__new__(cls)
        instance._host = host
        instance._port = port
        instance._username = username
        instance._password = cls.collect_password()

        dedicated_index_name = cls.collect_splunk_dedicated_index()

        instance._is_cloud = (
            "splunkcloud.com" in instance._host.lower()  # type: ignore
        )
        create_index_in_cloud = instance._is_cloud and not dedicated_index_name
        instance._token = cls.collect_splunk_token(
            is_optional=not create_index_in_cloud
        )
        instance._acs_server = cls.collect_acs_server(
            is_optional=not create_index_in_cloud
        )
        instance._acs_stack = cls.collect_acs_stack(
            is_optional=not create_index_in_cloud
        )
        instance._service = SplunkServicePool(
            host=instance._host,
            port=instance._port,
            username=instance._username,
            password=instance._password,
        )

        if dedicated_index_name:
            instance._dedicated_index = cls.get_index(
                dedicated_index_name, instance._service
            )
            if not instance._dedicated_index:
                reason = f"Environment variable \
                    {MODINPUT_TEST_SPLUNK_DEDICATED_INDEX} set to \
                        {dedicated_index_name}, but Splunk instance \
                            {instance._host} does not \
                                contain such index. Remove the variable \
                                    or create the index."
                logger.critical(reason)
                pytest.exit(reason)
            logger.debug(
                f"Existing index {dedicated_index_name} will be used for \
                    test in splunk {instance._host}"
            )
        else:
            instance._dedicated_index = instance.create_index(
                f"idx_{utils.Common().sufix}",
                instance._service,
                is_cloud=instance._is_cloud,
                acs_stack=instance._acs_stack,
                acs_server=instance._acs_server,
                splunk_token=instance._token,
            )

        logger.info(
            f"Splunk - host:port and user set to \
                {instance._host}:\
                    {instance._port}, \
                        {instance._username}"
        )

        if instance._dedicated_index is not None:
            logger.info(
                f"Splunk - index \
                    {instance._dedicated_index.name} will be \
                        used for the test run"
            )
        cls.__instances[connection_key] = instance
        return instance

    def __init__(self) -> None:
        pass

    @property
    def host(self) -> str:
        return self._host

    @property
    def is_cloud(self) -> bool:
        return self._is_cloud

    @property
    def port(self) -> int:
        return self._port

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

    @property
    def token(self) -> str:
        return self._token

    @property
    def acs_server(self) -> str:
        return (
            self._acs_server
            if self._acs_server or not self.is_cloud
            else "https://admin.splunk.com"
        )

    @property
    def acs_stack(self) -> str:
        return self._acs_stack

    @property
    def service(self) -> Service:
        return self._service

    @property
    def dedicated_index(self) -> Index:
        return self._dedicated_index


class SearchState:
    def __init__(self, job: Job):
        self._is_done = job["isDone"] == "1"
        self._done_progress = float(job["doneProgress"]) * 100
        self._scan_count = int(job["scanCount"])
        self._event_count = int(job["eventCount"])
        self._result_count = int(job["resultCount"])
        self._results = (
            [
                result
                for result in results.JSONResultsReader(
                    job.results(output_mode="json")
                )
            ]
            if self._is_done
            else None
        )

    @property
    def result_count(self) -> int:
        return self._result_count

    @property
    def results(self) -> list[object] | None:
        return self._results


def search(*, service: Service, searchquery: str) -> SearchState:
    search_state = None
    kwargs_normalsearch = {"exec_mode": "normal"}
    job = service.jobs.create(searchquery, **kwargs_normalsearch)
    while True:
        while not job.is_ready():
            pass
        if job["isDone"] == "1":
            search_state = SearchState(job)
            break
        time.sleep(1)
    job.cancel()
    return search_state
