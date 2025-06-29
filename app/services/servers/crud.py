import asyncio
import random

from fastapi import HTTPException, UploadFile, status

from app.models import (
    Gallery,
    GalleryImage,
    RoleEnum,
    SerRoleEnum,
    Server,
    ServerStatus,
    User,
    UserServer,
)
from app.services.auth.schemas import JWTData
from app.services.servers.schemas import (
    GallerySchema,
    GetServerManagers,
    GetServerStatusAPI,
    Motd,
    ServerDetail,
    ServerFilter,
    ServerGallery,
    ServerList,
    ServerTotalPlayers,
    UpdateServerRequest,
    UserBase,
)
from app.services.servers.utils import (
    get_server_cover_url,
    get_server_gallerys_urls,
    validate_and_upload_cover,
    validate_and_upload_gallery,
    validate_description,
    validate_ip,
    validate_link,
    validate_name,
    validate_tags,
    validate_version,
)
from app.services.user.utils import get_user_avatar_url

# 简单的内存缓存用于减少重复查询
_server_cache = {}
_cache_ttl = 60  # 缓存60秒


def _get_cache_key(prefix: str, *args) -> str:
    """生成缓存键"""
    return f"{prefix}:{':'.join(str(arg) for arg in args)}"


def _is_cache_valid(timestamp: float) -> bool:
    """检查缓存是否有效"""
    import time

    return time.time() - timestamp < _cache_ttl


def _get_cached_data(key: str):
    """获取缓存数据"""
    if key in _server_cache:
        data, timestamp = _server_cache[key]
        if _is_cache_valid(timestamp):
            return data
        else:
            del _server_cache[key]
    return None


def _set_cached_data(key: str, data):
    """设置缓存数据"""
    import time

    _server_cache[key] = (data, time.time())


# 性能优化: 添加数据库查询缓存清理函数
def clear_server_cache():
    """清理服务器缓存"""
    global _server_cache
    _server_cache.clear()


# 性能优化: 批量预热缓存
async def warmup_cache(server_ids: list[int]):
    """预热服务器缓存"""
    servers = await Server.filter(id__in=server_ids).prefetch_related("cover_hash")
    statuses = (
        await ServerStatus.filter(server_id__in=server_ids)
        .order_by("-timestamp")
        .prefetch_related("server")
    )

    # 为每个服务器创建状态映射
    status_map = {}
    for server_status in statuses:
        # 使用预加载的 server 关系
        server_id = server_status.server.id
        if server_id not in status_map:
            status_map[server_id] = server_status

    # 缓存数据
    for server in servers:
        cache_key = _get_cache_key("server_basic", server.id)
        server_status = status_map.get(server.id)
        _set_cached_data(cache_key, (server, server_status))


async def GetServers(
    filter: ServerFilter,
    limit: int | None = None,
    offset: int = 0,
    is_random: bool = True,
    seed: int | None = None,
    user: int | None = None,
) -> ServerList:
    # 并发查询服务器总数和成员数
    total_member_task = Server.filter(is_member=True).count()

    # 构建查询，预取相关数据以减少查询次数
    query = Server.all().prefetch_related("cover_hash")

    # 应用过滤条件
    if filter.is_member:
        query = query.filter(is_member=filter.is_member)

    if filter.modes:
        query = query.filter(type=filter.modes)

    if filter.authModes:
        query = query.filter(auth_mode__in=filter.authModes)

    if filter.tags:
        # 对标签进行过滤 (标签是数组字段，需要特殊处理)
        # 这里假设tags字段是JSON数组，查询包含任意指定标签的服务器
        for tag in filter.tags:
            query = query.filter(tags__contains=tag)

    # 并发获取过滤后的服务器和成员总数
    all_servers, total_member = await asyncio.gather(query, total_member_task)

    # 随机排序
    if is_random:
        if seed is None:
            seed = random.randint(0, 2**32 - 1)
        random.seed(seed)
        random.shuffle(all_servers)

    # 批量获取用户权限信息和服务器状态
    user_servers_map = {}
    user_info = None
    server_statuses_map = {}

    if user:
        user_info = await User.get_or_none(id=user)
        server_ids = [server.id for server in all_servers]
        user_servers = await UserServer.filter(
            user=user, server_id__in=server_ids
        ).prefetch_related("server")
        user_servers_map = {us.server.id: us.role for us in user_servers}

    # 批量获取服务器状态
    if all_servers:
        server_ids = [server.id for server in all_servers]
        server_statuses = (
            await ServerStatus.filter(server_id__in=server_ids)
            .prefetch_related("server")
            .order_by("-timestamp")
        )
        # 创建服务器ID到最新状态的映射
        for status in server_statuses:
            if status.server.id not in server_statuses_map:
                server_statuses_map[status.server.id] = status

    # 批量处理服务器详情，避免N+1查询
    server_list = []
    cover_url_tasks = []

    for server in all_servers:
        # 确定用户权限
        permission = (
            SerRoleEnum.owner
            if user_info and user_info.role == "admin"
            else user_servers_map.get(server.id, "guest")
        )

        # 处理服务器状态
        status_data = None
        server_status = server_statuses_map.get(server.id)
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

        # 准备封面URL任务
        cover_url_tasks.append(get_server_cover_url(server))

        server_detail = ServerDetail(
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
            cover_url=None,  # 稍后批量设置
        )
        server_list.append(server_detail)

    # 批量获取封面URL
    if cover_url_tasks:
        cover_urls = await asyncio.gather(*cover_url_tasks)
        for i, cover_url in enumerate(cover_urls):
            server_list[i].cover_url = cover_url

    total_servers = len(server_list)

    # 根据状态排序
    server_list.sort(key=lambda x: x.status is None)

    # 应用分页
    server_list = server_list[offset:]
    if limit is not None:
        server_list = server_list[:limit]

    return ServerList(
        server_list=server_list,
        total_member=total_member,
        total=total_servers,
        random_seed=seed,
    )


