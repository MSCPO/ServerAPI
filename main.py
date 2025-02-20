import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import disconnect, init_db
from app.router.auth import router as auth_router
from app.router.servers import router as serves_router
from app.router.user import router as user_router
from app.router.webhook import router as webhook_router
from app.servers.GetServerStatus import query_servers_periodically


@asynccontextmanager
async def startup(_: FastAPI):
    # 初始化数据库连接
    await init_db()
    asyncio.create_task(query_servers_periodically())  # noqa: RUF006
    yield
    await disconnect()


app = FastAPI(lifespan=startup)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],  # Allows all origins
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(serves_router, prefix="/v1", tags=["servers"])
app.include_router(auth_router, prefix="/v1", tags=["auth"])
app.include_router(webhook_router, tags=["webhook"])
app.include_router(user_router, prefix="/v1", tags=["user"])

app.include_router
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=1)
