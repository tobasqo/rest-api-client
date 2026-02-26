from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from json import JSONDecodeError
from typing import TYPE_CHECKING, Generic, TypeVar

from httpx import USE_CLIENT_DEFAULT
from httpx._models import Headers
from pydantic import BaseModel, ValidationError

from rest_api_client.exceptions import (
    RestApiBadRequestError,
    RestApiError,
    RestApiInvalidJsonError,
    RestApiInvalidResultSchemaError,
)
from rest_api_client.types import HttpMethod

if TYPE_CHECKING:
    from typing import Any, NoReturn

    from httpx import Client, Response
    from httpx._client import UseClientDefault
    from httpx._types import HeaderTypes, QueryParamTypes, RequestData, RequestFiles

TResultModel = TypeVar("TResultModel", bound=BaseModel)
TListResultModel = TypeVar("TListResultModel", bound=BaseModel)
TQueryParams = TypeVar("TQueryParams", bound=BaseModel | None)
TInputModel = TypeVar("TInputModel", bound=BaseModel)

ResourceId = int | str

# TODO: remove
MIN_OK_STATUS_CODE = 200
MAX_OK_STATUS_CODE = 399

# TODO: split routes into mixins and commons


class BaseRoute:
    def __init__(self, session: Client, logger: logging.Logger | None = None) -> None:
        super().__init__()
        self._session = session
        self._logger = logger or logging.getLogger(__name__)

    def _send_request(
        self,
        method: str,
        path: str,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        **kwargs,
    ) -> Response:
        self._logger.info("%s %s", method, path)
        _headers = self._get_default_headers()
        _headers.update(headers)
        return self._session.request(
            method,
            path,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=_headers,
            follow_redirects=follow_redirects,
            **kwargs,
        )

    # noinspection PyMethodMayBeStatic
    def _get_default_headers(self) -> Headers:
        # TODO: update
        return Headers(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )


