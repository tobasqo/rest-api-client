from typing import TypeVar

from pydantic import BaseModel

TInputModel = TypeVar("TInputModel", bound=BaseModel)
TResultModel = TypeVar("TResultModel", bound=BaseModel)

TListResultModel = TypeVar("TListResultModel", bound=BaseModel)
TQueryParams = TypeVar("TQueryParams", bound=BaseModel | None)

TCreateModel = TypeVar("TCreateModel", bound=BaseModel)
TCreateResultModel = TypeVar("TCreateResultModel", bound=BaseModel)

TUpdateModel = TypeVar("TUpdateModel", bound=BaseModel)
TUpdateResultModel = TypeVar("TUpdateResultModel", bound=BaseModel)

TPartialUpdateModel = TypeVar("TPartialUpdateModel", bound=BaseModel)
TPartialUpdateResultModel = TypeVar("TPartialUpdateResultModel", bound=BaseModel)
