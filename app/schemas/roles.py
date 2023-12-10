from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseRole(BaseModel):
    id: int
    name: str
    desc: str = ""
    users: Optional[list] = []
    menus: Optional[list] = []
    apis: Optional[list] = []
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class RoleCreate(BaseModel):
    name: str = Field(example="管理员")
    desc: str = Field("", example="管理员角色")


class RoleUpdate(BaseModel):
    id: int = Field(example=1)
    name: str = Field(example="管理员")
    desc: str = Field("", example="管理员角色")

    def update_dict(self):
        return self.model_dump(exclude_unset=True, exclude={"id"})


class RoleUpdateMenusApis(BaseModel):
    id: int
    menu_ids: list[int] = []
    api_infos: list[dict] = []
