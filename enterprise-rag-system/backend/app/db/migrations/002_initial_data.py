"""
初始数据迁移
"""

from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- 插入默认角色
        INSERT INTO `roles` (`name`, `display_name`, `description`, `is_system`) VALUES
        ('superuser', '超级管理员', '系统超级管理员，拥有所有权限', 1),
        ('admin', '管理员', '系统管理员，拥有大部分管理权限', 1),
        ('knowledge_manager', '知识库管理员', '负责知识库和文档管理', 1),
        ('user', '普通用户', '普通用户，可以使用知识库进行问答', 1),
        ('guest', '访客', '访客用户，只能查看公开内容', 1);

        -- 插入默认权限
        INSERT INTO `permissions` (`name`, `display_name`, `description`, `resource`, `action`) VALUES
        -- 用户管理权限
        ('user.create', '创建用户', '创建新用户账户', 'user', 'create'),
        ('user.read', '查看用户', '查看用户信息', 'user', 'read'),
        ('user.update', '更新用户', '更新用户信息', 'user', 'update'),
        ('user.delete', '删除用户', '删除用户账户', 'user', 'delete'),
        ('user.manage_roles', '管理用户角色', '分配和移除用户角色', 'user', 'manage_roles'),
        
        -- 角色权限管理
        ('role.create', '创建角色', '创建新角色', 'role', 'create'),
        ('role.read', '查看角色', '查看角色信息', 'role', 'read'),
        ('role.update', '更新角色', '更新角色信息', 'role', 'update'),
        ('role.delete', '删除角色', '删除角色', 'role', 'delete'),
        ('role.manage_permissions', '管理角色权限', '分配和移除角色权限', 'role', 'manage_permissions'),
        
        -- 知识库管理权限
        ('knowledge_base.create', '创建知识库', '创建新知识库', 'knowledge_base', 'create'),
        ('knowledge_base.read', '查看知识库', '查看知识库信息', 'knowledge_base', 'read'),
        ('knowledge_base.update', '更新知识库', '更新知识库信息', 'knowledge_base', 'update'),
        ('knowledge_base.delete', '删除知识库', '删除知识库', 'knowledge_base', 'delete'),
        ('knowledge_base.manage', '管理知识库', '完全管理知识库', 'knowledge_base', 'manage'),
        
        -- 文档管理权限
        ('document.create', '上传文档', '上传新文档', 'document', 'create'),
        ('document.read', '查看文档', '查看文档内容', 'document', 'read'),
        ('document.update', '更新文档', '更新文档信息', 'document', 'update'),
        ('document.delete', '删除文档', '删除文档', 'document', 'delete'),
        ('document.process', '处理文档', '处理和解析文档', 'document', 'process'),
        
        -- 对话管理权限
        ('conversation.create', '创建对话', '创建新对话', 'conversation', 'create'),
        ('conversation.read', '查看对话', '查看对话记录', 'conversation', 'read'),
        ('conversation.update', '更新对话', '更新对话信息', 'conversation', 'update'),
        ('conversation.delete', '删除对话', '删除对话记录', 'conversation', 'delete'),
        
        -- 系统管理权限
        ('system.config', '系统配置', '管理系统配置', 'system', 'config'),
        ('system.monitor', '系统监控', '查看系统监控信息', 'system', 'monitor'),
        ('system.logs', '系统日志', '查看系统日志', 'system', 'logs'),
        ('system.backup', '系统备份', '执行系统备份', 'system', 'backup'),
        
        -- 任务管理权限
        ('task.read', '查看任务', '查看任务状态', 'task', 'read'),
        ('task.manage', '管理任务', '管理和控制任务', 'task', 'manage'),
        
        -- 图谱管理权限
        ('graph.read', '查看图谱', '查看知识图谱', 'graph', 'read'),
        ('graph.manage', '管理图谱', '管理知识图谱', 'graph', 'manage');

        -- 为超级管理员角色分配所有权限
        INSERT INTO `role_permissions` (`role_id`, `permission_id`)
        SELECT r.id, p.id
        FROM `roles` r, `permissions` p
        WHERE r.name = 'superuser';

        -- 为管理员角色分配管理权限（除了用户删除和系统备份）
        INSERT INTO `role_permissions` (`role_id`, `permission_id`)
        SELECT r.id, p.id
        FROM `roles` r, `permissions` p
        WHERE r.name = 'admin'
        AND p.name NOT IN ('user.delete', 'system.backup');

        -- 为知识库管理员分配知识库和文档相关权限
        INSERT INTO `role_permissions` (`role_id`, `permission_id`)
        SELECT r.id, p.id
        FROM `roles` r, `permissions` p
        WHERE r.name = 'knowledge_manager'
        AND p.resource IN ('knowledge_base', 'document', 'graph', 'task')
        AND p.action IN ('create', 'read', 'update', 'delete', 'manage', 'process');

        -- 为普通用户分配基本权限
        INSERT INTO `role_permissions` (`role_id`, `permission_id`)
        SELECT r.id, p.id
        FROM `roles` r, `permissions` p
        WHERE r.name = 'user'
        AND (
            (p.resource = 'knowledge_base' AND p.action = 'read') OR
            (p.resource = 'document' AND p.action IN ('create', 'read')) OR
            (p.resource = 'conversation' AND p.action IN ('create', 'read', 'update', 'delete')) OR
            (p.resource = 'graph' AND p.action = 'read')
        );

        -- 为访客分配只读权限
        INSERT INTO `role_permissions` (`role_id`, `permission_id`)
        SELECT r.id, p.id
        FROM `roles` r, `permissions` p
        WHERE r.name = 'guest'
        AND p.action = 'read'
        AND p.resource IN ('knowledge_base', 'document', 'conversation');

        -- 创建默认超级管理员用户
        INSERT INTO `users` (
            `username`, 
            `email`, 
            `password_hash`, 
            `full_name`, 
            `is_superuser`, 
            `is_active`,
            `status`
        ) VALUES (
            'admin',
            'admin@example.com',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5/Qe2', -- password: admin123
            '系统管理员',
            1,
            1,
            'active'
        );

        -- 为默认管理员分配超级管理员角色
        INSERT INTO `user_roles` (`user_id`, `role_id`)
        SELECT u.id, r.id
        FROM `users` u, `roles` r
        WHERE u.username = 'admin' AND r.name = 'superuser';

        -- 插入默认系统配置
        INSERT INTO `system_configs` (`key`, `value`, `description`, `type`, `is_public`) VALUES
        ('system.name', '企业级RAG知识库系统', '系统名称', 'string', 1),
        ('system.version', '1.0.0', '系统版本', 'string', 1),
        ('system.description', '基于多智能体协作的企业级知识库系统', '系统描述', 'string', 1),
        ('system.logo', '/logo.png', '系统Logo', 'string', 1),
        ('system.favicon', '/favicon.ico', '系统图标', 'string', 1),
        
        -- 功能开关配置
        ('feature.registration_enabled', 'true', '是否允许用户注册', 'boolean', 0),
        ('feature.email_verification', 'false', '是否需要邮箱验证', 'boolean', 0),
        ('feature.guest_access', 'true', '是否允许访客访问', 'boolean', 0),
        ('feature.auto_backup', 'true', '是否启用自动备份', 'boolean', 0),
        
        -- 安全配置
        ('security.password_min_length', '8', '密码最小长度', 'integer', 0),
        ('security.password_require_special', 'true', '密码是否需要特殊字符', 'boolean', 0),
        ('security.max_login_attempts', '5', '最大登录尝试次数', 'integer', 0),
        ('security.lockout_duration', '30', '账户锁定时长（分钟）', 'integer', 0),
        ('security.session_timeout', '24', '会话超时时间（小时）', 'integer', 0),
        
        -- 文件上传配置
        ('upload.max_file_size', '104857600', '最大文件大小（字节）', 'integer', 0),
        ('upload.allowed_extensions', '.pdf,.docx,.doc,.pptx,.ppt,.txt,.md,.html,.csv,.xlsx,.xls,.json', '允许的文件扩展名', 'string', 0),
        ('upload.auto_process', 'true', '是否自动处理上传的文档', 'boolean', 0),
        
        -- AI模型配置
        ('ai.default_llm_model', 'deepseek-chat', '默认LLM模型', 'string', 0),
        ('ai.default_embedding_model', 'text-embedding-v1', '默认嵌入模型', 'string', 0),
        ('ai.max_tokens', '4000', '最大Token数', 'integer', 0),
        ('ai.temperature', '0.7', '生成温度', 'float', 0),
        
        -- 检索配置
        ('retrieval.default_top_k', '10', '默认检索数量', 'integer', 0),
        ('retrieval.similarity_threshold', '0.7', '相似度阈值', 'float', 0),
        ('retrieval.enable_rerank', 'true', '是否启用重排', 'boolean', 0),
        ('retrieval.chunk_size', '1000', '默认分块大小', 'integer', 0),
        ('retrieval.chunk_overlap', '200', '分块重叠大小', 'integer', 0),
        
        -- 通知配置
        ('notification.email_enabled', 'false', '是否启用邮件通知', 'boolean', 0),
        ('notification.sms_enabled', 'false', '是否启用短信通知', 'boolean', 0),
        ('notification.webhook_enabled', 'false', '是否启用Webhook通知', 'boolean', 0),
        
        -- 监控配置
        ('monitoring.metrics_enabled', 'true', '是否启用指标监控', 'boolean', 0),
        ('monitoring.log_level', 'INFO', '日志级别', 'string', 0),
        ('monitoring.retention_days', '30', '日志保留天数', 'integer', 0);

        -- 创建示例知识库
        INSERT INTO `knowledge_bases` (
            `name`, 
            `description`, 
            `owner_id`, 
            `is_public`, 
            `status`,
            `settings`
        ) VALUES (
            '示例知识库',
            '这是一个示例知识库，用于演示系统功能',
            1,
            1,
            'active',
            JSON_OBJECT(
                'auto_process', true,
                'chunk_size', 1000,
                'chunk_overlap', 200,
                'enable_graph', true,
                'enable_rerank', true
            )
        );
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DELETE FROM `knowledge_bases` WHERE `name` = '示例知识库';
        DELETE FROM `system_configs`;
        DELETE FROM `user_roles`;
        DELETE FROM `users` WHERE `username` = 'admin';
        DELETE FROM `role_permissions`;
        DELETE FROM `permissions`;
        DELETE FROM `roles`;
    """
