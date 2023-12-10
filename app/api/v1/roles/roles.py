import logging

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException
from tortoise.expressions import Q

from app.controllers import role_controller
from app.schemas.base import Success, SuccessExtra
from app.schemas.roles import *

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/list", summary="查看角色列表")
async def list_role(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    role_name: str = Query("", description="角色名称，用于查询"),
):
    q = Q()
    if role_name:
        q = Q(name__contains=role_name)
    total, role_objs = await role_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in role_objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看角色")
async def get_role(
    role_id: int = Query(..., description="角色ID"),
):
    role_obj = await role_controller.get(id=role_id)
    return Success(data=await role_obj.to_dict())


@router.post("/create", summary="创建角色")
async def create_role(role_in: RoleCreate):
    if await role_controller.is_exist(name=role_in.name):
        raise HTTPException(
            status_code=400,
            detail="The role with this rolename already exists in the system.",
        )
    await role_controller.create(obj_in=role_in)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新角色")
async def update_role(role_in: RoleUpdate):
    await role_controller.update(id=role_in.id, obj_in=role_in.update_dict())
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除角色")
async def delete_role(
    role_id: int = Query(..., description="角色ID"),
):
    await role_controller.remove(id=role_id)
    return Success(msg="Deleted Success")


@router.get("/authorized", summary="查看角色权限")
async def get_role_authorized(id: int = Query(..., description="角色ID")):
    role_obj = await role_controller.get(id=id)
    data = await role_obj.to_dict(m2m=True)
    return Success(data=data)


@router.post("/authorized", summary="更新角色权限")
async def update_role_authorized(role_in: RoleUpdateMenusApis):
    role_obj = await role_controller.get(id=role_in.id)
    await role_controller.update_roles(role=role_obj, menu_ids=role_in.menu_ids, api_infos=role_in.api_infos)
    return Success(msg="Updated Successfully")
