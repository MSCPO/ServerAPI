from typing import Any
from fastapi import APIRouter, Query
from app.services.conn.meilisearch import client
from app.config import settings

router = APIRouter()


@router.get("/search", tags=["search"]
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
