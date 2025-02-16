import random as func_random
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Query
from tortoise.contrib.fastapi import HTTPNotFoundError

from app import crud, models
from app.db import disconnect, init_db


@asynccontextmanager
async def startup(_: FastAPI):
    # 初始化数据库连接
    await init_db()
    yield
    await disconnect()


app = FastAPI(lifespan=startup)


@app.get("/servers", response_model=list[models.ServerBase])
async def list_servers(
    random: bool = Query(True),
    limit: int = Query(10, ge=1),  # 默认每次返回10条
    offset: int = Query(0, ge=0),  # 从第多少条开始返回
):
    servers = await crud.get_servers()
    if random:
        func_random.shuffle(servers)  # 打乱列表

    # 分页
    return servers[offset : offset + limit]


@app.get("/servers/{server_id}", response_model=models.ServerBase)
async def get_server(server_id: int):
    server = await crud.get_server_by_id(server_id)
    if not server:
        raise HTTPNotFoundError(f"Server with ID {server_id} not found")
    return server


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=1)
