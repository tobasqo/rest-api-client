from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from json import JSONDecodeError
from typing import TYPE_CHECKING, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from rest_api_client.exc import (
    RestApiBadRequestException,
    RestApiInvalidJsonException,
    RestApiInvalidResultSchemaException,
)
from rest_api_client.types import HttpMethod

if TYPE_CHECKING:
    from typing import Any, NoReturn

    from httpx import Client, Response
    from httpx._types import HeaderTypes, QueryParamTypes, RequestData, RequestFiles

TResultModel = TypeVar("TResultModel", bound=BaseModel)
TListResultModel = TypeVar("TListResultModel", bound=BaseModel)
TQueryParams = TypeVar("TQueryParams", bound=BaseModel | None)
TInputModel = TypeVar("TInputModel", bound=BaseModel)

ResourceId = int | str


# TODO: split routes into mixins and commons


class BaseRoute(ABC):
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
        self,
        response_data: Any,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        try:
            return result_model_type.model_validate(response_data)
        except ValidationError as exc:
            self._raise_invalid_schema(response_data, exc, result_model_type)

    def _parse_response(
        self,
        response: Response,
        result_model_type: type[TResultModel],
    ) -> TResultModel:
        # TODO: dict for more specific errors
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


class ListRoute(BaseRoute, Generic[TListResultModel, TQueryParams]):
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
        exc: Exception,
        list_result_model_type: type[TListResultModel],
    ) -> NoReturn:
        err_msg = "Received invalid response from server"
        self._logger.error("%s", err_msg)
        raise RestApiInvalidResultSchemaException(
            err_msg, response_data, list_result_model_type
        ) from exc

    def _make_list_result_model(
        self,
        response_data: Any,
        list_result_model_type: type[TListResultModel],
    ) -> TListResultModel:
        try:
            return self._validate_list_result_model(response_data)
        except ValidationError as exc:
            self._raise_invalid_list_result_schema(
                response_data, exc, list_result_model_type
            )

    def _parse_response_list_result(
        self,
        response: Response,
        list_result_model_type: type[TListResultModel],
    ) -> TListResultModel:
        # TODO: dict for more specific errors
        if 200 <= response.status_code < 400:
            try:
                response_data = response.json()
            except JSONDecodeError as exc:
                self._logger.error("%s", exc)
                raise RestApiInvalidJsonException(
                    response.text, list_result_model_type
                ) from exc
            return self._make_list_result_model(response_data, list_result_model_type)
        self._logger.error("%d: %s", response.status_code, response.text)
        raise RestApiBadRequestException(response.text, response.status_code)


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
