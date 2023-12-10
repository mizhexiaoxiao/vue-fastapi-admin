from pydantic import BaseModel, Field

from app.models.enums import MethodType


class BaseApi(BaseModel):
    path: str = Field(..., description="API路径", example="/api/v1/user/list")
    summary: str = Field("", description="API简介", example="查看用户列表")
    method: MethodType = Field(..., description="API方法", example="GET")
    tags: str = Field(..., description="API标签", example="User")


class ApiCreate(BaseApi):
    ...


class ApiUpdate(BaseApi):
    id: int

    def update_dict(self):
        return self.model_dump(exclude_unset=True, exclude={"id"})
