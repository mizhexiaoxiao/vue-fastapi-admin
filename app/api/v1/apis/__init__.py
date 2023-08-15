from fastapi import APIRouter

from .apis import router

apis_router = APIRouter()
apis_router.include_router(router, tags=["API模块"])

__all__ = ["apis_router"]
