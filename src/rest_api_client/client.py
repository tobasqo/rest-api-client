from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from httpx import Auth, Client, Timeout

from rest_api_client.utils.urls import parse_url

if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self


class RestApiClient:
    def __init__(
        self,
        base_url: str,
        auth: Auth | None = None,
        session: Client | None = None,
        timeout: Timeout | float | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__()

        self.base_url = parse_url(base_url)
        self._session = session or Client(
            auth=auth, timeout=timeout, base_url=self.base_url
        )
        self._logger = logger or logging.getLogger(__name__)

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        self.close()
        return None
