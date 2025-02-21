from splunklib import client
from threading import Lock
from typing import Any, Union
from splunk_add_on_ucc_modinput_test.common.utils import logger


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
        self._pool: list[SplunkServiceProxy] = []
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
