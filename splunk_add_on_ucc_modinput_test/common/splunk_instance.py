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
from .splunk_service_pool import SplunkServicePool

MODINPUT_TEST_SPLUNK_INDEX_LOCK = "MODINPUT_TEST_SPLUNK_INDEX_LOCK"
MODINPUT_TEST_SPLUNK_DEDICATED_INDEX = "MODINPUT_TEST_SPLUNK_DEDICATED_INDEX"


class Configuration:
    @staticmethod
    def get_index_from_classic_instance(
            index_name: str,
            client_service: SplunkServicePool,
            acs_stack: str,
            acs_server: str,
            splunk_token: str) -> Index:
        url = f"{acs_server}/{acs_stack}/adminconfig/v2/indexes/{index_name}"

        headers = {
            "Authorization": "Bearer " + splunk_token,
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            if not client_service._host.startswith(acs_stack):
                new_host_start = client_service._host.find(acs_stack)
            host = client_service._host[new_host_start:]
            service = SplunkServicePool(host=host, port=client_service._port, username=client_service._username,
                                        password=client_service._password)
            return Index(service, f"/services/data/indexes/{index_name}")
        else:
            idx_not_created_msg = f"Index {index_name} was not found on stack {acs_stack} controlled by {acs_server}."
            utils.logger.critical(idx_not_created_msg)
            return None

    @staticmethod
    def get_index(
            index_name: str,
            client_service: SplunkServicePool,
            acs_stack: str = None,
            acs_server: str = None,
            splunk_token: str = None) -> Index:
        if any(i.name == index_name for i in client_service.indexes):
            return client_service.indexes[index_name]
        else:
            if acs_stack:
                return Configuration.get_index_from_classic_instance(index_name, client_service, acs_stack, acs_server,
                                                                     splunk_token)
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
            retries = Retry(total=25, backoff_factor=1, status_forcelist=[404])
            session.mount("https://", HTTPAdapter(max_retries=retries))
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

    @staticmethod
    def create_index(
        index_name: str,
        client_service: SplunkServicePool,
        *,
        is_cloud: bool = False,
        acs_stack: str = None,
        acs_server: str = None,
        splunk_token: str = None,
    ) -> Index:
        if Configuration.get_index(index_name, client_service, acs_stack, acs_server, splunk_token):
            reason = f"Index {index_name} already exists"
            utils.logger.critical(reason)
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
                acs_stack,
                acs_server,
                splunk_token
            )
        else:
            created_index = Configuration._enterprise_create_index(
                index_name,
                client_service,
            )
        utils.logger.debug(
            f"Index {index_name} has just been created"
        )
        return created_index

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
        instance._service = SplunkServicePool(
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
            instance._dedicated_index = (
                instance.create_index(
                    f"idx_{utils.Common().sufix}",
                    instance._service,
                    is_cloud=instance._is_cloud,
                    acs_stack=instance._acs_stack,
                    acs_server=instance._acs_server,
                    splunk_token=instance._token,
                )
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
