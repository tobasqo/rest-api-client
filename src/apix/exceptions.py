from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel

    from apix.status_codes import HttpStatusCode


class ApixError(Exception):
    pass


class ApixInvalidUrlError(ApixError):
    pass


class ApixInvalidJsonError(ApixError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ApixResponseSchemaError(ApixError):
    def __init__(
        self,
        message: str,
        response_data: Any,
        expected_result_type: type[BaseModel],
    ) -> None:
        super().__init__(message)
        self.response_data = response_data
        self.expected_result_type = expected_result_type


class ApixHttpError(ApixError):
    def __init__(self, status_code: HttpStatusCode) -> None:
        super().__init__(status_code)
        self.status_code = status_code
