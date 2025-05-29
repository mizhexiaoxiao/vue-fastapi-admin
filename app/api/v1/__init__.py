from fastapi import APIRouter

from app.core.dependency import DependPermisson

from .apis import apis_router
from .auditlog import auditlog_router
from .base import base_router
from .depts import depts_router
from .menus import menus_router
from .roles import roles_router
from .users import users_router
from .certificate_requests import router as certificate_requests_router
from .issued_certificates import router as issued_certificates_router # New import
from .ca_management import router as ca_management_router           # New import
from .certificate_utils import router as certificate_utils_router     # New import

v1_router = APIRouter()

v1_router.include_router(base_router, prefix="/base")
v1_router.include_router(users_router, prefix="/user", dependencies=[DependPermisson])
v1_router.include_router(roles_router, prefix="/role", dependencies=[DependPermisson])
v1_router.include_router(menus_router, prefix="/menu", dependencies=[DependPermisson])
v1_router.include_router(apis_router, prefix="/api", dependencies=[DependPermisson])
v1_router.include_router(depts_router, prefix="/dept", dependencies=[DependPermisson])
v1_router.include_router(auditlog_router, prefix="/auditlog", dependencies=[DependPermisson])
v1_router.include_router(certificate_requests_router, prefix="/certificate-requests", dependencies=[DependPermisson])
v1_router.include_router(issued_certificates_router, prefix="/issued-certificates") # User-specific, per-endpoint auth
v1_router.include_router(ca_management_router, prefix="/ca-management", dependencies=[DependPermisson]) # Admin only
v1_router.include_router(certificate_utils_router, prefix="/certificate-utils") # User-specific, per-endpoint auth
