from __future__ import annotations

# mypy: disable-error-code="attr-defined,arg-type"

from typing import List, Optional, Dict, Tuple
import time
import pytest
import requests  # type: ignore
from requests.adapters import HTTPAdapter, Retry  # type: ignore
from splunklib import client
from splunklib.client import Service
from splunklib.client import Job
from splunklib.client import Index
import splunklib.results as results
from splunk_add_on_ucc_modinput_test.common import utils


MODINPUT_TEST_SPLUNK_INDEX_LOCK = "MODINPUT_TEST_SPLUNK_INDEX_LOCK"
MODINPUT_TEST_SPLUNK_DEDICATED_INDEX = "MODINPUT_TEST_SPLUNK_DEDICATED_INDEX"


class Configuration:
    @staticmethod
    def get_index(index_name: str, client_service: Service) -> Index:
        if any(i.name == index_name for i in client_service.indexes):
            return client_service.indexes[index_name]
        else:
            return None

    @staticmethod
    def _victoria_create_index(
        index_name: str, *, acs_stack: str, acs_server: str, splunk_token: str
    ) -> None:
        url = f"{acs_server}/{acs_stack}/adminconfig/v2/indexes"
        data = {
            "datatype": "event",
            "maxDataSizeMB": 0,
            "name": index_name,
            "searchableDays": 365,
            "splunkArchivalRetentionDays": 366,
            "totalEventCount": "0",
            "totalRawSizeMB": "0",
        }
        headers = {
            "Authorization": "Bearer " + splunk_token,
            "Content-Type": "application/json",
        }
        idx_not_created_msg = f"Index {index_name} was not created on stack \
            {acs_stack} controlleb by {acs_server}"
        response = requests.post(url, headers=headers, json=data)
        if response.ok:
            session = requests.Session()
            retries = Retry(total=5, backoff_factor=1, status_forcelist=[404])
            session.mount("http://", HTTPAdapter(max_retries=retries))
            response = session.get(f"{url}/{index_name}", headers=headers)
            if response.ok:
                return
            else:
                idx_not_created_msg += " or creation time exceeded timeout"
        utils.logger.critical(idx_not_created_msg)
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
            utils.logger.critical(reason)
            pytest.exit(reason)
        if new_index:
            return new_index
        else:
            utils.logger.critical(idx_not_created_msg)
            pytest.exit(idx_not_created_msg)

    __instances: dict[tuple[str, str, str], Configuration] = {}

    @classmethod
    def collect_host(cls) -> str:
        return utils.get_from_environment_variable(
            "MODINPUT_TEST_SPLUNK_HOST"
        )

    @classmethod
    def collect_port(cls) -> str:
        return utils.get_from_environment_variable(
            "MODINPUT_TEST_SPLUNK_PORT"
        )

    @classmethod
    def collect_username(cls) -> str:
        return utils.get_from_environment_variable(
            "MODINPUT_TEST_SPLUNK_USERNAME"
        )

    @classmethod
    def collect_password(cls) -> str:
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
    def collect_splunk_index_lock(cls) -> str | None:
        return utils.get_from_environment_variable(
            MODINPUT_TEST_SPLUNK_INDEX_LOCK,
            is_optional=True,
        )

    @classmethod
    def collect_splunk_token(cls, is_optional) -> str | None:
        return utils.get_from_environment_variable(
            "MODINPUT_TEST_SPLUNK_TOKEN_BASE64",
            string_function=utils.Base64.decode,
            is_optional=is_optional,
        )

    @classmethod
    def collect_acs_server(cls, is_optional) -> str | None:
        return utils.get_from_environment_variable(
            "MODINPUT_TEST_ACS_SERVER",
            is_optional=is_optional,
        )

    @classmethod
    def collect_acs_stack(cls, is_optional) -> str | None:
        return utils.get_from_environment_variable(
            "MODINPUT_TEST_ACS_STACK",
            is_optional=is_optional,
        )

    def __new__(cls, *args, **kwargs):  # type: ignore
        host = cls.collect_host()
        port = cls.collect_port()
        username = cls.collect_username()
        connection_key = (host, port, username)
        if connection_key in cls.__instances:
            return cls.__instances[connection_key]

        instance = object.__new__(cls)
        instance._host = host
        instance._port = port
        instance._username = username
        instance._password = cls.collect_password()

        dedicated_index_name = cls.collect_splunk_dedicated_index()

        index_lock = cls.collect_splunk_index_lock()
        existing_index = (
            dedicated_index_name if index_lock is None else index_lock
        )
        instance._is_cloud = (
            "splunkcloud.com" in instance._host.lower()  # type: ignore
        )
        create_index_in_cloud = instance._is_cloud and not existing_index
        instance._token = cls.collect_splunk_token(
            is_optional=not create_index_in_cloud
        )
        instance._acs_server = cls.collect_acs_server(
            is_optional=not create_index_in_cloud
        )
        instance._acs_stack = cls.collect_acs_stack(
            is_optional=not create_index_in_cloud
        )
        instance._service = client.connect(
            host=instance._host,
            port=instance._port,
            username=instance._username,
            password=instance._password,
        )

        if existing_index:
            instance._dedicated_index = cls.get_index(
                existing_index, instance._service
            )
            if not instance._dedicated_index:
                reason = f"Environment variable {MODINPUT_TEST_SPLUNK_INDEX_LOCK} or \
                    {MODINPUT_TEST_SPLUNK_DEDICATED_INDEX} set to \
                        {existing_index}, but Splunk instance \
                            {instance._host} does not \
                                contain such index. Remove the variable \
                                    or create the index."
                utils.logger.critical(reason)
                pytest.exit(reason)
            utils.logger.debug(
                f"Existing index {existing_index} will be used for \
                    test in splunk {instance._host}"
            )
        else:
            created_index_name = f"idx_{utils.Common().sufix}"
            if cls.get_index(created_index_name, instance._service):
                reason = f"Index {created_index_name} already exists"
                utils.logger.critical(reason)
                pytest.exit(reason)
            if create_index_in_cloud:
                cls._victoria_create_index(
                    created_index_name,
                    acs_stack=instance._acs_stack,
                    acs_server=instance._acs_server,
                    splunk_token=instance._token,
                )
                instance._dedicated_index = cls.get_index(
                    created_index_name,
                    instance._service,
                )
            else:
                instance._dedicated_index = (
                    cls._enterprise_create_index(
                        created_index_name,
                        instance._service,
                    )
                )
            utils.logger.debug(
                f"Index {created_index_name} has just been created in \
                    splunk {instance._host}"
            )

        utils.logger.info(
            f"Splunk - host:port and user set to \
                {instance._host}:\
                    {instance._port}, \
                        {instance._username}"
        )
        utils.logger.info(
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
