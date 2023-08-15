from starlette.background import BackgroundTasks

from .ctx import CTX_BG_TASKS


class BgTasks:
    """后台任务统一管理"""

    @classmethod
    async def init_bg_tasks_obj(cls):
        """实例化后台任务，并设置到上下文"""
        bg_tasks = BackgroundTasks()
        CTX_BG_TASKS.set(bg_tasks)

    @classmethod
    async def get_bg_tasks_obj(cls):
        """从上下文中获取后台任务实例"""
        return CTX_BG_TASKS.get()

    @classmethod
    async def add_task(cls, func, *args, **kwargs):
        """添加后台任务"""
        bg_tasks = await cls.get_bg_tasks_obj()
        bg_tasks.add_task(func, *args, **kwargs)

    @classmethod
    async def execute_tasks(cls):
        """执行后台任务，一般是请求结果返回之后执行"""
        bg_tasks = await cls.get_bg_tasks_obj()
        if bg_tasks.tasks:
            await bg_tasks()