class GenericRoute(BaseRoute, Generic[TResultModel]):
    def _raise_invalid_schema(
        self,
        response_data: Any,
        exception: ValidationError,
        result_model_type: type[TResultModel],
    ) -> NoReturn:
        message = "Received unexpected response from server"
        rest_api_exception = RestApiInvalidResultSchemaError(
            message, response_data, result_model_type
        )
        self._logger.exception("%s", message, exc_info=rest_api_exception)
        raise rest_api_exception from exception

    def _make_result_model(
        self,
        response_data: Any,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        try:
            return result_model_type.model_validate(response_data)
        except ValidationError as exception:
            self._raise_invalid_schema(response_data, exception, result_model_type)

    def _parse_response(
        self,
        response: Response,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        # TODO: mapping for more specific errors
        response.raise_for_status()
        if MIN_OK_STATUS_CODE <= response.status_code < MAX_OK_STATUS_CODE:
            try:
                response_data = response.json()
            except JSONDecodeError as exception:
                rest_api_exception: RestApiError = RestApiInvalidJsonError(
                    response.text, result_model_type
                )
                self._logger.exception(
                    "Received response is not a valid JSON", exc_info=rest_api_exception
                )
                raise rest_api_exception from exception
            return self._make_result_model(response_data, result_model_type)
        rest_api_exception = RestApiBadRequestError(response.text, response.status_code)
        self._logger.exception(
            "%d: %s", response.status_code, response.text, exc_info=rest_api_exception
        )
        raise rest_api_exception


class RetrieveRoute(GenericRoute[TResultModel]):
    def _get(
        self,
        path: str,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        response = self._send_request(HttpMethod.GET, path)
        return self._parse_response(response, result_model_type)

    def _get_by_id(
        self,
        path: str,
        resource_id: ResourceId,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return self._get(f"{path}/{resource_id}", result_model_type)


class ListRoute(ABC, BaseRoute, Generic[TListResultModel, TQueryParams]):
    def _get_list(
        self,
        path: str,
        list_result_model_type: type[TListResultModel],
        params: TQueryParams | None = None,
    ) -> TListResultModel:
        params_dict = None if params is None else params.model_dump(exclude_unset=True)
        response = self._send_request(HttpMethod.GET, path, params=params_dict)
        return self._parse_response_list_result(response, list_result_model_type)

    @abstractmethod
    def _validate_list_result_model(self, response_data: Any) -> TListResultModel:
        pass

    def _raise_invalid_list_result_schema(
        self,
        response_data: Any,
        exception: ValidationError,
        list_result_model_type: type[TListResultModel],
    ) -> NoReturn:
        message = "Received unexpected response from server"
        rest_api_exception = RestApiInvalidResultSchemaError(
            message, response_data, list_result_model_type
        )
        self._logger.exception("%s", message, exc_info=rest_api_exception)
        raise rest_api_exception from exception

    def _make_list_result_model(
        self,
        response_data: Any,
        list_result_model_type: type[TListResultModel],
    ) -> TListResultModel:
        try:
            return self._validate_list_result_model(response_data)
        except ValidationError as exception:
            self._raise_invalid_list_result_schema(
                response_data, exception, list_result_model_type
            )

    def _parse_response_list_result(
        self,
        response: Response,
        list_result_model_type: type[TListResultModel],
    ) -> TListResultModel:
        # TODO: mapping for more specific errors
        if MIN_OK_STATUS_CODE <= response.status_code < MAX_OK_STATUS_CODE:
            try:
                response_data = response.json()
            except JSONDecodeError as exception:
                rest_api_exception: RestApiError = RestApiInvalidJsonError(
                    response.text, list_result_model_type
                )
                self._logger.exception(
                    "Received response is not a valid JSON", exc_info=rest_api_exception
                )
                raise rest_api_exception from exception
            return self._make_list_result_model(response_data, list_result_model_type)
        rest_api_exception = RestApiBadRequestError(response.text, response.status_code)
        self._logger.exception(
            "%d: %s", response.status_code, response.text, exc_info=rest_api_exception
        )
        raise rest_api_exception


class SaveRoute(GenericRoute[TResultModel], Generic[TInputModel, TResultModel]):
    @staticmethod
    def _make_request_data(model: TInputModel) -> Any:
        return model.model_dump(exclude_unset=True)

    def _upload(
        self,
        method: HttpMethod,
        path: str,
        model: TInputModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        request_data = self._make_request_data(model)
        response = self._send_request(method, path, json=request_data)
        return self._parse_response(response, result_model_type)


class CreateRoute(SaveRoute[TInputModel, TResultModel]):
    def _create(
        self,
        path: str,
        model: TInputModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return self._upload(HttpMethod.POST, path, model, result_model_type)


class UpdateRoute(SaveRoute[TInputModel, TResultModel]):
    def _update(
        self,
        path: str,
        model: TInputModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return self._upload(HttpMethod.PUT, path, model, result_model_type)

    def _update_by_id(
        self,
        path: str,
        resource_id: ResourceId,
        model: TInputModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return self._update(f"{path}/{resource_id}", model, result_model_type)


class PartialUpdateRoute(SaveRoute[TInputModel, TResultModel]):
    def _partial_update(
        self,
        path: str,
        model: TInputModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return self._upload(HttpMethod.PATCH, path, model, result_model_type)

    def _partial_update_by_id(
        self,
        path: str,
        resource_id: ResourceId,
        model: TInputModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return self._partial_update(f"{path}/{resource_id}", model, result_model_type)


class DeleteRoute(BaseRoute):
    # TODO: allow for optional return type on delete

    def _delete(self, path: str) -> None:
        self._send_request(HttpMethod.DELETE, path)

    def _delete_by_id(self, path: str, resource_id: ResourceId) -> None:
        return self._delete(f"{path}/{resource_id}")
