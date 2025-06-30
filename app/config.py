from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./test.db"
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30
    HCAPTCHA_SITE_KEY: str = "your-hcaptcha-site-key"
    HCAPTCHA_SECRET_KEY: str = "your-hcaptcha-secret-key"
    SECRET: str = "your-secret"
    MIRROR_URL: str | None = None
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "your-s3-access-key"
    S3_SECRET_KEY: str = "your-s3-secret-key"
    S3_BUCKET: str = "your-s3-bucket"
    FROM_EMAIL: str = "your@email.com"
    FROM_EMAIL_PASSWORD: str = "your-email-password"
    SMTP_SERVER: str = "smtp.example.com"
    SMTP_PORT: int = 587
    MEILI_URL: str = "http://localhost:7700"
    MEILI_API_KEY: str = "your-meili-api-key"
    MEILI_INDEX: str = "your-meili-index"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    class Config:
        env_file = ".env"


settings = Settings()
