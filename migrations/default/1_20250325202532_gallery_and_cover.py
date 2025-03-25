from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `gallery` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `gallery_image` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(255) NOT NULL,
    `description` LONGTEXT NOT NULL,
    `gallery_id` INT NOT NULL,
    `image_hash_id` VARCHAR(64) NOT NULL,
    CONSTRAINT `fk_gallery__gallery_5df5692a` FOREIGN KEY (`gallery_id`) REFERENCES `gallery` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_gallery__files_43d8eb4b` FOREIGN KEY (`image_hash_id`) REFERENCES `files` (`hash_value`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        ALTER TABLE `server` ADD `cover_hash_id` VARCHAR(64);
        ALTER TABLE `server` ADD `gallery_id` INT;
        ALTER TABLE `server` ADD CONSTRAINT `fk_server_gallery_6d97a820` FOREIGN KEY (`gallery_id`) REFERENCES `gallery` (`id`) ON DELETE CASCADE;
        ALTER TABLE `server` ADD CONSTRAINT `fk_server_files_e469ed0d` FOREIGN KEY (`cover_hash_id`) REFERENCES `files` (`hash_value`) ON DELETE SET NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `server` DROP FOREIGN KEY `fk_server_files_e469ed0d`;
        ALTER TABLE `server` DROP FOREIGN KEY `fk_server_gallery_6d97a820`;
        ALTER TABLE `server` DROP COLUMN `cover_hash_id`;
        ALTER TABLE `server` DROP COLUMN `gallery_id`;
        DROP TABLE IF EXISTS `gallery_image`;
        DROP TABLE IF EXISTS `gallery`;"""
