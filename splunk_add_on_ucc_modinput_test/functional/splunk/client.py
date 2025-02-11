import time
from typing import List, Optional, Tuple, Callable, Generator
from splunk_add_on_ucc_modinput_test.common.splunk_instance import (
    search,
    Configuration,
    SearchState,
    Index,
)
from splunk_add_on_ucc_modinput_test.common.utils import logger
from splunk_add_on_ucc_modinput_test.functional.common.splunk_instance_file import (
    SplunkInstanceFileHelper,
)


class SplunkClientBase:
    def __init__(
        self, splunk_configuration: Optional[Configuration] = None
    ) -> None:
        self.ta_service = None
        self._splunk_configuration = splunk_configuration or Configuration()
        self._bind_swagger_client()

    def _bind_swagger_client(self):
        # this method is replaced in inherited class by the decorator
        # splunk_add_on_ucc_modinput_test.functional.decorators.register_splunk_class
        pass

    @property
    def splunk_configuration(self):
        return self._splunk_configuration

    @property
    def config(self):  # short alias for splunk_configuration
        return self._splunk_configuration

    @property
    def splunk(self):
        return self._splunk_configuration.service

    @property
    def ta_api(self):
        assert (
            self.ta_service is not None
        ), "Make sure you have decorated inherited client class with @register_splunk_class"
        return self.ta_service.api_instance

    @property
    def instance_epoch_time(self) -> int:
        state = self.search("| makeresults | eval splunk_epoch_time=_time")
        return int(state.results[0]["splunk_epoch_time"])

    @property
    def default_index(self) -> str:
        state = self.search("* | head 1 | fields index")
        return state.results[0]["index"]

    def _make_conf_error(self, prop_name: str):
        return f"Make sure you have '{prop_name}' attribute in your Splunk configuration class {self.config.__class__.__name__}"

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
            hasattr(self.config, "home") and self.config.splunk_home
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

    def run_saved_search(
        self, saved_search_name: str
    ) -> Tuple[int, Optional[List[object]]]:
        saved_search = self.splunk.saved_searches[saved_search_name]
        state = search(
            service=self.splunk,
            searchquery=saved_search.content["search"],
        )
        logger.debug(
            f"Executed saved search {saved_search_name}, count: {state.result_count}, query: {saved_search.content['search']}"
        )
        return state.result_count, state.results

    def create_index(self, index_name: str) -> Index:
        return self.config.create_index(
            index_name,
            self.splunk,
            is_cloud="splunkcloud.com" in self.config.host.lower(),
            acs_stack=self.config.acs_stack,
            acs_server=self.config.acs_server,
            splunk_token=self.config.splunk_token,
        )

    def search_probe(
        self,
        probe_spl: str,
        *,
        verify_fn: Optional[Callable[[SearchState], bool]] = None,
        timeout: int = 300,
        interval: int = 5,
        probe_name: Optional[str] = "probe",
    ) -> Generator[int, None, Optional[SearchState]]:
        """
        Probe state by search until it returns verify function return true.
        Default verify function checks for non empty search result
        @param probe_spl: Splunk search query to execure for each check iteration
        @param verify_fn: function to verify search state
        @param timeout: how long in seconds to wait for positive result
        @param interval: interval to repeat search
        @return: SearchState object
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
                    f"{probe_name} has successfully finished after {time.time()-start_time} seconds"
                )
                return search_state
            logger.debug(
                f"{probe_name} is negatve after {time.time()-start_time} seconds"
            )
            yield interval

        logger.error(f"{probe_name} is still negative after {timeout} seconds")

    def repeat_search_until(
        self,
        spl,
        *,
        confition_fn: Optional[Callable[[SearchState], bool]] = None,
        timeout: int = 300,
        interval: int = 5,
    ) -> Optional[SearchState]:
        """
        Reapeats search untill confition function returns True.
        Default confition function checks for non empty search result
        @param spl: Splunk search query to execure
        @param confition_fn: function to verify search state to stop search iterations
        @param timeout: how long in seconds to wait for positive result of condition function
        @param interval: interval to repeat search if condition function is negative
        @return: SearchState object
        """

        it = self.search_probe(
            probe_spl=spl,
            verify_fn=confition_fn,
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