# 2. GetServer_by_id 返回 ServerDetail
async def GetServer_by_id(server_id: int, user: int | None) -> None | ServerDetail:
    # 检查缓存（仅对没有用户特定信息的基础数据进行缓存）
    cache_key = _get_cache_key("server_basic", server_id)

    if cached_server_data := _get_cached_data(cache_key):
        server, server_status = cached_server_data
    else:
        # 查询服务器是否存在，预取封面信息
        server = await Server.get_or_none(id=server_id).prefetch_related("cover_hash")
        if not server:
            return None

        # 获取最新的服务器状态
        server_status = (
            await ServerStatus.filter(server=server).order_by("-timestamp").first()
        )

        # 缓存基础数据（不包含用户相关信息）
        _set_cached_data(cache_key, (server, server_status))

    # 用户相关查询不缓存，因为是用户特定的
    user_server_task = (
        UserServer.get_or_none(user=user, server=server_id)
        if user
        else asyncio.sleep(0, result=None)
    )
    user_info_task = (
        User.get_or_none(id=user) if user else asyncio.sleep(0, result=None)
    )
    cover_task = get_server_cover_url(server)

    user_server, user_info, cover_url = await asyncio.gather(
        user_server_task, user_info_task, cover_task
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

    return ServerDetail(
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


# 3. GetServer_by_id_editor 返回 ServerDetail
async def GetServer_by_id_editor(server_id: int, current_user) -> ServerDetail | None:
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

    return ServerDetail(
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

    # 批量查找服务器的所有者和管理员，预取用户信息
    owners_task = UserServer.filter(
        server=server_id, role=SerRoleEnum.owner
    ).prefetch_related("user")
    admins_task = UserServer.filter(
        server=server_id, role=SerRoleEnum.admin
    ).prefetch_related("user")

    owners, admins = await asyncio.gather(owners_task, admins_task)

    # 批量获取头像URL
    all_users = [us.user for us in owners + admins]
    avatar_tasks = [get_user_avatar_url(user) for user in all_users]
    avatar_urls = await asyncio.gather(*avatar_tasks)

    # 创建用户ID到头像URL的映射
    avatar_map = {
        user.id: avatar_url for user, avatar_url in zip(all_users, avatar_urls)
    }

    # 转换为UserBase对象
    def to_user_base(user_server) -> UserBase:
        user = user_server.user
        return UserBase(
            id=user.id,
            display_name=user.display_name,
            role=user.role,
            is_active=user.is_active,
            avatar_url=avatar_map[user.id],
        )

    # 转换管理员和所有者列表
    admins_list = [to_user_base(admin) for admin in admins]
    owners_list = [to_user_base(owner) for owner in owners]

    return GetServerManagers(admins=admins_list, owners=owners_list)


# 4. GetGallerylist 返回 ServerGallery
async def GetGallerylist(server_id: int) -> ServerGallery:
    # 查找是否有这个服务器
    server = await Server.get_or_none(id=server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="服务器不存在"
        )

    return ServerGallery(
        id=server.id,
        name=server.name,
        gallerys_url=await get_server_gallerys_urls(server),
    )


# 5. AddGalleryImage 参数类型 GallerySchema
async def AddGalleryImage(server_id, gallery_data: GallerySchema) -> None:
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
    if not isinstance(gallery_data.image, UploadFile):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="图片文件不能为空"
        )
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
    gallery_instance = await server.gallery.first()
    gallery = (
        await Gallery.get_or_none(id=gallery_instance.id) if gallery_instance else None
    )
    if not gallery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图库不存在")

    # 查找图片
    image = await GalleryImage.get_or_none(id=image_id, gallery=gallery.id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")

    await image.delete()


# 获取所有服务器的玩家总和
async def GetAllPlayersNum() -> ServerTotalPlayers:
    # 仅选择需要的字段，减少数据传输
    server_statuses = await ServerStatus.all().only("stat_data")

    total_players = sum(
        server_status.stat_data["players"]["online"]
        for server_status in server_statuses
        if server_status
        and server_status.stat_data
        and "players" in server_status.stat_data
    )

    return ServerTotalPlayers(total_players=total_players)


# 新增 update_server_by_id 方法，封装原有 update_server 逻辑


async def update_server_by_id(
    server_id: int, update_data: UpdateServerRequest, current_user: JWTData
):
    from fastapi import HTTPException, status

    from app.models import Server, User
    from app.services.servers.crud import GetServer_by_id_editor

    await GetServer_by_id_editor(server_id, current_user)
    server = await Server.get_or_none(id=server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到该服务器"
        )
    if not update_data.name and not update_data.ip and not update_data.desc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="更新字段不能为空"
        )
    await validate_name(update_data.name)
    await validate_description(update_data.desc)
    await validate_tags(update_data.tags)
    await validate_ip(update_data.ip, server.type)
    await validate_version(update_data.version)
    await validate_link(update_data.link)
    if update_data.cover:
        cover_hash = await validate_and_upload_cover(update_data.cover)
        server.cover_hash = cover_hash
    server.name = update_data.name
    server.ip = update_data.ip
    server.desc = update_data.desc
    server.tags = update_data.tags
    server.version = update_data.version
    server.link = update_data.link
    await server.save_with_user(await User.get(id=current_user.id))
    return await GetServer_by_id_editor(server_id, current_user)
