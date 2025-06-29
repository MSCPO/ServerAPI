import asyncio

from app.log import logger
from app.models import File, GalleryImage, Server, User


async def remove_unused_files() -> None:
    """Delete File entries not referenced by any other model."""
    # collect currently used file hashes
    avatar_hashes = await User.exclude(avatar_hash=None).values_list(
        "avatar_hash_id", flat=True
    )
    cover_hashes = await Server.exclude(cover_hash=None).values_list(
        "cover_hash_id", flat=True
    )
    gallery_hashes = await GalleryImage.all().values_list("image_hash_id", flat=True)

    used_hashes = set(avatar_hashes) | set(cover_hashes) | set(gallery_hashes)

    all_hashes = await File.all().values_list("hash_value", flat=True)

    obsolete_hashes = set(all_hashes) - used_hashes

    for file_hash in obsolete_hashes:
        file_obj = await File.get(hash_value=file_hash)
        await file_obj.delete()
        logger.info(f"已删除未使用的文件: {file_hash}")


async def cleanup_unused_files(interval: int = 86400) -> None:
    """Periodically clean unused files."""
    while True:
        try:
            await remove_unused_files()
        except Exception as exc:
            logger.error(f"清理未使用文件时出错: {exc}")
        await asyncio.sleep(interval)
