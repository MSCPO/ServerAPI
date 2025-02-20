from fastapi import APIRouter, HTTPException, Query, status

from .. import crud

router = APIRouter()


@router.get("/servers", response_model=crud.get_ServerShow_api,summary="获取服务器列表")
async def list_servers(
    limit: int | None = Query(None, ge=1),
    offset: int = Query(0, ge=0),
):
    return await crud.get_servers(limit=limit, offset=offset)


@router.get(
    "/servers/info/{server_id}",
    response_model=crud.get_ServerId_Show_api,
    summary="获取对应服务器具体信息",
)
async def get_server(server_id: int):
    server = await crud.get_server_by_id(server_id)
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
        )
    return server
