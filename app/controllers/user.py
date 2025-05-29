from datetime import datetime
from typing import List, Optional

from fastapi.exceptions import HTTPException

from datetime import datetime
from typing import List, Optional

from fastapi.exceptions import HTTPException

from app.core.crud import CRUDBase
from app.models.admin import User
from app.schemas.login import CredentialsSchema
from app.schemas.users import UserCreate, UserUpdate # UserUpdate might be needed
from app.utils.password import get_password_hash, verify_password
from app.core.ldap_service import authenticate_ldap_user # Added
from app.settings.config import settings # Added

from .role import role_controller


class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(model=User)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.model.filter(email=email).first()

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.model.filter(username=username).first()

    async def create_user(self, obj_in: UserCreate) -> User:
        # This method is for creating users with a hashed password (local auth)
        obj_in_data = obj_in.model_dump()
        obj_in_data["password"] = get_password_hash(password=obj_in.password)
        # Ensure avatar is handled if not provided
        if "avatar" not in obj_in_data or obj_in_data["avatar"] is None:
             obj_in_data["avatar"] = f"https://ui-avatars.com/api/?name={obj_in_data['username']}" # Default avatar
        obj = await self.model.create(**obj_in_data)
        return obj
    
    async def create_ldap_user(self, user_details: dict) -> User:
        # Creates a user from LDAP details, password is not hashed as it's managed by LDAP
        user_data = {
            "username": user_details['username'],
            "email": user_details.get('email'),
            "alias": user_details.get('alias'),
            "password": "ldap_managed_password", # Placeholder for LDAP managed password
            "is_superuser": user_details.get('is_superuser', False),
            "is_active": True, # LDAP users are active by default
            "avatar": f"https://ui-avatars.com/api/?name={user_details['username']}" # Default avatar
        }
        user = await self.model.create(**user_data)
        return user

    async def update_last_login(self, user_id: int) -> None: # Changed id to user_id for clarity
        user = await self.get_or_none(id=user_id) # Use get_or_none for safety
        if user:
            user.last_login = datetime.now()
            await user.save()

    async def authenticate(self, credentials: CredentialsSchema) -> Optional["User"]:
        if settings.LDAP_SERVER_URI:
            # LDAP authentication is configured
            ldap_user_details = authenticate_ldap_user(credentials.username, credentials.password)

            if ldap_user_details:
                # LDAP authentication successful
                user = await self.get_by_username(credentials.username)
                if user:
                    # User exists, update details
                    user.email = ldap_user_details.get('email', user.email)
                    user.alias = ldap_user_details.get('alias', user.alias)
                    user.is_superuser = ldap_user_details.get('is_superuser', user.is_superuser)
                    user.password = "ldap_managed_password" # Mark as LDAP managed
                    user.is_active = True # Ensure user is active
                    await user.save()
                else:
                    # User does not exist, create new user from LDAP details
                    user = await self.create_ldap_user(ldap_user_details)
                
                if user: # Ensure user object is valid
                    await self.update_last_login(user.id)
                return user # Return the local user object
            else:
                # LDAP authentication failed (and LDAP is configured)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,  # Correct status for auth failure
                    detail="LDAP authentication failed. Invalid username/password or LDAP system issue."
                )
        else:
            # LDAP is not configured, fall back to local database authentication
            user = await self.model.filter(username=credentials.username).first()
            if not user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的用户名") # "Invalid username"
            if not user.password: # Handle cases where password might be None (e.g. LDAP managed user trying local login)
                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码错误!") # "Incorrect password!"
            verified = verify_password(credentials.password, user.password)
            if not verified:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码错误!") # "Incorrect password!"
            if not user.is_active:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已被禁用") # "User is disabled"
            
            if user: # Ensure user object is valid before updating last_login
                await self.update_last_login(user.id)
            return user

    async def update_roles(self, user: User, role_ids: List[int]) -> None:
        await user.roles.clear()
        for role_id in role_ids:
            role_obj = await role_controller.get(id=role_id) # Ensure role_controller.get uses get_or_none or handles not found
            if role_obj: # Add role only if it exists
                await user.roles.add(role_obj)

    async def reset_password(self, user_id: int):
        user_obj = await self.get_or_none(id=user_id) # Changed to get_or_none
        if not user_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if user_obj.is_superuser: # This check is fine
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不允许重置超级管理员密码")
        if "ldap_managed_password" == user_obj.password: # Check if LDAP managed
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不允许重置LDAP管理的用户的密码")
        user_obj.password = get_password_hash(password="123456") # Default password
        await user_obj.save()


user_controller = UserController()
