# 新增model自动导入
import pkgutil
import importlib

# 当前包名
package_name = __name__
# 遍历当前目录下的所有模块和包
for _, name, is_pkg in pkgutil.iter_modules(__path__, prefix=package_name + '.'):
    # 跳过包，只导入模块
    if not is_pkg:
        # 动态导入模块
        module = importlib.import_module(name)
        # 从导入的模块中导入所有符号到当前命名空间
        globals().update(vars(module))
    