from typing import TypeVar

from pydantic import BaseModel

TInputModel = TypeVar("TInputModel", bound=BaseModel)
TResultModel = TypeVar("TResultModel", bound=BaseModel)

TListResultModel = TypeVar("TListResultModel", bound=BaseModel)
TQueryParams = TypeVar("TQueryParams", bound=BaseModel | None)

TCreate = TypeVar("TCreate", bound=BaseModel)
TCreateResult = TypeVar("TCreateResult", bound=BaseModel)

TUpdate = TypeVar("TUpdate", bound=BaseModel)
TUpdateResult = TypeVar("TUpdateResult", bound=BaseModel)

TPartialUpdate = TypeVar("TPartialUpdate", bound=BaseModel)
TPartialUpdateResult = TypeVar("TPartialUpdateResult", bound=BaseModel)
