from typing import Any

from fastapi import APIRouter, Query

from app.config import settings
from app.services.conn.meilisearch import client

router = APIRouter()


@router.get(
    "/search",
    tags=["search"],
    responses={
        200: {
            "description": "搜索成功",
            "content": {
                "application/json": {
                    "example": {
                        "results": [
                            {
                                "id": 2,
                                "name": "服务器名称",
                                "desc": "描述内容",
                                "ip": "example.com:37581",
                                "type": "BEDROCK",
                                "is_member": True,
                                "tags": ["生存", "建筑"],
                            }
                        ]
                    }
                }
            },
        }
    },
)
async def search_servers(
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, description="返回条数"),
    filters: str = Query(None, description="筛选条件，例如 'is_member=true'"),
):
    params: dict[str, Any] = {"limit": limit}
    if filters:
        params["filter"] = filters
    results = client.index(settings.MEILI_INDEX).search(query, params)
    return {"results": results.get("hits", [])}
