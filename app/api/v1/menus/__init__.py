from fastapi import APIRouter

from .menus import router

menus_router = APIRouter()
menus_router.include_router(router, tags=["菜单模块"])

__all__ = ["menus_router"]
