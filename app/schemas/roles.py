from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .base import BaseResponse, SuccessExtra


class BaseRole(BaseModel):
    id: int
    name: str
    desc: Optional[str]
    users: Optional[list]
    menus: Optional[list]
    apis: Optional[list]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class RoleCreate(BaseModel):
    name: str = Field(example="管理员")
    desc: Optional[str] = Field(example="管理员角色")


class RoleUpdate(BaseModel):
    id: int = Field(example=1)
    name: Optional[str] = Field(example="管理员")
    desc: Optional[str] = Field(example="管理员角色")

    def update_dict(self):
        return self.dict(exclude_unset=True, exclude={"id"})


class RoleUpdateMenusApis(BaseModel):
    id: int
    menu_ids: List[int] = []
    api_infos: List[dict] = []


"""Response"""


class RoleOutList(SuccessExtra):
    data: Optional[List[BaseRole]]


class RoleOut(BaseResponse):
    data: Optional[BaseRole]
