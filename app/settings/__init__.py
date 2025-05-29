from .config import settings, TORTOISE_ORM # Import both settings instance and global TORTOISE_ORM

# TORTOISE_ORM is now directly imported.
# The line "TORTOISE_ORM = settings.TORTOISE_ORM" is removed as it caused AttributeError.
