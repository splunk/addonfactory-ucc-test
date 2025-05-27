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
from splunklib import client
from threading import Lock
from typing import Any, Union, List
import logging

logger = logging.getLogger("ucc-modinput-test")


class SplunkServiceProxy:
    def __init__(
        self, host: str, port: Union[int, str], username: str, password: str
    ) -> None:
        self._lock = Lock()
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self.__connect()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._service, name)

    def __connect(self) -> None:
        with self._lock:
            self._service = client.connect(
                host=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
            )


class SplunkServicePool:
    def __init__(
        self,
        host: str,
        port: Union[int, str],
        username: str,
        password: str,
        *,
        pool_initial_size: int = 3,
        pool_size_inc: int = 2,
    ) -> None:
        logger.debug(f"SplunkServicePool init {username}@{host}:{port}")

        self._lock = Lock()
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._pool_initial_size = pool_initial_size
        self._pool_size_inc = pool_size_inc
        self._pool: List[SplunkServiceProxy] = []
        self.__increase_pool(self._pool_initial_size)

    def __increase_pool(self, increment_size: int) -> None:
        with self._lock:
            for _ in range(increment_size):
                self._pool.append(
                    SplunkServiceProxy(
                        self._host, self._port, self._username, self._password
                    )
                )
        logger.debug(f"SplunkServicePool has been sized to {len(self._pool)}")

    def __getattr__(self, name: str) -> Any:
        while True:
            for svc in self._pool:
                locked = svc._lock.acquire(False)
                if locked:
                    try:
                        return getattr(svc, name)
                    finally:
                        svc._lock.release()

            self.__increase_pool(self._pool_size_inc)
        return None
