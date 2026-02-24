import logging
from abc import ABC
from json import JSONDecodeError
from typing import NoReturn, Any, Generic, TypeVar

import httpx
from httpx import _types
from pydantic import BaseModel, ValidationError

from rest_api_client.exc import (
    RestApiInvalidResultSchemaException,
    RestApiInvalidJsonException,
    RestApiBadRequestException,
)
from rest_api_client.types import HttpMethod

TResultModel = TypeVar('TResultModel', bound=BaseModel)
TQueryParams = TypeVar('TQueryParams', bound=BaseModel | None)
TInputModel = TypeVar('TInputModel', bound=BaseModel)

ResourceId = int | str


class BaseRoute(ABC):
    path: str

    def __init__(self, session: httpx.Client, logger: logging.Logger | None = None) -> None:
        self._session = session
        self._logger = logger or logging.getLogger(__name__)

    def _send_request(
        self,
        method: str,
        path: str,
        data: _types.RequestData | None = None,
        files: _types.RequestFiles | None = None,
        json: Any | None = None,
        params: _types.QueryParamTypes | None = None,
        headers: _types.Headers | None = None,
    ) -> httpx.Response:
        self._logger.info('%d %s', method, path)
        return self._session.request(method, path, data=data, files=files, json=json, params=params, headers=headers)


class GenericRoute(BaseRoute, Generic[TResultModel]):
    result_model_type: type[TResultModel]

    def _raise_invalid_schema(self, response_data: Any, exc: BaseException) -> NoReturn:
        err_msg = 'Received invalid response from server'
        self._logger.error('%s', err_msg)
        raise RestApiInvalidResultSchemaException(err_msg, response_data, self.result_model_type) from exc

    def _make_result_model(self, response_data: Any) -> TResultModel:
        try:
            return self.result_model_type.model_validate(response_data)
        except ValidationError as exc:
            self._raise_invalid_schema(response_data, exc)

    def _parse_response(self, response: httpx.Response) -> TResultModel:
        if 200 <= response.status_code < 400:
            try:
                response_data = response.json()
            except JSONDecodeError as exc:
                self._logger.error('%s', exc)
                raise RestApiInvalidJsonException(response.text, self.result_model_type) from exc
            return self._make_result_model(response_data)
        self._logger.error('%d: %s', response.status_code, response.text)
        raise RestApiBadRequestException(response.text, response.status_code)


class RetrieveRoute(GenericRoute[TResultModel]):
    def get(self, resource_id: ResourceId) -> TResultModel:
        path = f'{self.path}/{resource_id}'
        response = self._send_request(HttpMethod.GET, path)
        return self._parse_response(response)


class ListRoute(GenericRoute[TResultModel], Generic[TResultModel, TQueryParams]):
    def get_list(self, params: TQueryParams | None = None) -> TResultModel:
        params_dict = None if params is None else params.model_dump(exclude_unset=True)
        response = self._send_request(HttpMethod.GET, self.path, params=params_dict)
        return self._parse_response(response)


class SaveRoute(GenericRoute[TResultModel], Generic[TResultModel, TInputModel]):
    @staticmethod
    def _make_request_data(model: TInputModel) -> Any:
        return model.model_dump(exclude_unset=True)


class CreateRoute(SaveRoute[TResultModel, TInputModel]):
    def create(self, model: TInputModel) -> TResultModel:
        request_data = self._make_request_data(model)
        response = self._send_request(HttpMethod.POST, self.path, json=request_data)
        return self._parse_response(response)


class UpdateRoute(SaveRoute[TResultModel, TInputModel]):
    def update(self, resource_id: ResourceId, model: TInputModel) -> TResultModel:
        path = f'{self.path}/{resource_id}'
        request_data = self._make_request_data(model)
        response = self._send_request(HttpMethod.PUT, path, json=request_data)
        return self._parse_response(response)


class PartialUpdateRoute(SaveRoute[TResultModel, TInputModel]):
    def partial_update(self, resource_id: ResourceId, model: TInputModel) -> TResultModel:
        path = f'{self.path}/{resource_id}'
        request_data = self._make_request_data(model)
        response = self._send_request(HttpMethod.PATCH, path, json=request_data)
        return self._parse_response(response)


class DeleteRoute(BaseRoute):
    def delete(self, resource_id: ResourceId) -> None:
        path = f'{self.path}/{resource_id}'
        self._send_request(HttpMethod.DELETE, path)
