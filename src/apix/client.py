from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from httpx import URL, AsyncClient, Auth, Client, Timeout

from apix.utils.urls import parse_url

if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self


class ApixClient:
    def __init__(
        self,
        base_url: str,
        auth: Auth | None = None,
        session: Client | None = None,
        async_session: AsyncClient | None = None,
        timeout: Timeout | float | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__()

        self.base_url = URL(parse_url(base_url))
        self._session = session or Client(auth=auth, timeout=timeout, base_url=self.base_url)
        self._async_session = async_session or AsyncClient(
            auth=auth, timeout=timeout, base_url=self.base_url
        )
        self._logger = logger or logging.getLogger(__name__)

    def close(self) -> None:
        self._session.close()

    async def aclose(self) -> None:
        await self._async_session.aclose()

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

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        await self.aclose()
        return None
