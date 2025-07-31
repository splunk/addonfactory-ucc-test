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
import json
import logging
from dataclasses import dataclass

from splunklib.client import Endpoint
from splunklib.binding import ResponseReader

from splunk_add_on_ucc_modinput_test.common.splunk_service_pool import (
    SplunkServicePool,
)

logger = logging.getLogger("ucc-modinput-test")


@dataclass
class SplunkInstanceKVStoreAPI:
    """
    This class provides an interface to interact with the Splunk KV store.
    """

    splunk: SplunkServicePool
    collection_name: str
    record_id: str
    app_name: str
    app_user: str = "nobody"

    def _create_record_path(self) -> str:
        return (
            f"/servicesNS/{self.app_user}/{self.app_name}/storage/"
            f"collections/data/{self.collection_name}/{self.record_id}"
        )

    def get_record_from_collection(self) -> dict[str, str]:
        try:
            record_path = self._create_record_path()
            kvstore_endpoint = Endpoint(self.splunk, record_path)
            response = kvstore_endpoint.get()
            response_body = ResponseReader(response["body"]).read()
            return json.loads(response_body.decode("utf-8"))
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to decode JSON response for KV store record"
                f" {self.record_id} in collection {self.collection_name}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Failed to get KV store record {self.record_id} from "
                f"collection {self.collection_name}: {e}"
            )
            raise
