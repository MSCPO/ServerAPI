import asyncio

from tortoise.signals import post_delete

from app.config import settings
from app.file_storage.conn import session
from app.file_storage.models import File
from app.log import logger


async def _list_bucket_keys() -> list[str]:
    async with session.resource("s3", endpoint_url=settings.S3_ENDPOINT_URL) as s3:
        bucket = await s3.Bucket(settings.S3_BUCKET)
        return [obj.key async for obj in bucket.objects.all()]


@post_delete(File)
async def sync_bucket_with_db() -> None:
    keys = await _list_bucket_keys()
    bucket_paths = {
        f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET}/{key}": key for key in keys
    }

    db_files = await File.all()
    db_paths = {file.file_path for file in db_files}

    # S3 中存在但数据库中没有的路径
    obsolete_paths = set(bucket_paths.keys()) - db_paths

    async with session.resource("s3", endpoint_url=settings.S3_ENDPOINT_URL) as s3:
        for path in obsolete_paths:
            object_key = bucket_paths[path]
            obj = await s3.Object(settings.S3_BUCKET, object_key)
            await obj.delete()
            logger.info(f"已从 S3 删除多余对象: {object_key}")


async def sync_bucket_periodically(interval: int = 300) -> None:
    while True:
        try:
            await sync_bucket_with_db()
        except Exception as exc:
            logger.error(f"同步桶和数据库时出错: {exc}")
        await asyncio.sleep(interval)
