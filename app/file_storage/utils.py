import uuid

from app.config import settings
from app.file_storage.conn import session
from app.models import File


def get_file_extension(filename: str) -> str:
    last_dot_pos = filename.rfind(".")

    if last_dot_pos == -1:
        return ""

    last_extension = filename[last_dot_pos:]

    if last_extension.count(".") > 1:
        return filename[last_dot_pos:]

    return last_extension


async def upload_file_to_s3(file_content: bytes, file_name: str) -> tuple[str, File]:
    file_hash = File.generate_file_hash(file_content)
    s3_object_name = f"uploads/{uuid.uuid4()!s}{get_file_extension(file_name)}"

    file = await File.get_or_none(hash_value=file_hash)
    if file:
        return (
            f"{settings.S3_ENDPOINT_URL}/{settings.S3_SECRET_KEY}/{s3_object_name}",
            file,
        )

    async with session.resource("s3", endpoint_url=settings.S3_ENDPOINT_URL) as s3:
        bucket = await s3.Bucket(settings.S3_BUCKET)
        await bucket.put_object(Key=s3_object_name, Body=file_content)

    file_object = await File.create(
        hash_value=file_hash,
        file_path=f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET}/{s3_object_name}",
    )

    return (
        f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET}/{s3_object_name}",
        file_object,
    )
