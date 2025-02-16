from .models import Server


async def get_servers() -> list:
    server_list: list[Server] = await Server.all()
    server_show = []
    for server in server_list:
        server_data = {
            "id": server.id,
            "name": server.name,
            "ip": None,
            "type": server.type,
            "version": server.version,
            "desc": server.desc,
            "link": server.link,
            "is_member": server.is_member,
            "auth_mode": server.auth_mode,
            "tags": server.tags,
            "is_hide": server.is_hide,
        }
        if not server.is_hide:
            server_data["ip"] = server.ip
        server_show.append(server_data)
    return server_show


async def get_server_by_id(server_id: int) -> Server | None:
    return await Server.get_or_none(id=server_id)
