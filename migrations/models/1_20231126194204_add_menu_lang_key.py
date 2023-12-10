from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "menu" ADD "lang_key" VARCHAR(100)   /* i18n translation key */;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "menu" DROP COLUMN "lang_key";"""
