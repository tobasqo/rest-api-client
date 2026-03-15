from __future__ import annotations

import logging
from json import JSONDecodeError
from typing import TYPE_CHECKING, Generic

from httpx import USE_CLIENT_DEFAULT, AsyncClient, HTTPStatusError
from httpx._models import Headers
from pydantic import BaseModel, ValidationError

from rest_api_client.exceptions import (
    RestApiHttpError,
    RestApiInvalidJsonError,
    RestApiUnexpectedResponseSchemaError,
)
from rest_api_client.http_methods import HttpMethod
from rest_api_client.routes._models import TListResultModel
from rest_api_client.status_codes import HttpStatusCode

if TYPE_CHECKING:
    from typing import Any, NoReturn

    from httpx import Client, Response
    from httpx._client import UseClientDefault
    from httpx._types import HeaderTypes, QueryParamTypes, RequestData, RequestFiles

    from rest_api_client.routes._models import TResultModel

"""
TODOs:
- request/response streaming
"""


class BaseMixin:
    def __init__(
        self,
        session: Client,
        async_session: AsyncClient,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__()
        self._session = session
        self._async_session = async_session
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

    async def _async_send_request(
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
        return await self._async_session.request(
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
        except HTTPStatusError as exc:
            status_code = HttpStatusCode.from_value(response.status_code)
            self._logger.exception("%d - %s", response.status_code, response.text)
            raise RestApiHttpError(status_code) from exc

    def _get_data_from_response(self, response: Response) -> Any:
        try:
            return response.json()
        except JSONDecodeError as exc:
            self._logger.exception("Received response is not a valid JSON")
            raise RestApiInvalidJsonError(response.text) from exc


class ResultMixin(BaseMixin):
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
        try:
            return result_model_type.model_validate(response_data)
        except ValidationError as exc:
            self._raise_invalid_response_schema(response_data, exc, result_model_type)

    def _raise_invalid_response_schema(
        self,
        response_data: Any,
        exc: ValidationError,
        result_model_type: type[BaseModel],
    ) -> NoReturn:
        message = "Received unexpected response from server"
        _exc = RestApiUnexpectedResponseSchemaError(message, response_data, result_model_type)
        self._logger.exception("%s", message, exc_info=_exc)
        raise _exc from exc


class GetMixin(ResultMixin):
    def _get(self, path: str, result_model_type: type[TResultModel]) -> TResultModel:
        response = self._send_request(HttpMethod.GET.value, path)
        return self._handle_response(response, result_model_type)

    async def _async_get(self, path: str, result_model_type: type[TResultModel]) -> TResultModel:
        response = await self._async_send_request(HttpMethod.GET.value, path)
        return self._handle_response(response, result_model_type)


class ListMixin(ResultMixin, Generic[TListResultModel]):
    def _get_list(
        self,
        path: str,
        list_result_model_type: type[TListResultModel],
        params: BaseModel | None = None,
    ) -> TListResultModel:
        params_dict = self._make_query_params(params)
        response = self._send_request(HttpMethod.GET.value, path, params=params_dict)
        return self._handle_list_response(response, list_result_model_type)

    async def _async_get_list(
        self,
        path: str,
        list_result_model_type: type[TListResultModel],
        params: BaseModel | None = None,
    ) -> TListResultModel:
        params_dict = self._make_query_params(params)
        response = await self._async_send_request(HttpMethod.GET.value, path, params=params_dict)
        return self._handle_list_response(response, list_result_model_type)

    def _validate_list_result_model(
        self,
        response_data: Any,
        result_model_type: type[TListResultModel],
    ) -> TListResultModel:
        return result_model_type.model_validate(response_data)

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
            return self._validate_list_result_model(response_data, list_result_model_type)
        except ValidationError as exc:
            self._raise_invalid_response_schema(response_data, exc, list_result_model_type)

    def _make_query_params(self, params: BaseModel | None) -> dict[str, Any]:
        if params is None:
            return {}
        return params.model_dump(mode="json", exclude_unset=True, by_alias=True)


class UploadMixin(ResultMixin):
    def _upload(
        self,
        method: HttpMethod,
        path: str,
        model: BaseModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        request_data = self._make_request_data(model)
        response = self._send_request(method.value, path, json=request_data)
        return self._handle_response(response, result_model_type)

    async def _async_upload(
        self,
        method: HttpMethod,
        path: str,
        model: BaseModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        request_data = self._make_request_data(model)
        response = await self._async_send_request(method.value, path, json=request_data)
        return self._handle_response(response, result_model_type)

    @staticmethod
    def _make_request_data(model: BaseModel) -> Any:
        return model.model_dump(mode="json", exclude_unset=True, by_alias=True)


class PostMixin(UploadMixin):
    def _post(
        self,
        path: str,
        model: BaseModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return self._upload(HttpMethod.POST, path, model, result_model_type)

    async def _async_post(
        self,
        path: str,
        model: BaseModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return await self._async_upload(HttpMethod.POST, path, model, result_model_type)


class PutMixin(UploadMixin):
    def _put(
        self,
        path: str,
        model: BaseModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return self._upload(HttpMethod.PUT, path, model, result_model_type)

    async def _async_put(
        self,
        path: str,
        model: BaseModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return await self._async_upload(HttpMethod.PUT, path, model, result_model_type)


class PatchMixin(UploadMixin):
    def _patch(
        self,
        path: str,
        model: BaseModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return self._upload(HttpMethod.PATCH, path, model, result_model_type)

    async def _async_patch(
        self,
        path: str,
        model: BaseModel,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        return await self._async_upload(HttpMethod.PATCH, path, model, result_model_type)


class DeleteMixin(BaseMixin):
    # TODO: allow for optional return type on delete

    def _delete(self, path: str) -> None:
        response = self._send_request(HttpMethod.DELETE.value, path)
        self._check_api_error(response)

    async def _async_delete(self, path: str) -> None:
        response = await self._async_send_request(HttpMethod.DELETE.value, path)
        self._check_api_error(response)
