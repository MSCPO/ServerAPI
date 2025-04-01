import asyncio

from fastapi import Depends, HTTPException, status

from app.services.auth.schemas import jwt_data
from app.services.servers.models import (
    Gallery,
    GalleryImage,
    Server,
    ServerStatus,
)
from app.services.servers.schemas import (
    AddServerGallerys,
    GetServerGallerys,
    GetServerIdShowAPI,
    GetServerManagers,
    GetServerShowAPI,
    GetServerStatusAPI,
    Motd,
    UserBase,
)
from app.services.servers.utils import (
    get_server_cover_url,
    get_server_gallerys_urls,
    validate_and_upload_gallery,
    validate_description,
    validate_name,
)
from app.services.user.crud import get_current_user
from app.services.user.models import RoleEnum, SerRoleEnum, User, UserServer
from app.services.user.utils import get_user_avatar_url


async def GetServers(
    limit: int | None = None, offset: int = 0, user: int | None = None
) -> GetServerShowAPI:
    # 并发查询服务器总数和成员数
    total_servers, total_member = await asyncio.gather(
        Server.all().count(), Server.filter(is_member=True).count()
    )

    # 构建查询
    query = Server.all().offset(offset)
    if limit is not None:
        query = query.limit(limit)
    server_query = await query

    # 并发调用每个服务器的详情查询
    tasks = [GetServer_by_id(server.id, user) for server in server_query]
    server_info_list = await asyncio.gather(*tasks)
    # 过滤掉返回 None 的情况
    server_list = [info for info in server_info_list if info is not None]

    return GetServerShowAPI(
        server_list=server_list, total_member=total_member, total=total_servers
    )


async def GetServer_by_id(
    server_id: int, user: int | None
) -> None | GetServerIdShowAPI:
    # 查询服务器是否存在，不存在直接返回 None
    server = await Server.get_or_none(id=server_id)
    if not server:
        return None

    # 并发查询服务器状态和用户权限（user_server）
    server_status_task = ServerStatus.get_or_none(server=server)
    user_server_task = (
        UserServer.get_or_none(user=user, server=server_id)
        if user
        else asyncio.sleep(0, result=None)
    )
    cover_task = get_server_cover_url(server)

    user_info_task = User.get_or_none(id=user)
    (
        server_status,
        user_server,
        user_info,
        cover_url,
    ) = await asyncio.gather(
        server_status_task, user_server_task, user_info_task, cover_task
    )

    permission = (
        SerRoleEnum.owner
        if user_info and user_info.role == "admin"
        else (user_server.role if user_server else "guest")
    )
    status_data = None
    if server_status and server_status.stat_data:
        stat_data = server_status.stat_data
        status_data = GetServerStatusAPI(
            players=stat_data["players"],
            delay=stat_data["delay"],
            version=stat_data["version"],
            motd=Motd(
                plain=stat_data["motd"]["plain"],
                html=stat_data["motd"]["html"],
                minecraft=stat_data["motd"]["minecraft"],
                ansi=stat_data["motd"]["ansi"],
            ),
            icon=stat_data["icon"],
        )

    return GetServerIdShowAPI(
        id=server.id,
        name=server.name,
        ip=None if server.is_hide else server.ip,
        type=server.type,
        version=server.version,
        desc=server.desc,
        link=server.link,
        is_member=server.is_member,
        auth_mode=server.auth_mode,
        tags=server.tags,
        is_hide=server.is_hide,
        status=status_data,
        permission=permission,
        cover_url=cover_url,
    )


