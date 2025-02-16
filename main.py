import random
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Query
from tortoise.contrib.fastapi import HTTPNotFoundError

from app import crud
from app.db import disconnect, init_db


@asynccontextmanager
async def startup(_: FastAPI):
    # 初始化数据库连接
    await init_db()
    yield
    await disconnect()


app = FastAPI(lifespan=startup)


@app.get("/servers", response_model=list)
async def list_servers(
    limit: int | None = Query(None, ge=1),
    offset: int = Query(0, ge=0),
):
    return await crud.get_servers(limit=limit, offset=offset)


@app.get("/servers/random", response_model=list)
async def list_random_servers():
    servers = await crud.get_servers()
    random.shuffle(servers)
    return servers


@app.get("/servers/{server_id}", response_model=dict | HTTPNotFoundError)
async def get_server(server_id: int):
    server = await crud.get_server_by_id(server_id)
    return server or HTTPNotFoundError(detail="Server not found")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=1)
