import shutil

from aerich import Command
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from tortoise.expressions import Q

from app.api import api_router
from app.controllers.api import api_controller
from app.controllers.user import UserCreate, user_controller
from app.core.exceptions import (
    DoesNotExist,
    DoesNotExistHandle,
    HTTPException,
    HttpExcHandle,
    IntegrityError,
    IntegrityHandle,
    RequestValidationError,
    RequestValidationHandle,
    ResponseValidationError,
    ResponseValidationHandle,
)
from app.log import logger
from app.models.admin import Api, Menu, Role
from app.schemas.menus import MenuType
from app.settings.config import settings

from .middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware


def make_middlewares():
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
        ),
        Middleware(BackGroundTaskMiddleware),
        Middleware(
            HttpAuditLogMiddleware,
            methods=["GET", "POST", "PUT", "DELETE"],
            exclude_paths=[
                "/api/v1/base/access_token",
                "/docs",
                "/openapi.json",
            ],
        ),
    ]
    return middleware


def register_exceptions(app: FastAPI):
    app.add_exception_handler(DoesNotExist, DoesNotExistHandle)
    app.add_exception_handler(HTTPException, HttpExcHandle)
    app.add_exception_handler(IntegrityError, IntegrityHandle)
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)
    app.add_exception_handler(ResponseValidationError, ResponseValidationHandle)


def register_routers(app: FastAPI, prefix: str = "/api"):
    app.include_router(api_router, prefix=prefix)


async def init_superuser():
    user = await user_controller.model.exists()
    if not user:
        await user_controller.create_user(
            UserCreate(
                username="admin",
                email="admin@admin.com",
                password="123456",
                is_active=True,
                is_superuser=True,
            )
        )


