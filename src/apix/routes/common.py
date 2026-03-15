from abc import ABCMeta
from typing import Generic

from apix.routes._models import (
    TCreateModel,
    TCreateResultModel,
    TListResultModel,
    TPartialUpdateModel,
    TPartialUpdateResultModel,
    TQueryParams,
    TResultModel,
    TUpdateModel,
    TUpdateResultModel,
)
from apix.routes.mixins import (
    DeleteMixin,
    GetMixin,
    ListMixin,
    PatchMixin,
    PostMixin,
    PutMixin,
)

ResourceId = int | str


class _BaseRoute:
    path: str


class RetrieveRoute(GetMixin, _BaseRoute, Generic[TResultModel]):
    _get_result_model_type: type[TResultModel]

    def get(self, resource_id: ResourceId) -> TResultModel:
        return self._get(f"{self.path}/{resource_id}", self._get_result_model_type)

    async def async_get(self, resource_id: ResourceId) -> TResultModel:
        return await self._async_get(f"{self.path}/{resource_id}", self._get_result_model_type)


class ListRoute(
    ListMixin,
    _BaseRoute,
    Generic[TListResultModel, TQueryParams],
    metaclass=ABCMeta,
):
    _get_list_result_model_type: type[TListResultModel]

    def get_list(self, params: TQueryParams | None = None) -> TListResultModel:
        return self._get_list(self.path, self._get_list_result_model_type, params)

    async def async_get_list(self, params: TQueryParams | None = None) -> TListResultModel:
        return await self._async_get_list(self.path, self._get_list_result_model_type, params)


class CreateRoute(PostMixin, _BaseRoute, Generic[TCreateModel, TCreateResultModel]):
    _create_result_model_type: type[TCreateResultModel]

    def create(self, model: TCreateModel) -> TCreateResultModel:
        return self._post(self.path, model, self._create_result_model_type)

    async def async_create(self, model: TCreateModel) -> TCreateResultModel:
        return await self._async_post(self.path, model, self._create_result_model_type)


class UpdateRoute(PutMixin, _BaseRoute, Generic[TUpdateModel, TUpdateResultModel]):
    _update_result_model_type: type[TUpdateResultModel]

    def update(
        self,
        resource_id: ResourceId,
        model: TUpdateModel,
    ) -> TUpdateResultModel:
        return self._put(f"{self.path}/{resource_id}", model, self._update_result_model_type)

    async def async_update(
        self,
        resource_id: ResourceId,
        model: TUpdateModel,
    ) -> TUpdateResultModel:
        return await self._async_put(
            f"{self.path}/{resource_id}", model, self._update_result_model_type
        )


class PartialUpdateRoute(
    PatchMixin,
    _BaseRoute,
    Generic[TPartialUpdateModel, TPartialUpdateResultModel],
):
    _partial_update_result_model_type: type[TPartialUpdateResultModel]

    def partial_update(
        self,
        resource_id: ResourceId,
        model: TPartialUpdateModel,
    ) -> TPartialUpdateResultModel:
        return self._patch(
            f"{self.path}/{resource_id}", model, self._partial_update_result_model_type
        )

    async def async_partial_update(
        self,
        resource_id: ResourceId,
        model: TPartialUpdateModel,
    ) -> TPartialUpdateResultModel:
        return await self._async_patch(
            f"{self.path}/{resource_id}", model, self._partial_update_result_model_type
        )


class DeleteRoute(DeleteMixin, _BaseRoute):
    def delete(self, resource_id: ResourceId) -> None:
        return self._delete(f"{self.path}/{resource_id}")

    async def async_delete(self, resource_id: ResourceId) -> None:
        return await self._async_delete(f"{self.path}/{resource_id}")


class FullApiRoutes(
    RetrieveRoute[TResultModel],
    ListRoute[TListResultModel, TQueryParams],
    CreateRoute[TCreateModel, TCreateResultModel],
    UpdateRoute[TUpdateModel, TUpdateResultModel],
    PartialUpdateRoute[TPartialUpdateModel, TPartialUpdateResultModel],
    DeleteRoute,
    Generic[
        TResultModel,
        TListResultModel,
        TQueryParams,
        TCreateModel,
        TCreateResultModel,
        TUpdateModel,
        TUpdateResultModel,
        TPartialUpdateModel,
        TPartialUpdateResultModel,
    ],
    metaclass=ABCMeta,
):
    pass
