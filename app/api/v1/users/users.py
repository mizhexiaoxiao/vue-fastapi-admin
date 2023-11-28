import logging

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException
from tortoise.expressions import Q

from app.controllers.user import UserController
from app.core.dependency import DependPermisson
from app.schemas.base import Success, SuccessExtra
from app.schemas.users import *

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list", summary="查看用户列表", dependencies=[DependPermisson])
async def list_user(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    username: str = Query("", description="用户名称，用于搜索"),
    email: str = Query("", description="邮箱地址"),
):
    user_controller = UserController()
    q = Q()
    if username:
        q &= Q(username__contains=username)
    if email:
        q &= Q(email__contains=email)
    total, user_objs = await user_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict(m2m=True, exclude_fields=["password"]) for obj in user_objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看用户", dependencies=[DependPermisson])
async def get_user(
    user_id: int = Query(..., description="用户ID"),
):
    user_controller = UserController()
    user_obj = await user_controller.get(id=user_id)
    user_dict = await user_obj.to_dict(exclude_fields=["password"])
    return Success(data=user_dict)


@router.post("/create", summary="创建用户", dependencies=[DependPermisson])
async def create_user(
    user_in: UserCreate,
):
    user_controller = UserController()
    user = await user_controller.get_by_email(user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    new_user = await user_controller.create(obj_in=user_in)
    await user_controller.update_roles(new_user, user_in.roles)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新用户", dependencies=[DependPermisson])
async def update_user(
    user_in: UserUpdate,
):
    user_controller = UserController()
    user = await user_controller.update(obj_in=user_in)
    await user_controller.update_roles(user, user_in.roles)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除用户", dependencies=[DependPermisson])
async def delete_user(
    user_id: int = Query(..., description="用户ID"),
):
    user_controller = UserController()
    await user_controller.remove(id=user_id)
    return Success(msg="Deleted Successfully")
