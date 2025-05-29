from datetime import datetime, timedelta, timezone
from typing import Optional # Added Optional

from fastapi import APIRouter, HTTPException # Added HTTPException

from app.controllers.user import user_controller
from app.schemas.users import UserCreate # Added UserCreate
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.admin import Api, Menu, Role, User
from app.schemas.base import Fail, Success
from app.schemas.login import *
from app.schemas.users import UpdatePassword
from app.settings import settings
from app.utils.jwt import create_access_token
from app.utils.password import get_password_hash, verify_password
from app.core.auth.ldap_mock import mock_ldap_authenticate # LDAP Mock
from app.controllers.role import role_controller # To fetch roles

router = APIRouter()


@router.post("/access_token", summary="获取token")
async def login_access_token(credentials: CredentialsSchema):
    ldap_user_data = mock_ldap_authenticate(username=credentials.username, password=credentials.password)
    user: Optional[User] = None

    if ldap_user_data:
        # LDAP authentication successful
        user = await user_controller.get_by_username(username=ldap_user_data["username"])
        if not user:
            # Create new local user for LDAP user
            # Ensure email is unique if your model requires it. LDAP email might not be unique system-wide.
            # For this mock, we assume username from LDAP is unique enough for local username.
            existing_email_user = await user_controller.get_by_email(ldap_user_data["email"])
            if existing_email_user:
                # Handle email conflict, e.g. by raising an error or modifying email
                # For mock, let's assume email is also unique or we append something.
                # This part might need more robust handling in a real scenario.
                pass # Or raise HTTPException(status_code=400, detail="Email from LDAP already exists for another user")

            new_user_data = UserCreate(
                username=ldap_user_data["username"],
                email=ldap_user_data["email"],
                alias=f"{ldap_user_data.get('first_name', '')} {ldap_user_data.get('last_name', '')}".strip(),
                password=get_password_hash("ldap_user_no_local_login"), # Non-usable password
                is_active=True,
                is_superuser=False, # LDAP users are not superusers by default
                dept_id=None, # Or some default department
            )
            # Directly use model to create to bypass UserCreate schema password validation if it's strict
            # user = await User.create(**new_user_data.model_dump(exclude_unset=True), password=get_password_hash("..."))
            # However, user_controller.create_user will hash the password again.
            # So, let's create then update password to None or a non-usable hash.
            
            # Simplest way: create user object directly
            user = await User.create(
                username=new_user_data.username,
                email=new_user_data.email,
                alias=new_user_data.alias,
                password=None, # Or a known non-usable hash
                is_active=new_user_data.is_active,
                is_superuser=new_user_data.is_superuser,
                dept_id=new_user_data.dept_id,
                last_login=datetime.now(timezone.utc) # Set last_login for new user
            )
            
            # Assign default role "普通用户"
            # It's better to fetch role by a stable identifier or config value if possible
            default_role = await role_controller.get_by_name(name="普通用户")
            if default_role:
                await user_controller.update_roles(user, [default_role.id])
            else:
                # Handle case where default role isn't found, maybe log a warning
                # For now, user will have no roles if "普通用户" doesn't exist
                pass
        else:
            # User exists, ensure password is not usable locally if they are an LDAP user
            if user.password is not None and not verify_password("ldap_user_no_local_login", user.password):
                 # This check is a bit circular with the hash above.
                 # More directly, if user is from LDAP, ensure local password field is nullified or set to known hash.
                 user.password = None # Or get_password_hash("ldap_user_no_local_login")
                 await user.save(update_fields=['password'])
        
        # Update last login for LDAP user
        await user_controller.update_last_login(user.id)

    else:
        # LDAP authentication failed, fall back to local DB authentication
        user = await user_controller.authenticate(credentials)
        await user_controller.update_last_login(user.id)

    if not user: # Should not happen if authenticate() raises HTTPException or LDAP creates user
        raise HTTPException(status_code=400, detail="Invalid credentials or LDAP user creation failed")

    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + access_token_expires

    data = JWTOut(
        access_token=create_access_token(
            data=JWTPayload(
                user_id=user.id,
                username=user.username,
                is_superuser=user.is_superuser,
                exp=expire,
            )
        ),
        username=user.username,
    )
    return Success(data=data.model_dump())


@router.get("/userinfo", summary="查看用户信息", dependencies=[DependAuth])
async def get_userinfo():
    user_id = CTX_USER_ID.get()
    user_obj = await user_controller.get(id=user_id)
    data = await user_obj.to_dict(exclude_fields=["password"])
    data["avatar"] = "https://avatars.githubusercontent.com/u/54677442?v=4"
    return Success(data=data)


@router.get("/usermenu", summary="查看用户菜单", dependencies=[DependAuth])
async def get_user_menu():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()
    menus: list[Menu] = []
    if user_obj.is_superuser:
        menus = await Menu.all()
    else:
        role_objs: list[Role] = await user_obj.roles
        for role_obj in role_objs:
            menu = await role_obj.menus
            menus.extend(menu)
        menus = list(set(menus))
    parent_menus: list[Menu] = []
    for menu in menus:
        if menu.parent_id == 0:
            parent_menus.append(menu)
    res = []
    for parent_menu in parent_menus:
        parent_menu_dict = await parent_menu.to_dict()
        parent_menu_dict["children"] = []
        for menu in menus:
            if menu.parent_id == parent_menu.id:
                parent_menu_dict["children"].append(await menu.to_dict())
        res.append(parent_menu_dict)
    return Success(data=res)


@router.get("/userapi", summary="查看用户API", dependencies=[DependAuth])
async def get_user_api():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()
    if user_obj.is_superuser:
        api_objs: list[Api] = await Api.all()
        apis = [api.method.lower() + api.path for api in api_objs]
        return Success(data=apis)
    role_objs: list[Role] = await user_obj.roles
    apis = []
    for role_obj in role_objs:
        api_objs: list[Api] = await role_obj.apis
        apis.extend([api.method.lower() + api.path for api in api_objs])
    apis = list(set(apis))
    return Success(data=apis)


@router.post("/update_password", summary="修改密码", dependencies=[DependAuth])
async def update_user_password(req_in: UpdatePassword):
    user_id = CTX_USER_ID.get()
    user = await user_controller.get(user_id)
    verified = verify_password(req_in.old_password, user.password)
    if not verified:
        return Fail(msg="旧密码验证错误！")
    user.password = get_password_hash(req_in.new_password)
    await user.save()
    return Success(msg="修改成功")
