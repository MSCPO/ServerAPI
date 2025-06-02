from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    HCAPTCHA_SITE_KEY: str
    HCAPTCHA_SECRET_KEY: str
    SECRET: str
    MIRROR_URL: str | None = None
    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET: str
    FROM_EMAIL: str
    FROM_EMAIL_PASSWORD: str
    SMTP_SERVER: str
    SMTP_PORT: int
    MEILI_URL: str
    MEILI_API_KEY: str
    MEILI_INDEX: str
    REDIS_HOST: str
    REDIS_PORT: int

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore
