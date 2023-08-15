import jwt

from app.schemas.login import JWTPayload
from app.settings.config import settings


def create_access_token(*, data: JWTPayload):
    payload = data.dict().copy()
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt
