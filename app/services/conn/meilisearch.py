import meilisearch

from app.config import settings
from app.log import logger

client = meilisearch.Client(settings.MEILI_URL, settings.MEILI_API_KEY)


async def init_meilisearch_index():
    """初始化 Meilisearch 索引并设置相关配置"""
    index = client.index(settings.MEILI_INDEX)
    # 设置可搜索字段
    index.update_searchable_attributes(
        ["id", "name", "desc", "ip", "tags", "type", "auth_mode"]
    )
    index.update_filterable_attributes(
        [
            "type",
            "tags",
            "auth_mode",
            "is_member",
            "is_hide",
            "version",
        ]
    )
    logger.info("Meilisearch 索引初始化完成")
