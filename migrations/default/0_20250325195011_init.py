from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `files` (
    `hash_value` VARCHAR(64) NOT NULL PRIMARY KEY,
    `file_path` VARCHAR(255) NOT NULL UNIQUE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `server` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `type` VARCHAR(50) NOT NULL,
    `version` VARCHAR(20) NOT NULL,
    `desc` LONGTEXT NOT NULL,
    `link` VARCHAR(255) NOT NULL,
    `ip` VARCHAR(255) NOT NULL,
    `is_member` BOOL NOT NULL DEFAULT 0,
    `is_hide` BOOL NOT NULL DEFAULT 0,
    `auth_mode` VARCHAR(50) NOT NULL,
    `tags` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `server_stats` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `timestamp` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `stat_data` JSON,
    `server_id` INT NOT NULL,
    CONSTRAINT `fk_server_s_server_c9e4fa0b` FOREIGN KEY (`server_id`) REFERENCES `server` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `username` VARCHAR(32) NOT NULL UNIQUE,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `display_name` VARCHAR(16) NOT NULL,
    `hashed_password` VARCHAR(60) NOT NULL,
    `role` VARCHAR(5) NOT NULL COMMENT 'user: user\nadmin: admin' DEFAULT 'user',
    `is_active` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `last_login` DATETIME(6),
    `last_login_ip` VARCHAR(15),
    `avatar_hash_id` VARCHAR(64),
    CONSTRAINT `fk_users_files_8014f763` FOREIGN KEY (`avatar_hash_id`) REFERENCES `files` (`hash_value`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `ban_records` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `ban_type` VARCHAR(8) NOT NULL COMMENT 'mute: mute\nban: ban\ntemp_ban: temp_ban',
    `reason` LONGTEXT,
    `started_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `ended_at` DATETIME(6),
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_ban_reco_users_58e85cdb` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user_server` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `role` VARCHAR(50) NOT NULL COMMENT 'owner: owner\nadmin: admin',
    `server_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_user_ser_server_3150d958` FOREIGN KEY (`server_id`) REFERENCES `server` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_user_ser_users_f0afdb14` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `ticket` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(255) NOT NULL,
    `description` LONGTEXT,
    `status` SMALLINT NOT NULL COMMENT 'CANCELED: 0\nPENDING: 1\nUNDER_REVIEW: 2\nRESOLVED: 3\nACCEPTED: 4\nINVALID: 5' DEFAULT 1,
    `priority` SMALLINT NOT NULL COMMENT 'LOW: 1\nMEDIUM: 2\nHIGH: 3' DEFAULT 2,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `reported_content_id` INT,
    `report_reason` LONGTEXT,
    `admin_remark` LONGTEXT,
    `assignee_id` INT,
    `creator_id` INT NOT NULL,
    `reported_user_id` INT,
    `server_id` INT,
    CONSTRAINT `fk_ticket_users_01f9e99c` FOREIGN KEY (`assignee_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_ticket_users_b9461ef3` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ticket_users_ed45e3eb` FOREIGN KEY (`reported_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_ticket_server_fd880816` FOREIGN KEY (`server_id`) REFERENCES `server` (`id`) ON DELETE SET NULL,
    KEY `idx_ticket_reporte_6d5fde` (`reported_content_id`)
) CHARACTER SET utf8mb4 COMMENT='工单模型，用于存储工单的信息，包括状态、优先级、处理人等';
CREATE TABLE IF NOT EXISTS `ticket_log` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `old_status` SMALLINT NOT NULL COMMENT 'CANCELED: 0\nPENDING: 1\nUNDER_REVIEW: 2\nRESOLVED: 3\nACCEPTED: 4\nINVALID: 5',
    `new_status` SMALLINT NOT NULL COMMENT 'CANCELED: 0\nPENDING: 1\nUNDER_REVIEW: 2\nRESOLVED: 3\nACCEPTED: 4\nINVALID: 5',
    `changed_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `changed_by_id` INT NOT NULL,
    `ticket_id` INT NOT NULL,
    CONSTRAINT `fk_ticket_l_users_e4ae2bab` FOREIGN KEY (`changed_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ticket_l_ticket_95d1de4c` FOREIGN KEY (`ticket_id`) REFERENCES `ticket` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='工单日志模型，用于记录工单状态变更的日志';
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
