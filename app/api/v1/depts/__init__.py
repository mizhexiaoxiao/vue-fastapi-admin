from fastapi import APIRouter

from .depts import router

depts_router = APIRouter()
depts_router.include_router(router, tags=["部门模块"])

__all__ = ["depts_router"]
