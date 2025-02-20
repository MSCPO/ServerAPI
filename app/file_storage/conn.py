from aioboto3 import Session

from app.config import settings

session = Session(
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
)

s3_client = session.client("s3", endpoint_url=settings.S3_ENDPOINT_URL)
