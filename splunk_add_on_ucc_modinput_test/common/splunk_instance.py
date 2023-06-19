import time
import pytest
from splunklib import client
from splunklib.client import Service
from splunklib.client import Job
from splunklib.client import Index
import splunklib.results as results
from splunk_add_on_ucc_modinput_test.common import utils


class Configuration:
    def get_index(self, index_name, client_service):
        if any(i.name == index_name for i in client_service.indexes):
            return client_service.indexes[index_name]
        else:
            return None
    
    def _create_dedicated_index(self, client_service):
        the_index_name = f"idx_{utils.Common().sufix}"
        if self.get_index(the_index_name,client_service) != None:
            pytest.exit(f"Index {the_index_name} already exists")
        idx_not_created_msg = f"Index {the_index_name} was not created"
        try:
            new_index = client_service.indexes.create(the_index_name)
        except Exception as e:
            pytest.exit(f"{idx_not_created_msg}\nException raised:\n{e}")
        if new_index:
            return new_index
        else:
            pytest.exit(idx_not_created_msg)

    __instance = None

    def __new__(cls, *args, **kwargs):
        if not Configuration.__instance:
            Configuration.__instance = object.__new__(cls)
            Configuration.__instance._host = utils.get_from_environment_variable(
                "MODINPUT_TEST_SPLUNK_HOST"
            )
            Configuration.__instance._port = utils.get_from_environment_variable(
                "MODINPUT_TEST_SPLUNK_PORT"
            )
            Configuration.__instance._username = utils.get_from_environment_variable(
                "MODINPUT_TEST_SPLUNK_USERNAME"
            )
            Configuration.__instance._password = utils.get_from_environment_variable(
                "MODINPUT_TEST_SPLUNK_PASSWORD_BASE64",
                string_function=utils.Base64.decode,
            )
            Configuration.__instance._service = client.connect(
                host=Configuration.__instance._host,
                port=Configuration.__instance._port,
                username=Configuration.__instance._username,
                password=Configuration.__instance._password,
            )
            dedicated_index_name = utils.get_from_environment_variable(
                "MODINPUT_TEST_SPLUNK_DEDICATED_INDEX",
                is_optional=True,
            )
            if dedicated_index_name:
                Configuration.__instance._dedicated_index = Configuration.__instance.get_index(dedicated_index_name,Configuration.__instance._service)
                if Configuration.__instance._dedicated_index == None:
                    pytest.exit(f"Environment variable MODINPUT_TEST_SPLUNK_DEDICATED_INDEX set to {dedicated_index_name}, but Splunk instance {Configuration.__instance._host} does not contain such index. Remove the variable or create the index.")
            else:
                Configuration.__instance._dedicated_index = (
                    Configuration.__instance._create_dedicated_index(
                        Configuration.__instance._service
                    )
                )
        return Configuration.__instance

    def __init__(self):
        pass

    @property
    def host(self) -> str:
        return self._host

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
                for result in results.JSONResultsReader(job.results(output_mode="json"))
            ]
            if self._is_done
            else None
        )

    @property
    def result_count(self) -> int:
        return self._result_count


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
