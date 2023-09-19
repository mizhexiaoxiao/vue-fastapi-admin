from fastapi import APIRouter, Query
from fastapi.routing import APIRoute
from tortoise.expressions import Q

from app.controllers.api import api_controller
from app.log import logger
from app.models.admin import Api
from app.schemas import Success, SuccessExtra
from app.schemas.apis import *

router = APIRouter()


@router.get("/list", summary="查看API列表")
async def list_api(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    path: str = Query(None, description="API路径"),
    summary: str = Query(None, description="API简介"),
    tags: str = Query(None, description="API模块"),
):
    q = Q()
    if path:
        q &= Q(path__contains=path)
    if summary:
        q &= Q(summary__contains=summary)
    if tags:
        q &= Q(tags__contains=tags)
    total, api_objs = await api_controller.list(page=page, page_size=page_size, search=q, order=["tags", "id"])
    data = [await obj.to_dict() for obj in api_objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看Api")
async def get_api(
    id: int = Query(..., description="Api"),
):
    api_obj = await api_controller.get(id=id)
    data = await api_obj.to_dict()
    return Success(data=data)


@router.post("/create", summary="创建Api")
async def create_api(
    api_in: ApiCreate,
):
    await api_controller.create(obj_in=api_in)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新Api")
async def update_api(
    api_in: ApiUpdate,
):
    await api_controller.update(id=api_in.id, obj_in=api_in.update_dict())
    return Success(msg="Update Successfully")


@router.delete("/delete", summary="删除Api")
async def delete_api(
    api_id: int = Query(..., description="ApiID"),
):
    await api_controller.remove(id=api_id)
    return Success(msg="Deleted Success")


@router.post("/refresh", summary="刷新API列表")
async def refresh_api():
    from app import app

    # 删除废弃API数据
    all_api_list = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            all_api_list.append((list(route.methods)[0], route.path_format))
    delete_api = []
    for api in await Api.all():
        if (api.method, api.path) not in all_api_list:
            delete_api.append((api.method, api.path))
    for item in delete_api:
        method, path = item
        logger.debug(f"API Deleted {method} {path}")
        await Api.filter(method=method, path=path).delete()

    for route in app.routes:
        if isinstance(route, APIRoute):
            method = list(route.methods)[0]
            path = route.path_format
            summary = route.summary
            tags = list(route.tags)[0]
            api_obj = await Api.filter(method=method, path=path).first()
            if api_obj:
                await api_obj.update_from_dict(dict(method=method, path=path, summary=summary, tags=tags)).save()
            else:
                logger.debug(f"API Created {method} {path}")
                await Api.create(**dict(method=method, path=path, summary=summary, tags=tags))

    return Success(msg="OK")
