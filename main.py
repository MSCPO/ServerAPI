import asyncio
import uuid
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.log import logger
from app.router.auth import router as auth_router
from app.router.report import router as report_router
from app.router.search import router as search_router
from app.router.servers import router as serves_router
from app.router.user import router as user_router
from app.router.webhook import router as webhook_router
from app.services.conn.db import disconnect, init_db
from app.services.conn.meilisearch import init_meilisearch_index
from app.services.conn.redis import redis_client
from app.services.search.sync_index import sync_meilisearch_while
from app.services.servers.GetServerStatus import query_servers_periodically

REDIS_LOCK_KEY = "query_servers_lock"
REDIS_LOCK_TTL = 5
PROCESS_ID = str(uuid.uuid4())


async def acquire_lock() -> bool:
    """
    尝试获取 Redis 分布式锁，成功返回 True，失败返回 False。
    """

    lock_set = await redis_client.set(
        REDIS_LOCK_KEY, PROCESS_ID, ex=REDIS_LOCK_TTL, nx=True
    )

    return lock_set is True


release_lock_script = redis_client.register_script("""
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    else
        return 0
    end
""")


async def release_lock():
    await release_lock_script(keys=[REDIS_LOCK_KEY], args=[PROCESS_ID])


async def refresh_lock():
    """
    定期刷新锁，防止锁过期
    """
    while True:
        await asyncio.sleep(REDIS_LOCK_TTL * 0.6)
        stored_id: str = await redis_client.get(REDIS_LOCK_KEY)

        if stored_id and stored_id == PROCESS_ID:
            await redis_client.expire(REDIS_LOCK_KEY, REDIS_LOCK_TTL)
        else:
            logger.error("⛔ 续期失败，锁已被其他进程占用")
            break


@asynccontextmanager
async def startup(app: FastAPI):
    await init_db()
    app.state.task = app.state.lock_task = None

    if await acquire_lock():
        logger.success(f"🔐 获取到锁，进程 {PROCESS_ID} 启动任务")

        # 存储任务引用
        app.state.lock_task = asyncio.create_task(refresh_lock())  # 续期任务
        await init_meilisearch_index()
        app.state.task = [
            asyncio.create_task(query_servers_periodically()),
            asyncio.create_task(sync_meilisearch_while()),
        ]
    else:
        logger.warning("⛔ 另一个进程已持有锁，不启动任务")

    yield

    # 进程退出时清理任务
    if app.state.task:
        for task in app.state.task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.success("✅ 任务已取消")

    if app.state.lock_task:
        app.state.lock_task.cancel()
        try:
            await app.state.lock_task
        except asyncio.CancelledError:
            logger.success("✅ 续期任务已取消")

    await release_lock()
    await disconnect()


origins = [
    "https://mscpo.crashvibe.cn",
    "https://mscpo.1fu.top",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
]

app = FastAPI(lifespan=startup)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=origins,  # Allows all origins
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(serves_router, prefix="/v1", tags=["servers"])
app.include_router(auth_router, prefix="/v1", tags=["auth"])
app.include_router(webhook_router, tags=["webhook"])
app.include_router(user_router, prefix="/v1", tags=["user"])
app.include_router(search_router, prefix="/v1", tags=["search"])
app.include_router(report_router, prefix="/v1", tags=["report"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=4)
