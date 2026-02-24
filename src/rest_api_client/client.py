import logging
from abc import ABC
from types import TracebackType

import httpx

from rest_api_client.utils.urls import parse_url


class RestApiClient(ABC):
    def __init__(
        self,
        base_url: str,
        auth: httpx.Auth | None = None,
        session: httpx.Client | None = None,
        timeout: httpx.Timeout | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__()

        self.base_url = parse_url(base_url)
        self.session = session or httpx.Client(
            auth=auth, timeout=timeout, base_url=self.base_url
        )
        self.logger = logger or logging.getLogger(__name__)

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "RestApiClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        self.close()
        return None
