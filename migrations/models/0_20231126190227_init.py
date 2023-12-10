from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "api" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "path" VARCHAR(100) NOT NULL  /* API路径 */,
    "method" VARCHAR(6) NOT NULL  /* 请求方法 */,
    "summary" VARCHAR(500) NOT NULL  /* 请求简介 */,
    "tags" VARCHAR(100) NOT NULL  /* API标签 */
);
CREATE TABLE IF NOT EXISTS "dept" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(20) NOT NULL UNIQUE /* 部门名称 */,
    "desc" VARCHAR(500)   /* 菜单描述 */,
    "is_deleted" INT NOT NULL  DEFAULT 0 /* 软删除标记 */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "parent_id" INT NOT NULL  DEFAULT 0 /* 父部门ID */
);
CREATE TABLE IF NOT EXISTS "menu" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(20) NOT NULL  /* 菜单名称 */,
    "remark" JSON   /* 保留字段 */,
    "menu_type" VARCHAR(7)   /* 菜单类型 */,
    "icon" VARCHAR(100)   /* 菜单图标 */,
    "path" VARCHAR(100) NOT NULL  /* 菜单路径 */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "parent_id" INT NOT NULL  DEFAULT 0 /* 父菜单ID */,
    "is_hidden" INT NOT NULL  DEFAULT 0 /* 是否隐藏 */,
    "component" VARCHAR(100) NOT NULL  /* 组件 */,
    "keepalive" INT NOT NULL  DEFAULT 1 /* 存活 */,
    "redirect" VARCHAR(100)   /* 重定向 */
);
CREATE TABLE IF NOT EXISTS "role" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(20) NOT NULL UNIQUE /* 角色名称 */,
    "desc" VARCHAR(500)   /* 角色描述 */
);
CREATE TABLE IF NOT EXISTS "user" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "username" VARCHAR(20) NOT NULL UNIQUE /* 用户名称 */,
    "alias" VARCHAR(30)   /* 姓名 */,
    "email" VARCHAR(255) NOT NULL UNIQUE /* 邮箱 */,
    "phone" VARCHAR(20)   /* 电话 */,
    "password" VARCHAR(128)   /* 密码 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否激活 */,
    "is_superuser" INT NOT NULL  DEFAULT 0 /* 是否为超级管理员 */,
    "last_login" TIMESTAMP   /* 最后登录时间 */
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS "role_menu" (
    "role_id" BIGINT NOT NULL REFERENCES "role" ("id") ON DELETE CASCADE,
    "menu_id" BIGINT NOT NULL REFERENCES "menu" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "role_api" (
    "role_id" BIGINT NOT NULL REFERENCES "role" ("id") ON DELETE CASCADE,
    "api_id" BIGINT NOT NULL REFERENCES "api" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "user_role" (
    "user_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "role_id" BIGINT NOT NULL REFERENCES "role" ("id") ON DELETE CASCADE
);"""





async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
