from fastapi import APIRouter, HTTPException, Query, status

from .. import crud

router = APIRouter()


# 获取服务器列表
@router.get(
    "/servers",
    response_model=crud.get_ServerShow_api,
    summary="获取服务器列表",
    responses={
        200: {
            "description": "成功获取服务器列表",
            "content": {
                "application/json": {
                    "example": {
                        "servers": [
                            {"id": 1, "name": "Server 1", "status": "active"},
                            {"id": 2, "name": "Server 2", "status": "inactive"},
                        ]
                    }
                }
            },
        },
        400: {
            "description": "无效的请求参数",
            "content": {
                "application/json": {"example": {"detail": "limit should be >= 1"}}
            },
        },
    },
)
async def list_servers(
    limit: int | None = Query(None, ge=1),  # 查询结果限制，最小为1
    offset: int = Query(0, ge=0),  # 查询偏移量，默认从第0个服务器开始
):
    """
    获取服务器列表。

    - `limit`: 返回的服务器数量，默认为空，传入1及以上的值。
    - `offset`: 查询的起始位置，默认为0。

    返回值为服务器列表，包含基本的服务器信息。
    """
    return await crud.get_servers(limit=limit, offset=offset)


# 获取服务器的具体信息
@router.get(
    "/servers/info/{server_id}",
    response_model=crud.get_ServerId_Show_api,
    summary="获取对应服务器具体信息",
    responses={
        200: {
            "description": "成功获取指定服务器信息",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Server 1",
                        "status": "active",
                        "location": "US-East",
                    }
                }
            },
        },
        404: {
            "description": "未找到该服务器",
            "content": {"application/json": {"example": {"detail": "未找到该服务器"}}},
        },
    },
)
async def get_server(server_id: int):
    """
    获取指定ID服务器的详细信息。

    - `server_id`: 服务器的唯一标识符。

    返回指定服务器的详细信息，如无法找到该服务器，则返回404。
    """
    server = await crud.get_server_by_id(server_id)
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到该服务器"
        )
    return server
