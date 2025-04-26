import asyncio

from app import logger
from app.services.servers.crud import Server, ServerStatus
from app.services.servers.MineStatus import get_server_stats


async def query_servers_periodically():
    while True:
        servers = await Server.all()

        tasks = []
        tasks.extend(
            asyncio.create_task(query_server_periodically(server)) for server in servers
        )
        # 并行执行所有任务
        logger.info(
            f"正在查询服务器状态，共 {len(servers)} 个服务器，任务数：{len(tasks)}"
        )
        await asyncio.gather(*tasks)
        logger.info("已同步服务器状态")
        await asyncio.sleep(60)


async def query_server_periodically(server: Server):
    newstats = await get_server_stats(server.ip, server.type)
    stats, _ = await ServerStatus.get_or_create(server=server)
    stats.stat_data = newstats
    await stats.save()
