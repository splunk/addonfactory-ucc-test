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
import time
from typing import Callable
from splunk_add_on_ucc_modinput_test.common.splunk_instance import (
    search,
    Configuration,
    SearchState,
    Index,
)
from splunk_add_on_ucc_modinput_test.common.splunk_service_pool import (
    SplunkServicePool,
)
from splunk_add_on_ucc_modinput_test.common.ta_base import ConfigurationBase
from splunk_add_on_ucc_modinput_test.functional.common.splunk_instance_file import (  # noqa: E501
    SplunkInstanceFileHelper,
)
from splunk_add_on_ucc_modinput_test.typing import ProbeGenType
import logging

logger = logging.getLogger("ucc-modinput-test")


class SplunkClientBase:
    def __init__(
        self, splunk_configuration: Configuration | None = None
    ) -> None:
        self.ta_service: ConfigurationBase | None = None
        self._splunk_configuration = splunk_configuration or Configuration()
        self._bind_swagger_client()

    _bind_swagger_client: Callable[..., None] = lambda: None
    # this method is replaced in inherited class by the decorator
    # splunk_add_on_ucc_modinput_test.functional.decorators.register_splunk_class
    # pass

    @property
    def splunk_configuration(self) -> Configuration:
        return self._splunk_configuration

    @property
    def config(self) -> Configuration:  # short alias for splunk_configuration
        return self._splunk_configuration

    @property
    def splunk(self) -> SplunkServicePool:
        return self._splunk_configuration.service

    @property
    def ta_api(
        self,
    ) -> swagger_client.api.default_api.DefaultApi:  # type: ignore    # noqa: E501, F821
        assert (
            self.ta_service is not None
        ), "Make sure you have decorated inherited client class \
            with @register_splunk_class"
        return self.ta_service._api_instance

    @property
    def instance_epoch_time(self) -> int:
        state = self.search("| makeresults | eval splunk_epoch_time=_time")
        if isinstance(state.results, list) and len(state.results) > 0:
            first_result = state.results[0]
            if (
                isinstance(first_result, dict)
                and "splunk_epoch_time" in first_result
            ):
                return int(first_result["splunk_epoch_time"])
        raise ValueError(
            "Expected a list of dictionaries with 'splunk_epoch_time' key \
                in search results"
        )

    @property
    def default_index(self) -> str:
        state = self.search("* | head 1 | fields index")
        if isinstance(state.results, list) and len(state.results) > 0:
            first_result = state.results[0]
            if isinstance(first_result, dict) and "index" in first_result:
                return first_result["index"]
        raise ValueError(
            "Expected a list of dictionaries with 'index' key in search \
                results"
        )

    def _make_conf_error(self, prop_name: str) -> str:
        return f"Make sure you have '{prop_name}' attribute in your Splunk \
            configuration class {self.config.__class__.__name__}"

    @property
    def remote_file_helper(self) -> SplunkInstanceFileHelper:
        connect = dict(
            splunk_url=f"https://{self.config.host}:{self.config.port}",
            username=self.config.username,
            password=self.config.password,
        )
        return SplunkInstanceFileHelper(**connect)

    @property
    def instance_file_helper(self) -> SplunkInstanceFileHelper:
        assert (
            hasattr(self.config, "home")
            and self.config.splunk_home  # type: ignore
        ), self._make_conf_error("home")
        connect = dict(
            splunk_url=f"https://{self.config.host}:{self.config.port}",
            username=self.config.username,
            password=self.config.password,
            base_dir=self.config.home,
        )
        return SplunkInstanceFileHelper(**connect)

    @property
    def app_file_helper(self) -> SplunkInstanceFileHelper:
        assert hasattr(self.config, "home") and self._make_conf_error("home")
        assert hasattr(self.config, "app_name") and self._make_conf_error(
            "app_name"
        )
        connect = dict(
            splunk_url=f"https://{self.config.host}:{self.config.port}",
            username=self.config.username,
            password=self.config.password,
            base_dir=f"{self.config.home}/etc/apps/{self.config.app_name}",
        )
        return SplunkInstanceFileHelper(**connect)

    def search(self, searchquery: str) -> SearchState:
        return search(service=self.splunk, searchquery=searchquery)

    @property
    def _is_cloud(self) -> bool:
        return "splunkcloud.com" in self.config.host.lower()

    def create_index(self, index_name: str) -> Index:
        return self.config.create_index(
            index_name,
            self.splunk,
            is_cloud=self._is_cloud,
            acs_stack=self.config.acs_stack if self._is_cloud else None,
            acs_server=self.config.acs_server if self._is_cloud else None,
            splunk_token=self.config.token if self._is_cloud else None,
        )

    def get_index(self, index_name: str) -> Index | None:
        return self.config.get_index(
            index_name,
            self.splunk,
        )

    def search_probe(
        self,
        probe_spl: str,
        *,
        verify_fn: Callable[[SearchState], bool] | None = None,
        timeout: int = 300,
        interval: int = 5,
        probe_name: str | None = "probe",
    ) -> ProbeGenType:
        """
        Probe state by search until it returns verify function return true.
        Default verify function checks for non empty search result.
        @param probe_spl: Splunk search query to execute for each check
                iteration.
        @param verify_fn: function to verify search state.
        @param timeout: how long in seconds to wait for positive result.
        @param interval: interval to repeat search.
        @return: True, if probe conditions met before expiration,
            otherwise False.
        """

        def non_empty_result(state: SearchState) -> bool:
            return state.result_count > 0

        if verify_fn is None:
            verify_fn = non_empty_result
        else:
            assert callable(verify_fn)

        if probe_name is None:
            probe_name = verify_fn.__name__

        start_time = time.time()
        logger.debug(probe_spl)
        expire = start_time + timeout
        while time.time() < expire:
            search_state = self.search(searchquery=probe_spl)
            if verify_fn(search_state):
                logger.debug(
                    f"{probe_name} has successfully finished after "
                    f"{time.time() - start_time} seconds"
                )
                return True
            logger.debug(
                f"{probe_name} is negative after "
                f"{time.time()-start_time} seconds"
            )
            yield interval

        logger.info(f"{probe_name} is still negative after {timeout} seconds")
        return False

    def repeat_search_until(
        self,
        spl: str,
        *,
        condition_fn: Callable[[SearchState], bool] | None = None,
        timeout: int = 300,
        interval: int = 5,
    ) -> SearchState | None:
        """
        Repeats search until condition function returns True.
        Default condition function checks for non empty search result.
        @param spl: Splunk search query to execute.
        @param condition_fn: function to verify search state to stop search
                iterations.
        @param timeout: how long in seconds to wait for positive result of
                condition function.
        @param interval: interval to repeat search if condition function is
                negative.
        @return: SearchState object.
        """

        it = self.search_probe(
            probe_spl=spl,
            verify_fn=condition_fn,
            timeout=timeout,
            interval=interval,
            probe_name=None,
        )

        try:
            while True:
                wait = next(it)
                time.sleep(wait)
        except StopIteration as si:
            return si.value
