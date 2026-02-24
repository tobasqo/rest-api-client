from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from json import JSONDecodeError
from typing import TYPE_CHECKING, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from rest_api_client.exc import (
    RestApiInvalidResultSchemaException,
    RestApiInvalidJsonException,
    RestApiBadRequestException,
)
from rest_api_client.types import HttpMethod

if TYPE_CHECKING:
    from typing import Any, NoReturn
    from httpx import Client, Response
    from httpx._types import RequestData, RequestFiles, HeaderTypes, QueryParamTypes

TResultModel = TypeVar("TResultModel", bound=BaseModel)
TListResultModel = TypeVar("TListResultModel", bound=BaseModel)
TQueryParams = TypeVar("TQueryParams", bound=BaseModel | None)
TInputModel = TypeVar("TInputModel", bound=BaseModel)

ResourceId = int | str


class BaseRoute(ABC):
    path: str

    def __init__(self, session: Client, logger: logging.Logger | None = None) -> None:
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
    ) -> Response:
        self._logger.info("%s %s", method, path)
        return self._session.request(
            method,
            path,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
        )


class GenericRoute(BaseRoute, Generic[TResultModel]):
    def _raise_invalid_schema(
        self,
        response_data: Any,
        exc: BaseException,
        result_model_type: type[TResultModel],
    ) -> NoReturn:
        err_msg = "Received invalid response from server"
        self._logger.error("%s", err_msg)
        raise RestApiInvalidResultSchemaException(
            err_msg, response_data, result_model_type
        ) from exc

    def _make_result_model(
        self, response_data: Any, result_model_type: type[TResultModel]
    ) -> TResultModel:
        try:
            return result_model_type.model_validate(response_data)
        except ValidationError as exc:
            self._raise_invalid_schema(response_data, exc, result_model_type)

    def _parse_response(
        self, response: Response, result_model_type: type[TResultModel]
    ) -> TResultModel:
        if 200 <= response.status_code < 400:
            try:
                response_data = response.json()
            except JSONDecodeError as exc:
                self._logger.error("%s", exc)
                raise RestApiInvalidJsonException(
                    response.text, result_model_type
                ) from exc
            return self._make_result_model(response_data, result_model_type)
        self._logger.error("%d: %s", response.status_code, response.text)
        raise RestApiBadRequestException(response.text, response.status_code)


class RetrieveRoute(GenericRoute[TResultModel]):
    retrieve_result_model_type: type[TResultModel]

    def get(self, resource_id: ResourceId) -> TResultModel:
        path = f"{self.path}/{resource_id}"
        response = self._send_request(HttpMethod.GET, path)
        return self._parse_response(response, self.retrieve_result_model_type)


class ListRoute(BaseRoute, Generic[TListResultModel, TQueryParams]):
    list_result_model_type: type[TListResultModel]

    def get_list(self, params: TQueryParams | None = None) -> TListResultModel:
        params_dict = None if params is None else params.model_dump(exclude_unset=True)
        response = self._send_request(HttpMethod.GET, self.path, params=params_dict)
        return self._parse_response_list_result(response)

    @abstractmethod
    def _validate_list_result_model(self, response_data: Any) -> TListResultModel:
        pass

    def _raise_invalid_list_result_schema(
        self,
        response_data: Any,
        exc: Exception,
    ) -> NoReturn:
        err_msg = "Received invalid response from server"
        self._logger.error("%s", err_msg)
        raise RestApiInvalidResultSchemaException(
            err_msg, response_data, self.list_result_model_type
        ) from exc

    def _make_list_result_model(self, response_data: Any) -> TListResultModel:
        try:
            return self._validate_list_result_model(response_data)
        except ValidationError as exc:
            self._raise_invalid_list_result_schema(response_data, exc)

    def _parse_response_list_result(self, response: Response) -> TListResultModel:
        if 200 <= response.status_code < 400:
            try:
                response_data = response.json()
            except JSONDecodeError as exc:
                self._logger.error("%s", exc)
                raise RestApiInvalidJsonException(
                    response.text, self.list_result_model_type
                ) from exc
            return self._make_list_result_model(response_data)
        self._logger.error("%d: %s", response.status_code, response.text)
        raise RestApiBadRequestException(response.text, response.status_code)


class SaveRoute(GenericRoute[TResultModel], Generic[TResultModel, TInputModel]):
    @staticmethod
    def _make_request_data(model: TInputModel) -> Any:
        return model.model_dump(exclude_unset=True)


class CreateRoute(
    SaveRoute[TResultModel, TInputModel], Generic[TResultModel, TInputModel]
):
    create_result_model_type: type[TResultModel]

    def create(self, model: TInputModel) -> TResultModel:
        request_data = self._make_request_data(model)
        response = self._send_request(HttpMethod.POST, self.path, json=request_data)
        return self._parse_response(response, self.create_result_model_type)


class UpdateRoute(
    SaveRoute[TResultModel, TInputModel], Generic[TResultModel, TInputModel]
):
    update_result_model_type: type[TResultModel]

    def update(self, resource_id: ResourceId, model: TInputModel) -> TResultModel:
        path = f"{self.path}/{resource_id}"
        request_data = self._make_request_data(model)
        response = self._send_request(HttpMethod.PUT, path, json=request_data)
        return self._parse_response(response, self.update_result_model_type)


class PartialUpdateRoute(
    SaveRoute[TResultModel, TInputModel], Generic[TResultModel, TInputModel]
):
    partial_update_result_model_type: type[TResultModel]

    def partial_update(
        self, resource_id: ResourceId, model: TInputModel
    ) -> TResultModel:
        path = f"{self.path}/{resource_id}"
        request_data = self._make_request_data(model)
        response = self._send_request(HttpMethod.PATCH, path, json=request_data)
        return self._parse_response(response, self.partial_update_result_model_type)


class DeleteRoute(BaseRoute):
    def delete(self, resource_id: ResourceId) -> None:
        path = f"{self.path}/{resource_id}"
        self._send_request(HttpMethod.DELETE, path)
