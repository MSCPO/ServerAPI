import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from passlib.context import CryptContext

from app import crud
from app.auth.auth import create_access_token
from app.auth.auth_crud import (
    UserLogin,
    get_user_by_username,
    verify_hcaptcha,
    verify_password,
)
from app.config import settings
from app.db import disconnect, init_db
from app.getstatus.GetServerStatus import query_servers_periodically

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    limit: int | None = Query(None, ge=1), offset: int = Query(0, ge=0)
):
    return await crud.get_servers(limit=limit, offset=offset)


@app.get(
    "/servers/info/{server_id}",
    response_model=crud.get_ServerId_Show_api,
)
async def get_server(server_id: int):
    server = await crud.get_server_by_id(server_id)
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
        )
    return server


@app.post("/login", response_model=dict)
async def login(user: UserLogin):
    if not await verify_hcaptcha(user.captcha_response):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hCaptcha response"
        )
    db_user = await get_user_by_username(user.username)
    if db_user is None or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # 创建并返回 JWT token
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/hcaptcha-site-key")
def get_hcaptcha_site_key():
    if site_key := settings.HCAPTCHA_SECRET_KEY:
        return {"hcaptcha_site_key": site_key}
    else:
        return JSONResponse(
            status_code=400, content={"message": "hCaptcha site key not configured"}
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=1)
