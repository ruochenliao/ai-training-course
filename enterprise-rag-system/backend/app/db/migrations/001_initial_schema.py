"""
初始数据库架构迁移
"""

from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- 创建用户表
        CREATE TABLE IF NOT EXISTS `users` (
            `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `username` VARCHAR(50) NOT NULL UNIQUE,
            `email` VARCHAR(100) NOT NULL UNIQUE,
            `password_hash` VARCHAR(255) NOT NULL,
            `full_name` VARCHAR(100),
            `avatar` VARCHAR(255),
            `phone` VARCHAR(20),
            `status` VARCHAR(20) NOT NULL DEFAULT 'active',
            `is_superuser` BOOL NOT NULL DEFAULT 0,
            `is_active` BOOL NOT NULL DEFAULT 1,
            `is_deleted` BOOL NOT NULL DEFAULT 0,
            `failed_login_attempts` INT NOT NULL DEFAULT 0,
            `locked_until` DATETIME(6),
            `password_changed_at` DATETIME(6),
            `language` VARCHAR(10) NOT NULL DEFAULT 'zh-CN',
            `timezone` VARCHAR(50) NOT NULL DEFAULT 'Asia/Shanghai',
            `theme` VARCHAR(20) NOT NULL DEFAULT 'light',
            `last_login_at` DATETIME(6),
            `last_login_ip` VARCHAR(45),
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            INDEX `idx_users_username_email` (`username`, `email`),
            INDEX `idx_users_status_deleted` (`status`, `is_deleted`),
            INDEX `idx_users_created_at` (`created_at`)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

        -- 创建角色表
        CREATE TABLE IF NOT EXISTS `roles` (
            `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `name` VARCHAR(50) NOT NULL UNIQUE,
            `display_name` VARCHAR(100) NOT NULL,
            `description` TEXT,
            `is_system` BOOL NOT NULL DEFAULT 0,
            `is_active` BOOL NOT NULL DEFAULT 1,
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            INDEX `idx_roles_name` (`name`),
            INDEX `idx_roles_active` (`is_active`)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

        -- 创建权限表
        CREATE TABLE IF NOT EXISTS `permissions` (
            `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `name` VARCHAR(100) NOT NULL UNIQUE,
            `display_name` VARCHAR(100) NOT NULL,
            `description` TEXT,
            `resource` VARCHAR(50) NOT NULL,
            `action` VARCHAR(50) NOT NULL,
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            INDEX `idx_permissions_resource_action` (`resource`, `action`)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

        -- 创建用户角色关联表
        CREATE TABLE IF NOT EXISTS `user_roles` (
            `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `user_id` INT NOT NULL,
            `role_id` INT NOT NULL,
            `assigned_by` INT,
            `assigned_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            `expires_at` DATETIME(6),
            FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
            FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE,
            FOREIGN KEY (`assigned_by`) REFERENCES `users` (`id`) ON DELETE SET NULL,
            UNIQUE KEY `uk_user_role` (`user_id`, `role_id`),
            INDEX `idx_user_roles_user` (`user_id`),
            INDEX `idx_user_roles_role` (`role_id`)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

        -- 创建角色权限关联表
        CREATE TABLE IF NOT EXISTS `role_permissions` (
            `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `role_id` INT NOT NULL,
            `permission_id` INT NOT NULL,
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE,
            FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`) ON DELETE CASCADE,
            UNIQUE KEY `uk_role_permission` (`role_id`, `permission_id`)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

        -- 创建知识库表
        CREATE TABLE IF NOT EXISTS `knowledge_bases` (
            `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `name` VARCHAR(100) NOT NULL,
            `description` TEXT,
            `owner_id` INT NOT NULL,
            `is_public` BOOL NOT NULL DEFAULT 0,
            `status` VARCHAR(20) NOT NULL DEFAULT 'active',
            `settings` JSON,
            `document_count` INT NOT NULL DEFAULT 0,
            `total_size` BIGINT NOT NULL DEFAULT 0,
            `last_updated_at` DATETIME(6),
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
            INDEX `idx_kb_owner` (`owner_id`),
            INDEX `idx_kb_status` (`status`),
            INDEX `idx_kb_public` (`is_public`)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

        -- 创建文档表
        CREATE TABLE IF NOT EXISTS `documents` (
            `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `knowledge_base_id` INT NOT NULL,
            `filename` VARCHAR(255) NOT NULL,
            `original_filename` VARCHAR(255) NOT NULL,
            `file_path` VARCHAR(500),
            `file_size` BIGINT NOT NULL DEFAULT 0,
            `file_type` VARCHAR(50),
            `mime_type` VARCHAR(100),
            `content` LONGTEXT,
            `metadata` JSON,
            `status` VARCHAR(20) NOT NULL DEFAULT 'uploaded',
            `processing_status` VARCHAR(20) NOT NULL DEFAULT 'pending',
            `error_message` TEXT,
            `page_count` INT DEFAULT 0,
            `word_count` INT DEFAULT 0,
            `chunk_count` INT DEFAULT 0,
            `uploaded_by` INT NOT NULL,
            `processed_at` DATETIME(6),
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            FOREIGN KEY (`knowledge_base_id`) REFERENCES `knowledge_bases` (`id`) ON DELETE CASCADE,
            FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`id`) ON DELETE CASCADE,
            INDEX `idx_docs_kb` (`knowledge_base_id`),
            INDEX `idx_docs_status` (`status`),
            INDEX `idx_docs_processing` (`processing_status`),
            INDEX `idx_docs_uploader` (`uploaded_by`),
            INDEX `idx_docs_created` (`created_at`)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

        -- 创建文档分块表
        CREATE TABLE IF NOT EXISTS `document_chunks` (
            `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `document_id` INT NOT NULL,
            `knowledge_base_id` INT NOT NULL,
            `chunk_index` INT NOT NULL,
            `content` LONGTEXT NOT NULL,
            `metadata` JSON,
            `token_count` INT DEFAULT 0,
            `embedding_status` VARCHAR(20) NOT NULL DEFAULT 'pending',
            `vector_id` VARCHAR(100),
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE CASCADE,
            FOREIGN KEY (`knowledge_base_id`) REFERENCES `knowledge_bases` (`id`) ON DELETE CASCADE,
            INDEX `idx_chunks_doc` (`document_id`),
            INDEX `idx_chunks_kb` (`knowledge_base_id`),
            INDEX `idx_chunks_embedding` (`embedding_status`),
            INDEX `idx_chunks_vector` (`vector_id`)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

        -- 创建对话表
        CREATE TABLE IF NOT EXISTS `conversations` (
            `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `user_id` INT NOT NULL,
            `knowledge_base_id` INT,
            `title` VARCHAR(200),
            `status` VARCHAR(20) NOT NULL DEFAULT 'active',
            `settings` JSON,
            `message_count` INT NOT NULL DEFAULT 0,
            `last_message_at` DATETIME(6),
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
            FOREIGN KEY (`knowledge_base_id`) REFERENCES `knowledge_bases` (`id`) ON DELETE SET NULL,
            INDEX `idx_conv_user` (`user_id`),
            INDEX `idx_conv_kb` (`knowledge_base_id`),
            INDEX `idx_conv_status` (`status`),
            INDEX `idx_conv_last_msg` (`last_message_at`)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

        -- 创建消息表
        CREATE TABLE IF NOT EXISTS `messages` (
            `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `conversation_id` INT NOT NULL,
            `role` VARCHAR(20) NOT NULL,
            `content` LONGTEXT NOT NULL,
            `metadata` JSON,
            `tokens` INT DEFAULT 0,
            `model` VARCHAR(50),
            `finish_reason` VARCHAR(50),
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`) ON DELETE CASCADE,
            INDEX `idx_msg_conv` (`conversation_id`),
            INDEX `idx_msg_role` (`role`),
            INDEX `idx_msg_created` (`created_at`)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

        -- 创建系统配置表
        CREATE TABLE IF NOT EXISTS `system_configs` (
            `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `key` VARCHAR(100) NOT NULL UNIQUE,
            `value` LONGTEXT,
            `description` TEXT,
            `type` VARCHAR(20) NOT NULL DEFAULT 'string',
            `is_public` BOOL NOT NULL DEFAULT 0,
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            INDEX `idx_config_key` (`key`),
            INDEX `idx_config_public` (`is_public`)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

        -- 创建审计日志表
        CREATE TABLE IF NOT EXISTS `audit_logs` (
            `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `user_id` INT,
            `action` VARCHAR(50) NOT NULL,
            `resource_type` VARCHAR(50),
            `resource_id` VARCHAR(50),
            `details` JSON,
            `ip_address` VARCHAR(45),
            `user_agent` TEXT,
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
            INDEX `idx_audit_user` (`user_id`),
            INDEX `idx_audit_action` (`action`),
            INDEX `idx_audit_resource` (`resource_type`, `resource_id`),
            INDEX `idx_audit_created` (`created_at`)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `audit_logs`;
        DROP TABLE IF EXISTS `system_configs`;
        DROP TABLE IF EXISTS `messages`;
        DROP TABLE IF EXISTS `conversations`;
        DROP TABLE IF EXISTS `document_chunks`;
        DROP TABLE IF EXISTS `documents`;
        DROP TABLE IF EXISTS `knowledge_bases`;
        DROP TABLE IF EXISTS `role_permissions`;
        DROP TABLE IF EXISTS `user_roles`;
        DROP TABLE IF EXISTS `permissions`;
        DROP TABLE IF EXISTS `roles`;
        DROP TABLE IF EXISTS `users`;
    """
