from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from PIL import Image

from app import logger
from app.file_storage.utils import upload_file_to_s3
from app.models import File, GalleryImage, Server
from app.services.servers.schemas import GallerySchema
from app.services.servers.stats_utils import get_server_stats
from app.services.utils import convert_to_webp


async def get_server_cover_url(server_data: Server) -> str | None:
    """获取用户封面 URL"""
    if not server_data.cover_hash:
        return None
    file_instance = await server_data.cover_hash
    return file_instance.file_path


async def get_server_gallerys_urls(server_data: Server) -> list[GallerySchema]:
    """获取服务器图库 URL 列表"""
    if not server_data.gallery:
        return []
    gallery = await server_data.gallery
    return [
        GallerySchema(
            id=image.id,
            title=image.title,
            description=image.description,
            image_url=await get_server_galleryimage_url(image),
        )
        for image in await gallery.images
    ]


async def get_server_galleryimage_url(gallery_model: GalleryImage) -> str:
    """获取服务器图库图片 URL"""
    file_instance = await gallery_model.image_hash
    return file_instance.file_path


async def validate_tags(tags: list[str]) -> None:
    """验证 tags 字段"""
    if len(tags) > 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="tags 数量不能超过 7 个"
        )
    for tag in tags:
        if not 1 <= len(tag) <= 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="tags 长度限制为 1~4"
            )


async def validate_name(name: str, min: int = 1, max: int = 20) -> None:
    """验证服务器名称字段"""
    if not min <= len(name) <= max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"名称长度限制为 {min}~{max}",
        )


async def validate_description(desc: str, min: int = 100) -> None:
    """验证简介字段"""
    if len(desc) < min:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"简介必须大于 {min} 字"
        )


async def validate_ip(ip: str, server_type: str) -> None:
    """验证服务器 IP 是否有效"""
    if not await get_server_stats(ip, server_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="服务器 IP 无效"
        )


async def validate_version(version: str) -> None:
    """验证版本字段"""
    if len(version) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="版本不能超过 20 字"
        )


async def validate_link(link: str) -> None:
    """验证链接字段"""
    import re

    if link and (not re.match(r"^https?:/{2}\w.+$", link) or len(link) > 255):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="link 不合法"
        )


async def validate_and_upload_cover(cover: UploadFile) -> File:
    """验证并上传封面文件"""
    if not isinstance(cover.filename, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="图片文件名无效"
        )
    content = await cover.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图片文件大小不能超过 5 MB",
        )
    try:
        cover.file.seek(0)  # 归零指针，确保后续读取正常
        image = Image.open(BytesIO(content))
        image.verify()  # 验证图片文件是否有效

        # 检查图片格式
        if image.format not in ["JPEG", "PNG", "WEBP"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="图片文件格式无效"
            )
        width, height = image.size
        expected_ratio = 16 / 9
        actual_ratio = width / height
        if abs(actual_ratio - expected_ratio) > 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="图片比例最好为 512*300"
            )

    except Exception as e:
        logger.error(f"Failed to open image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="图片文件无效"
        ) from e

    try:
        return (await upload_file_to_s3(convert_to_webp(content), "cover.webp"))[1]
    except Exception as e:
        logger.error(f"Failed to upload avatar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="图片上传失败"
        ) from e


async def validate_and_upload_gallery(cover: UploadFile) -> File:
    """验证并上传画廊图片文件"""
    if not isinstance(cover.filename, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="图片文件名无效"
        )
    content = await cover.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图片文件大小不能超过 5 MB",
        )

    try:
        cover.file.seek(0)  # 归零指针，确保后续读取正常
        image = Image.open(BytesIO(content))
        image.verify()  # 验证图片文件是否有效

        # 检查图片格式
        if image.format not in ["JPEG", "PNG", "WEBP"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="图片文件格式无效"
            )

    except Exception as e:
        logger.error(f"Failed to open image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="图片文件无效"
        ) from e

    try:
        return (await upload_file_to_s3(convert_to_webp(content), "cover.webp"))[1]
    except Exception as e:
        logger.error(f"Failed to upload avatar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="图片上传失败"
        ) from e