async def init_menus():
    menus = await Menu.exists()
    if not menus:
        parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=1,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/user",
        )
        children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="用户管理",
                path="user",
                order=1,
                parent_id=parent_menu.id,
                icon="material-symbols:person-outline-rounded",
                is_hidden=False,
                component="/system/user",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="角色管理",
                path="role",
                order=2,
                parent_id=parent_menu.id,
                icon="carbon:user-role",
                is_hidden=False,
                component="/system/role",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="菜单管理",
                path="menu",
                order=3,
                parent_id=parent_menu.id,
                icon="material-symbols:list-alt-outline",
                is_hidden=False,
                component="/system/menu",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="API管理",
                path="api",
                order=4,
                parent_id=parent_menu.id,
                icon="ant-design:api-outlined",
                is_hidden=False,
                component="/system/api",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="部门管理",
                path="dept",
                order=5,
                parent_id=parent_menu.id,
                icon="mingcute:department-line",
                is_hidden=False,
                component="/system/dept",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="审计日志",
                path="auditlog",
                order=6,
                parent_id=parent_menu.id,
                icon="ph:clipboard-text-bold",
                is_hidden=False,
                component="/system/auditlog",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(children_menu)
        
        # --- Certificate Services (User) ---
        cert_services_parent = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="Certificate Services",
            path="/certificate",
            order=2, # After System Management
            parent_id=0,
            icon="mdi:security", # Example icon
            is_hidden=False,
            component="Layout", # Standard layout component
            keepalive=False,
            redirect="/certificate/request",
        )
        cert_services_children = [
            Menu(
                menu_type=MenuType.MENU,
                name="Request New Certificate",
                path="request", # Relative to /certificate
                order=1,
                parent_id=cert_services_parent.id,
                icon="mdi:file-document-plus-outline",
                is_hidden=False,
                component="/certificate/RequestForm",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="My Certificate Requests",
                path="my-requests", # Relative to /certificate
                order=2,
                parent_id=cert_services_parent.id,
                icon="mdi:list-box-outline",
                is_hidden=False,
                component="/certificate/MyRequestsList",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(cert_services_children)

        # --- Tools (User) ---
        tools_parent = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="Tools",
            path="/tools",
            order=3, # After Certificate Services
            parent_id=0,
            icon="mdi:tools", # Example icon
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/tools/pem-to-pfx",
        )
        tools_children = [
            Menu(
                menu_type=MenuType.MENU,
                name="PEM to PFX Converter",
                path="pem-to-pfx", # Relative to /tools
                order=1,
                parent_id=tools_parent.id,
                icon="mdi:key-swap",
                is_hidden=False,
                component="/tools/PemToPfxConverter",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(tools_children)

        # --- Certificate Admin (Admin, under System Management) ---
        # Find "System Management" parent menu again to add "Certificate Admin" under it
        system_management_parent = await Menu.get(path="/system", parent_id=0)
        if system_management_parent:
            cert_admin_parent = await Menu.create(
                menu_type=MenuType.CATALOG, # Or MENU if it's a direct link to a combined view
                name="Certificate Admin",
                path="certificate-admin", # Relative to /system
                order=7, # After existing System Management items
                parent_id=system_management_parent.id,
                icon="mdi:shield-key",
                is_hidden=False,
                component="Layout", # Or specific parent component for admin views
                keepalive=False,
                redirect="/system/certificate-admin/requests",
            )
            cert_admin_children = [
                Menu(
                    menu_type=MenuType.MENU,
                    name="Manage Cert Requests",
                    path="requests", # Relative to /system/certificate-admin
                    order=1,
                    parent_id=cert_admin_parent.id,
                    icon="mdi:clipboard-list-outline",
                    is_hidden=False,
                    component="/admin/certificate/RequestManagement",
                    keepalive=False,
                ),
                Menu(
                    menu_type=MenuType.MENU,
                    name="Manage CAs",
                    path="cas", # Relative to /system/certificate-admin
                    order=2,
                    parent_id=cert_admin_parent.id,
                    icon="mdi:shield-crown-outline",
                    is_hidden=False,
                    component="/admin/certificate/CAManagement",
                    keepalive=False,
                ),
            ]
            await Menu.bulk_create(cert_admin_children)
        else:
            logger.warning("System Management parent menu not found, cannot add Certificate Admin menus.")
        
        # Removed the old "一级菜单" example as it's not relevant
        # await Menu.create(
        #     menu_type=MenuType.MENU,
        #     name="一级菜单",
        #     path="/top-menu",
        #     order=2, # This order might conflict if not managed carefully
        #     parent_id=0,
        #     icon="material-symbols:featured-play-list-outline",
        #     is_hidden=False,
        #     component="/top-menu",
        #     keepalive=False,
        #     redirect="",
        # )


async def init_apis():
    apis = await api_controller.model.exists()
    if not apis:
        await api_controller.refresh_api()


async def init_db():
    command = Command(tortoise_config=settings.TORTOISE_ORM)
    try:
        await command.init_db(safe=True)
    except FileExistsError:
        pass

    await command.init()
    try:
        await command.migrate()
    except AttributeError:
        logger.warning("unable to retrieve model history from database, model history will be created from scratch")
        shutil.rmtree("migrations")
        await command.init_db(safe=True)

    await command.upgrade(run_in_transaction=True)


async def init_roles():
    roles = await Role.exists()
    if not roles:
        admin_role = await Role.create(
            name="管理员",
            desc="管理员角色",
        )
        user_role = await Role.create(
            name="普通用户",
            desc="普通用户角色",
        )

        # 分配所有API给管理员角色
        all_apis = await Api.all()
        await admin_role.apis.add(*all_apis)
        
        # 分配所有菜单给管理员
        all_menus_for_admin = await Menu.all()
        await admin_role.menus.add(*all_menus_for_admin)

        # 分配特定菜单给普通用户
        user_accessible_parent_paths = ["/certificate", "/tools"] # Paths of parent menus for users
        user_menus = await Menu.filter(
            Q(path__in=user_accessible_parent_paths, parent_id=0) | 
            Q(parent__path__in=user_accessible_parent_paths) | # Children of user-accessible parents
            Q(path="/system/user") # Profile page, assuming it's part of user management
        ).all()
        
        # Also add the "System Management" parent itself if we want users to see their profile link
        system_management_menu = await Menu.get_or_none(path="/system", parent_id=0)
        if system_management_menu:
            user_menus.append(system_management_menu)
            # Add "User Management" (profile) under "System Management" for users
            user_management_menu = await Menu.get_or_none(path="user", parent_id=system_management_menu.id)
            if user_management_menu:
                user_menus.append(user_management_menu)
        
        # Remove duplicates if any by converting to set of IDs then back to list of unique menus
        unique_user_menus = {menu.id: menu for menu in user_menus}
        await user_role.menus.add(*list(unique_user_menus.values()))

        # 为普通用户分配基本API
        basic_apis = await Api.filter(Q(method__in=["GET"]) | Q(tags="基础模块"))
        await user_role.apis.add(*basic_apis)


async def init_data():
    await init_db()
    await init_superuser()
    await init_menus()
    await init_apis()
    await init_roles()
