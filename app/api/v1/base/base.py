from datetime import datetime, timedelta, timezone

from urllib import parse
from fastapi import APIRouter, Request, HTTPException

from app.controllers.user import user_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.admin import Api, Menu, Role, User
from app.schemas.base import Fail, Success
from app.schemas.login import *
from app.schemas.users import UpdatePassword, ForgetPasswordSchema, ResetPasswordSchema
from app.core.bgtask import BgTasks
from app.settings import settings
from app.utils.jwt import create_access_token
from app.utils.password import get_password_hash, verify_password, send_forgot_password_email

router = APIRouter()


@router.post("/access_token", summary="获取token")
async def login_access_token(credentials: CredentialsSchema):
    user: User = await user_controller.authenticate(credentials)
    await user_controller.update_last_login(user.id)
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


@router.post("/forgot_password", summary="忘记密码")
async def forget_password(request: Request, forget_password_schema: ForgetPasswordSchema):
    email_address = forget_password_schema.email
    user_obj = await user_controller.get_by_email(email_address)
    if not user_obj:
        raise HTTPException(status_code=404, detail="notFound")

    if not user_obj.is_active:
        raise HTTPException(status_code=403, detail="userHasDisabled")

    uuid_v4 = await user_controller.forgot_password(email_address)
    referer_url = request.headers.get("referer")
    if not referer_url:
        raise HTTPException(status_code=400, detail="refererUrlNotFound")

    reset_url = parse.urljoin(referer_url, f"/reset-password/{uuid_v4}")
    await BgTasks.add_task(send_forgot_password_email,
                           language=forget_password_schema.language,
                           reset_url=reset_url,
                           app_title=settings.APP_TITLE,
                           to_address=email_address
                           )

    return Success(code=200, msg="sendEmailSuccess")


@router.post('/rest_password', summary="重置密码")
async def rest_password(reset_password_schema: ResetPasswordSchema):
    await user_controller.reset_password_by_token(reset_password_schema.reset_token,
                                                  reset_password_schema.password)
    return Success(code=200, msg="resetSuccessful")


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
