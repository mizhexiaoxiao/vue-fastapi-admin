from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class BaseUser(BaseModel):
    id: int
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    roles: Optional[list] = []


class UserCreate(BaseModel):
    email: EmailStr = Field(example="admin@qq.com")
    username: str = Field(example="admin")
    password: str = Field(example="123456")
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    roles: Optional[List[int]] = []

    def create_dict(self):
        return self.model_dump(exclude_unset=True, exclude={"roles"})


class UserUpdate(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    roles: Optional[List[int]] = []

    def update_dict(self):
        return self.model_dump(exclude_unset=True, exclude={"roles", "id"})


class UpdatePassword(BaseModel):
    id: int = Field(description="用户ID")
    old_password: str = Field(description="旧密码")
    new_password: str = Field(description="新密码")
