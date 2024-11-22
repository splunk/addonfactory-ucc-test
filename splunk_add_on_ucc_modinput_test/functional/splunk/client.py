from typing import List, Optional, Tuple
from splunk_add_on_ucc_modinput_test.common.splunk_instance import search, Configuration, SearchState
from splunk_add_on_ucc_modinput_test.common.utils import logger

class SplunkClientBase:
    def __init__(self, splunk_configuration:Optional[Configuration]=None) -> None:
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
    def config(self): # short alias for splunk_configuration 
        return self._splunk_configuration

    @property
    def splunk(self):
        return self._splunk_configuration.service

    @property
    def ta_api(self):
        assert self.ta_service is not None, "Make sure you have decorated inherited client class with @register_splunk_class"
        return self.ta_service.api_instance

    def search(self, searchquery:str) -> SearchState:
        return search(service=self.splunk, searchquery=searchquery)

    def run_saved_search(self, saved_search_name:str) -> Tuple[int, Optional[List[object]]]:
        saved_search = self.splunk.saved_searches[
            saved_search_name
        ]
        state = search(
            service=self.splunk,
            searchquery=saved_search.content["search"],
        )
        logger.debug(
            f"Executed saved search {saved_search_name}, count: {state.result_count}, query: {saved_search.content['search']}"
        )
        return state.result_count, state.results
