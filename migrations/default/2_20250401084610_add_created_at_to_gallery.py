from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `gallery` ADD `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `gallery` DROP COLUMN `created_at`;"""
