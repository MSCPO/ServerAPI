from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users` MODIFY COLUMN `last_login_ip` VARCHAR(45);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users` MODIFY COLUMN `last_login_ip` VARCHAR(15);"""
