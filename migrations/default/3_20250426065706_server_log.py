from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `server_log` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `changed_fields` JSON NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `server_id` INT NOT NULL,
    `user_id` INT,
    CONSTRAINT `fk_server_l_server_726896a2` FOREIGN KEY (`server_id`) REFERENCES `server` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_server_l_users_d6bb6d10` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `server_log`;"""
