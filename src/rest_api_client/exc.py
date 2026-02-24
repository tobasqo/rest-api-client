from typing import Any

from pydantic import BaseModel


class RestApiException(Exception):
    pass


class RestApiInvalidUrlException(RestApiException):
    def __init__(self, url: str) -> None:
        super().__init__(url)

        self.message = url


class RestApiInvalidResultSchemaException(RestApiException):
    def __init__(self, msg: str, response_data: Any, expected_result_type: BaseModel) -> None:
        super().__init__(msg, response_data, expected_result_type)

        self.message = msg
        self.response_data = response_data
        self.expected_result_type = expected_result_type


class RestApiInvalidJsonException(RestApiException):
    def __init__(self, msg: str, expected_result_type: BaseModel) -> None:
        super().__init__(msg, expected_result_type)
        
        self.message = msg
        self.expected_result_type = expected_result_type


class RestApiBadRequestException(RestApiException):
    def __init__(self, msg: str, status_code: int) -> None:
        super().__init__(msg, status_code)

        self.message = msg
        self.status_code = status_code
