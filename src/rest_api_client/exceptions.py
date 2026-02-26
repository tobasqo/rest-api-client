from typing import Any

from pydantic import BaseModel


class RestApiError(Exception):
    pass


class RestApiInvalidUrlError(RestApiError):
    def __init__(self, url: str) -> None:
        super().__init__(url)
        self.message = url


class RestApiInvalidResultSchemaError(RestApiError):
    def __init__(
        self, msg: str, response_data: Any, expected_result_type: type[BaseModel]
    ) -> None:
        super().__init__(msg, response_data, expected_result_type)
        self.message = msg
        self.response_data = response_data
        self.expected_result_type = expected_result_type


class RestApiInvalidJsonError(RestApiError):
    def __init__(self, msg: str, expected_result_type: type[BaseModel]) -> None:
        super().__init__(msg, expected_result_type)
        self.message = msg
        self.expected_result_type = expected_result_type


class RestApiBadRequestError(RestApiError):
    def __init__(self, msg: str, status_code: int) -> None:
        super().__init__(msg, status_code)
        self.message = msg
        self.status_code = status_code
