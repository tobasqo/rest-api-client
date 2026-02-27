from __future__ import annotations

import logging
from abc import ABCMeta, abstractmethod
from json import JSONDecodeError
from typing import TYPE_CHECKING, Generic

from httpx import USE_CLIENT_DEFAULT, HTTPStatusError
from httpx._models import Headers
from pydantic import ValidationError

from rest_api_client.exceptions import (
    RestApiHttpError,
    RestApiInvalidJsonError,
    RestApiUnexpectedResponseSchemaError,
)
from rest_api_client.http_methods import HttpMethod
from rest_api_client.routes._models import (
    TInputModel,
    TListResultModel,
    TQueryParams,
    TResultModel,
)
from rest_api_client.status_codes import HttpStatusCode

if TYPE_CHECKING:
    from typing import Any, NoReturn

    from httpx import Client, Response
    from httpx._client import UseClientDefault
    from httpx._types import HeaderTypes, QueryParamTypes, RequestData, RequestFiles


class BaseMixin:
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

    def _check_api_error(self, response: Response) -> None:
        try:
            response.raise_for_status()
        except HTTPStatusError as exception:
            status_code = HttpStatusCode.from_value(response.status_code)
            rest_api_exception = RestApiHttpError(status_code)
            self._logger.exception(
                "%s", response.status_code, exc_info=rest_api_exception
            )
            raise rest_api_exception from exception

    def _get_data_from_response(self, response: Response) -> Any:
        try:
            return response.json()
        except JSONDecodeError as exception:
            rest_api_exception = RestApiInvalidJsonError(response.text)
            self._logger.exception(
                "Received response is not a valid JSON", exc_info=rest_api_exception
            )
            raise rest_api_exception from exception


class GenericMixin(BaseMixin, Generic[TResultModel]):
    def _handle_response(
        self,
        response: Response,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        self._check_api_error(response)
        response_data = self._get_data_from_response(response)
        return self._make_result_model(response_data, result_model_type)

    def _make_result_model(
        self,
        response_data: Any,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        assert result_model_type is not None
        try:
            return result_model_type.model_validate(response_data)
        except ValidationError as exception:
            self._raise_invalid_response_schema(
                response_data, exception, result_model_type
            )

    def _raise_invalid_response_schema(
        self,
        response_data: Any,
        exception: ValidationError,
        result_model_type: type[TResultModel],
    ) -> NoReturn:
        assert result_model_type is not None
        message = "Received unexpected response from server"
        rest_api_exception = RestApiUnexpectedResponseSchemaError(
            message, response_data, result_model_type
        )
        self._logger.exception("%s", message, exc_info=rest_api_exception)
        raise rest_api_exception from exception


class GetMixin(GenericMixin[TResultModel]):
    def _get(self, path: str, result_model_type: type[TResultModel]) -> TResultModel:
        response = self._send_request(HttpMethod.GET, path)
        return self._handle_response(response, result_model_type)


class ListMixin(
    GenericMixin[TListResultModel],
    Generic[TListResultModel, TQueryParams],
    metaclass=ABCMeta,
):
    def _get_list(
        self,
        path: str,
        list_result_model_type: type[TListResultModel],
        params: TQueryParams | None = None,
    ) -> TListResultModel:
        params_dict = None if params is None else params.model_dump(exclude_unset=True)
        response = self._send_request(HttpMethod.GET, path, params=params_dict)
        return self._handle_list_response(response, list_result_model_type)

    @abstractmethod
    def _validate_list_result_model(
        self, response_data: Any, result_model_type: type[TListResultModel]
    ) -> TListResultModel:
        raise NotImplementedError

    def _handle_list_response(
        self,
        response: Response,
        list_result_model_type: type[TListResultModel],
    ) -> TListResultModel:
        self._check_api_error(response)
        response_data = self._get_data_from_response(response)
        return self._make_list_result_model(response_data, list_result_model_type)

    def _make_list_result_model(
        self,
        response_data: Any,
        list_result_model_type: type[TListResultModel],
    ) -> TListResultModel:
        try:
            return self._validate_list_result_model(
                response_data, list_result_model_type
            )
        except ValidationError as exception:
            self._raise_invalid_response_schema(
                response_data, exception, list_result_model_type
            )


class UploadMixin(GenericMixin[TResultModel], Generic[TInputModel, TResultModel]):
    def _upload(
        self,
        method: HttpMethod,
        path: str,
        model: TInputModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        request_data = self._make_request_data(model)
        response = self._send_request(method, path, json=request_data)
        return self._handle_response(response, result_model_type)

    @staticmethod
    def _make_request_data(model: TInputModel) -> Any:
        return model.model_dump(exclude_unset=True)


class PostMixin(UploadMixin[TInputModel, TResultModel]):
    def _post(
        self,
        path: str,
        model: TInputModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return self._upload(HttpMethod.POST, path, model, result_model_type)


class PutMixin(UploadMixin[TInputModel, TResultModel]):
    def _put(
        self,
        path: str,
        model: TInputModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return self._upload(HttpMethod.PUT, path, model, result_model_type)


class PatchMixin(UploadMixin[TInputModel, TResultModel]):
    def _patch(
        self,
        path: str,
        model: TInputModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return self._upload(HttpMethod.PATCH, path, model, result_model_type)


class DeleteMixin(BaseMixin):
    # TODO: allow for optional return type on delete

    def _delete(self, path: str) -> None:
        self._send_request(HttpMethod.DELETE, path)
