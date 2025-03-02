from app.log import logger
from app.services.conn.meilisearch import client
from app.services.servers.models import Server


async def batch_sync_to_meilisearch():
    servers = await Server.all()
    documents = [
        {
            "id": server.id,
            "name": server.name,
            "type": server.type,
            "version": server.version,
            "desc": server.desc,
            "link": server.link,
            "ip": server.ip,
            "is_member": server.is_member,
            "is_hide": server.is_hide,
            "auth_mode": server.auth_mode,
            "tags": server.tags,
        }
        for server in servers
    ]
    client.index("servers").add_documents(documents)
    print("Batch synced servers to Meilisearch!")
    logger.info("已同步 Meilisearch 索引")
