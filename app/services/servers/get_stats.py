import asyncio
import time

from app import logger
from app.services.servers.crud import Server, ServerStatus
from app.services.servers.stats_utils import get_server_stats

queue = asyncio.Queue()
WORKER_COUNT = 10

# 缓存最近状态数据，减少重复写入
status_cache = {}
CACHE_TIMEOUT = 300


async def query_servers_periodically():
    [asyncio.create_task(consumer(i)) for i in range(WORKER_COUNT)]
    while True:
        servers = await Server.all()
        for server in servers:
            await queue.put(server)
        logger.info(f"已放入 {len(servers)} 台服务器到任务队列")
        await asyncio.sleep(60)


async def consumer(worker_id: int):
    while True:
        server = await queue.get()
        try:
            new_stats = await get_server_stats(server.ip, server.type)

            # 获取缓存
            cached = status_cache.get(server.id)
            now = time.time()

            # 判断是否需要更新
            should_update = (
                cached is None  # 无缓存
                or cached["stat_data"] != new_stats  # 状态变化
                or now - cached["timestamp"] > CACHE_TIMEOUT  # 缓存超时
            )

            if should_update:
                stats, _ = await ServerStatus.get_or_create(server=server)
                stats.stat_data = new_stats
                await stats.save()

                # 更新缓存
                status_cache[server.id] = {"stat_data": new_stats, "timestamp": now}

                logger.info(f"[Worker {worker_id}] 更新服务器 {server.id} 状态")
            else:
                logger.debug(f"[Worker {worker_id}] 跳过未变服务器 {server.id}")

        except Exception as e:
            logger.error(f"[Worker {worker_id}] 查询服务器 {server.id} 出错: {e}")
        finally:
            queue.task_done()
