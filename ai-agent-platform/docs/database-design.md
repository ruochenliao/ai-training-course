# 数据库设计文档

## 1. 数据库架构概述

### 1.1 数据存储分层
- **MySQL**: 关系型数据，用户信息、权限、会话、元数据
- **Milvus**: 向量数据，文档嵌入向量、相似度检索
- **Minio**: 对象存储，原始文件、图片、附件
- **Redis**: 缓存数据，会话缓存、任务队列、临时数据

## 2. MySQL数据库设计

### 2.1 用户与权限模块

```sql
-- 用户表
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    avatar_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL,
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
);

-- 角色表
CREATE TABLE roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 用户角色关联表
CREATE TABLE user_roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by BIGINT,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(id),
    UNIQUE KEY uk_user_role (user_id, role_id)
);
```

### 2.2 知识库模块

```sql
-- 知识库表
CREATE TABLE knowledge_bases (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    type ENUM('public', 'private', 'shared') DEFAULT 'private',
    owner_id BIGINT NOT NULL,
    settings JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (owner_id) REFERENCES users(id),
    INDEX idx_owner_id (owner_id),
    INDEX idx_type (type),
    INDEX idx_created_at (created_at)
);

-- 文件表
CREATE TABLE files (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    knowledge_base_id BIGINT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100),
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    error_message TEXT,
    uploaded_by BIGINT NOT NULL,
    processed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id),
    INDEX idx_kb_id (knowledge_base_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- 文档块表
CREATE TABLE document_chunks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    file_id BIGINT NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    metadata JSON,
    vector_id VARCHAR(100),
    token_count INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    INDEX idx_file_id (file_id),
    INDEX idx_vector_id (vector_id),
    INDEX idx_content_hash (content_hash)
);
```

### 2.3 会话与对话模块

```sql
-- 会话表
CREATE TABLE conversations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    agent_type ENUM('customer_service', 'text2sql', 'knowledge_qa', 'content_creation') NOT NULL,
    title VARCHAR(200),
    context JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_agent_type (agent_type),
    INDEX idx_created_at (created_at)
);

-- 消息表
CREATE TABLE messages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    conversation_id BIGINT NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,
    attachments JSON,
    feedback ENUM('positive', 'negative') NULL,
    feedback_comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_role (role),
    INDEX idx_created_at (created_at)
);
```

### 2.4 系统配置与日志模块

```sql
-- 系统配置表
CREATE TABLE system_configs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSON NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    updated_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (updated_by) REFERENCES users(id),
    INDEX idx_config_key (config_key)
);

-- 操作日志表
CREATE TABLE operation_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT,
    operation_type VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    operation_detail JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_operation_type (operation_type),
    INDEX idx_resource_type (resource_type),
    INDEX idx_created_at (created_at)
);

-- API调用统计表
CREATE TABLE api_statistics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INT NOT NULL,
    response_time_ms INT,
    user_id BIGINT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_endpoint (endpoint),
    INDEX idx_status_code (status_code),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);
```

## 3. Milvus向量数据库设计

### 3.1 集合结构设计

```python
# 文档向量集合
collection_schema = {
    "collection_name": "document_vectors",
    "fields": [
        {
            "name": "id",
            "type": "INT64",
            "is_primary": True,
            "auto_id": True
        },
        {
            "name": "chunk_id",
            "type": "INT64",
            "description": "对应document_chunks表的id"
        },
        {
            "name": "file_id", 
            "type": "INT64",
            "description": "对应files表的id"
        },
        {
            "name": "knowledge_base_id",
            "type": "INT64", 
            "description": "对应knowledge_bases表的id"
        },
        {
            "name": "content",
            "type": "VARCHAR",
            "max_length": 65535,
            "description": "文档块内容"
        },
        {
            "name": "embedding",
            "type": "FLOAT_VECTOR",
            "dim": 1536,  # OpenAI text-embedding-ada-002维度
            "description": "文档向量"
        },
        {
            "name": "metadata",
            "type": "JSON",
            "description": "元数据信息"
        }
    ],
    "indexes": [
        {
            "field_name": "embedding",
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 1024}
        }
    ]
}
```

### 3.2 分区策略

```python
# 按知识库分区
partition_strategy = {
    "partition_by": "knowledge_base_id",
    "partition_naming": "kb_{knowledge_base_id}",
    "benefits": [
        "数据隔离",
        "查询性能优化", 
        "权限控制",
        "独立管理"
    ]
}
```

## 4. Redis缓存设计

### 4.1 缓存键命名规范

```python
# 缓存键命名规范
cache_keys = {
    "user_session": "session:user:{user_id}",
    "user_permissions": "perm:user:{user_id}",
    "conversation_context": "conv:context:{conversation_id}",
    "file_processing_status": "file:status:{file_id}",
    "api_rate_limit": "rate:api:{user_id}:{endpoint}",
    "system_config": "config:{config_key}",
    "knowledge_base_stats": "stats:kb:{kb_id}",
    "search_cache": "search:{query_hash}"
}
```

### 4.2 缓存策略

```python
# 缓存过期时间配置
cache_ttl = {
    "user_session": 86400,      # 24小时
    "user_permissions": 3600,   # 1小时
    "conversation_context": 7200,  # 2小时
    "file_processing_status": 300,  # 5分钟
    "api_rate_limit": 60,       # 1分钟
    "system_config": 3600,      # 1小时
    "search_cache": 1800        # 30分钟
}
```

## 5. 数据迁移与初始化

### 5.1 初始数据

```sql
-- 插入默认角色
INSERT INTO roles (name, description, permissions) VALUES
('admin', '系统管理员', '["*"]'),
('user', '普通用户', '["read:own", "write:own"]'),
('viewer', '只读用户', '["read:own"]');

-- 插入默认系统配置
INSERT INTO system_configs (config_key, config_value, description) VALUES
('llm.default_model', '"gpt-4o"', '默认LLM模型'),
('embedding.model', '"text-embedding-ada-002"', '默认嵌入模型'),
('rag.chunk_size', '1000', 'RAG文档分块大小'),
('rag.chunk_overlap', '200', 'RAG文档分块重叠'),
('api.rate_limit', '{"requests_per_minute": 60}', 'API限流配置');
```

### 5.2 索引优化

```sql
-- 性能优化索引
CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at);
CREATE INDEX idx_files_kb_status ON files(knowledge_base_id, status);
CREATE INDEX idx_chunks_file_index ON document_chunks(file_id, chunk_index);
CREATE INDEX idx_logs_user_created ON operation_logs(user_id, created_at);
CREATE INDEX idx_stats_endpoint_created ON api_statistics(endpoint, created_at);
```

## 6. 数据备份与恢复策略

### 6.1 备份策略
- **MySQL**: 每日全量备份 + 实时binlog备份
- **Milvus**: 定期快照备份
- **Minio**: 跨区域复制备份
- **Redis**: RDB + AOF持久化

### 6.2 数据保留策略
- 操作日志: 保留1年
- API统计: 保留6个月  
- 会话消息: 永久保留(可配置)
- 文件数据: 永久保留
- 缓存数据: 按TTL自动清理