async def GetServer_by_id_editor(
    server_id: int, current_user: jwt_data = Depends(get_current_user)
) -> GetServerIdShowAPI | None:
    """查看服务器详细信息（详细信息）"""

    # 并发查询服务器和当前用户在该服务器中的角色
    server, user_server = await asyncio.gather(
        Server.get_or_none(id=server_id),
        UserServer.get_or_none(user=current_user.id, server=server_id),
    )

    user = await User.get_or_none(id=current_user.id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到该服务器"
        )

    # 获取服务器状态信息
    server_status = await ServerStatus.get_or_none(server=server)

    def no_permission():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="你咩有权限编辑它！它拒绝了你！",
        )

    # 用户权限
    permission = (
        SerRoleEnum.owner
        if user and user.role == RoleEnum.admin
        else (user_server.role if user_server else no_permission())
    )

    if not user_server and (user and user.role != RoleEnum.admin):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="你咩有权限编辑它！它拒绝了你！",
        )

    # 生成服务器状态数据
    status_data = None
    if server_status and server_status.stat_data:
        stat_data = server_status.stat_data
        status_data = GetServerStatusAPI(
            players=stat_data["players"],
            delay=stat_data["delay"],
            version=stat_data["version"],
            motd=Motd(
                plain=stat_data["motd"]["plain"],
                html=stat_data["motd"]["html"],
                minecraft=stat_data["motd"]["minecraft"],
                ansi=stat_data["motd"]["ansi"],
            ),
            icon=stat_data["icon"],
        )

    return GetServerIdShowAPI(
        id=server.id,
        name=server.name,
        ip=server.ip,
        type=server.type,
        version=server.version,
        desc=server.desc,
        link=server.link,
        is_member=server.is_member,
        auth_mode=server.auth_mode,
        tags=server.tags,
        is_hide=server.is_hide,
        status=status_data,
        permission=permission,
        cover_url=await get_server_cover_url(server),
    )


# 返回一个服务器的所有主人
async def GetServerOwners_by_id(server_id: int) -> GetServerManagers:
    # 查找是否有这个服务器
    server = await Server.get_or_none(id=server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="服务器不存在"
        )

    # 查找服务器的所有者和管理员
    owners = await UserServer.filter(server=server_id, role=SerRoleEnum.owner)
    admins = await UserServer.filter(server=server_id, role=SerRoleEnum.admin)

    async def to_user_base(user_server) -> UserBase:
        user = await user_server.user
        avatar_url = await get_user_avatar_url(user)
        return UserBase(
            id=user.id,
            display_name=user.display_name,
            role=user.role,
            is_active=user.is_active,
            avatar_url=avatar_url,
        )

    # 并发转换管理员和所有者列表
    admins_list, owners_list = await asyncio.gather(
        asyncio.gather(*(to_user_base(admin) for admin in admins)),
        asyncio.gather(*(to_user_base(owner) for owner in owners)),
    )

    return GetServerManagers(admins=admins_list, owners=owners_list)


async def GetGallerylist(server_id: int) -> GetServerGallerys:
    # 查找是否有这个服务器
    server = await Server.get_or_none(id=server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="服务器不存在"
        )

    return GetServerGallerys(
        id=server.id,
        name=server.name,
        gallerys_url=await get_server_gallerys_urls(server),
    )


async def AddGalleryImage(server_id, gallery_data: AddServerGallerys) -> None:
    # 查找是否有这个服务器
    server = await Server.get_or_none(id=server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="服务器不存在"
        )

    # 创建图库
    if not server.gallery:
        server.gallery = await Gallery.create()
        await server.save()
    await validate_name(gallery_data.title)
    await validate_description(gallery_data.description, min=3)
    # 创建图片
    image_hash = await validate_and_upload_gallery(gallery_data.image)
    await GalleryImage.create(
        title=gallery_data.title,
        description=gallery_data.description,
        image_hash=image_hash,
        gallery=await server.gallery,
    )


async def RemoveGalleryImage(server_id: int, image_id: int) -> None:
    # 查找是否有这个服务器
    server = await Server.get_or_none(id=server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="服务器不存在"
        )

    # 查找图库
    if not server.gallery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="无法找到关联图库"
        )
    gallery = await Gallery.get_or_none(id=server.gallery.id)
    if not gallery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图库不存在")

    # 查找图片
    image = await GalleryImage.get_or_none(id=image_id, gallery=gallery.id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")

    await image.delete()
