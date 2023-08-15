from typing import Generic, Optional, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

DataT = TypeVar("DataT")


class BaseResponse(GenericModel, BaseModel, Generic[DataT]):
    code: int
    msg: str = ""
    data: Optional[DataT] = None


class Success(BaseResponse):
    code: int = 200


class Fail(BaseResponse):
    code: int = -1


class SuccessExtra(Success):
    total: int
    page: int
    page_size: int
