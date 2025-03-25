from tortoise import Tortoise
from ujson import dumps

from app import logger
from app.config import settings

# 数据库连接配置
DATABASE = {
    "connections": {"default": settings.DATABASE_URL},
    "apps": {
        "default": {
            "models": [],
            "default_connection": "default",
        }
    },
    "aerich": {  # 为 Aerich 配置数据库连接
        "models": ["aerich.models"],  # Aerich 模型
        "default_connection": "default",  # 使用默认数据库连接
    },
    "use_tz": False,
    "timezone": "Asia/Shanghai",
}

# 用于存储模型的列表
models: list[str] = []


async def init_db():
    """
    初始化数据库连接，并生成数据库架构
    """
    DATABASE["apps"]["default"]["models"] = models

    logger.debug("参数预览\n" + dumps(DATABASE, ensure_ascii=False, indent=4))

    # 初始化数据库连接
    await Tortoise.init(DATABASE)
    await Tortoise.generate_schemas()  # 自动生成数据库架构

    # 输出每个数据库连接的状态
    for db_name, db_url in DATABASE["connections"].items():
        db_url = db_url.split("@", maxsplit=1)[-1]  # 提取 URL 部分
        logger.opt(colors=True).success(
            f"<y>数据库：{db_name} 连接成功</y> URL: <r>{db_url}</r>"
        )


async def disconnect():
    await Tortoise.close_connections()
    logger.opt(colors=True).success("<y>数据库：断开链接</y>")


def add_model(model: str, db_name: None | str = None, db_url: None | str = None):
    """
    向数据库添加模型
    :param model: 模型名称
    :param db_name: 数据库名称
    :param db_url: 数据库连接 URL
    """
    if (db_name is not None and db_url is None) or (
        db_name is None and db_url is not None
    ):
        raise TypeError("db_name 和 db_url 必须同时为 None 或 str")

    # 若提供了 db_name 和 db_url，则更新数据库配置
    if db_name and db_url:
        DATABASE["connections"][db_name] = db_url
        DATABASE["apps"][db_name] = {"models": [model], "default_connection": db_name}
        logger.opt(colors=True).success(
            f"<y>数据库：添加模型 {db_name}</y>: <r>{model}</r>"
        )
    else:
        # 向全局模型列表中添加模型
        models.append(model)
        logger.opt(colors=True).success(f"<y>数据库：添加模型</y>: <r>{model}</r>")
