from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    RECAPTCHA_SITE_KEY: str
    RECAPTCHA_SECRET_KEY: str
    SECRET: str
    MIRROR_URL: str | None = None
    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET: str

    class Config:
        env_file = ".env"


settings = Settings()
