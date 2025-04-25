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
        await asyncio.gather(*tasks)
        await asyncio.sleep(60)


async def query_server_periodically(server: Server):
    logger.info(f"Querying server {server.name} ({server.ip})")
    newstats = await get_server_stats(server.ip, server.type)
    stats, _ = await ServerStatus.get_or_create(server=server)
    stats.stat_data = newstats
    await stats.save()
