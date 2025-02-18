import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import crud
from app.db import disconnect, init_db
from app.getstatus.GetServerStatus import query_servers_periodically


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


@app.get("/servers", response_model=crud.get_ServerShow_api)
async def list_servers(
    limit: int | None = Query(None, ge=1),
    offset: int = Query(0, ge=0),
):
    return await crud.get_servers(limit=limit, offset=offset)


@app.get(
    "/servers/info/{server_id}",
    response_model=crud.get_ServerId_Show_api,
)
async def get_server(server_id: int):
    server = await crud.get_server_by_id(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=1)
