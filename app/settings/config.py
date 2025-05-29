import os
import typing

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    VERSION: str = "0.1.0"
    APP_TITLE: str = "Vue FastAPI Admin"
    PROJECT_NAME: str = "Vue FastAPI Admin"
    APP_DESCRIPTION: str = "Description"

    CORS_ORIGINS: typing.List = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: typing.List = ["*"]
    CORS_ALLOW_HEADERS: typing.List = ["*"]

    DEBUG: bool = True

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    SECRET_KEY: str = "3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf"  # openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 day

    # LDAP settings (Re-adding from Subtask 1)
    LDAP_SERVER_URI: str = ""
    LDAP_BIND_DN: str = ""
    LDAP_BIND_PASSWORD: str = ""
    LDAP_BASE_DN: str = ""
    LDAP_USER_LOGIN_ATTR: str = ""
    LDAP_USER_OBJECT_FILTER: str = ""
    LDAP_USER_EMAIL_ATTR: str = ""
    LDAP_USER_FULLNAME_ATTR: str = ""
    LDAP_ADMIN_GROUP_DN: str = ""
    LDAP_USER_ROLE_GROUP_PREFIX: str = ""

    # TORTOISE_ORM is now defined globally below
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # CA Settings
    CA_CERT_PATH: str = ""
    CA_PRIVATE_KEY_PATH: str = ""
    CA_PRIVATE_KEY_PASSWORD: typing.Optional[str] = None

# Global TORTOISE_ORM configuration
# Note: BASE_DIR needs to be defined before this block if used, or paths adjusted.
# For simplicity, using os.path.abspath for db.sqlite3 path if it were active.
_BASE_DIR_FOR_SQLITE = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
TORTOISE_ORM = {
    "connections": {
        # SQLite configuration (commented out)
        # "sqlite": {
        #     "engine": "tortoise.backends.sqlite",
        #     "credentials": {"file_path": f"{_BASE_DIR_FOR_SQLITE}/db.sqlite3"},
        # },
        # MySQL/MariaDB configuration
        "mysql": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": "localhost",
                "port": 3306,
                "user": "yourusername_placeholder",
                "password": "yourpassword_placeholder",
                "database": "yourdatabase_placeholder",
            },
        },
    },
    "apps": {
        "models": {
            "models": ["app.models.admin", "app.models.certificate", "aerich.models"], # Updated model paths
            "default_connection": "mysql",
        },
    },
    "use_tz": False,
    "timezone": "Asia/Shanghai",
}

settings = Settings()
# The line "settings.TORTOISE_ORM = TORTOISE_ORM" has been removed
# as it caused a ValueError during aerich init.
# Application code should be updated to reference the global TORTOISE_ORM if needed.
