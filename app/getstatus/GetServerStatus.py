import asyncio

from .. import logger
from ..models import Server, ServerStats
from .MineStatus import get_server_stats


# 定义一个异步任务来每5分钟查询一次所有服务器
async def query_servers_periodically():
    # 获取所有的服务器数据，假设你用 async ORM 查询
    servers = await Server.all()  # 查询所有服务器

    # 调度每个服务器的查询任务
    tasks = []
    tasks.extend(
        asyncio.create_task(query_server_periodically(server)) for server in servers
    )
    # 并行执行所有任务
    await asyncio.gather(*tasks)


# 定义每个服务器的查询任务
async def query_server_periodically(server: Server):
    while True:
        # 每隔5分钟进行一次查询
        logger.info(f"Querying server {server.name} ({server.ip})")
        newstats = await get_server_stats(server.ip, server.type)
        # 储存或修改服务器状态
        stats, _ = await ServerStats.get_or_create(server=server)
        stats.stat_data = newstats
        await stats.save()
        await asyncio.sleep(300)
