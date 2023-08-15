from datetime import datetime
from typing import List, Optional

from fastapi.exceptions import HTTPException

from app.core.crud import CRUDBase
from app.models.admin import User
from app.schemas.login import CredentialsSchema
from app.schemas.users import UserCreate, UserUpdate
from app.utils.password import get_password_hash, verify_password

from .role import role_controller


class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(model=User)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.model.filter(email=email).first()

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.model.filter(username=username).first()

    async def create(self, obj_in: UserCreate) -> User:
        obj_in.password = get_password_hash(password=obj_in.password)
        obj = await super().create(obj_in.create_dict())
        return obj

    async def update(self, obj_in: UserUpdate) -> User:
        return await super().update(id=obj_in.id, obj_in=obj_in.update_dict())

    async def update_last_login(self, id: int) -> None:
        user = await self.model.get(id=id)
        user.last_login = datetime.now()
        await user.save()

    async def authenticate(self, credentials: CredentialsSchema) -> Optional["User"]:
        user = await self.model.filter(username=credentials.username).first()
        if not user:
            raise HTTPException(status_code=400, detail="无效的用户名")
        verified = verify_password(credentials.password, user.password)
        if not verified:
            raise HTTPException(status_code=400, detail="密码错误!")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="用户已被禁用")
        return user

    async def update_roles(self, user: User, roles: List[int]) -> None:
        await user.roles.clear()
        for role_id in roles:
            role_obj = await role_controller.get(id=role_id)
            await user.roles.add(role_obj)


user_controller = UserController()
