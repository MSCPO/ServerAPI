import asyncio

from app import logger
from app.services.servers.crud import Server, ServerStatus
from app.services.servers.stats_utils import get_server_stats


async def query_servers_periodically():
    while True:
        servers = await Server.all()

        # 使用 asyncio.gather 优化并行任务
        logger.info(f"正在查询服务器状态，共 {len(servers)} 个服务器")
        await asyncio.gather(*(query_server_periodically(server) for server in servers))
        logger.info("已同步服务器状态")
        await asyncio.sleep(60)


async def query_server_periodically(server: Server):
    try:
        newstats = await get_server_stats(server.ip, server.type)
        stats, _ = await ServerStatus.get_or_create(server=server)
        stats.stat_data = newstats
        await stats.save()
    except Exception as e:
        logger.error(f"查询服务器 {server.id} 状态时出错: {e}")
