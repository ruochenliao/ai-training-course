# 智能聊天服务使用指南

## 概述

本项目实现了一个基于AutoGen框架的智能聊天服务，支持多记忆融合、流式响应和多模态交互。

## 核心功能

### 1. 聊天会话管理
- **ChatSession类**: 管理单用户对话状态
- **会话生命周期**: 自动创建、管理和清理会话
- **多会话支持**: 每个用户可以同时维护多个独立会话

### 2. 智能体创建
- **AssistantAgent配置**: 基于AutoGen框架的智能助手
- **模型客户端**: 支持Deepseek等OpenAI兼容的模型
- **系统提示**: 可自定义的智能体人格和行为

### 3. 多记忆融合
- **聊天历史记忆**: 基于SQLite的对话历史存储
- **私有记忆**: 用户个人知识库（ChromaDB向量存储）
- **公共记忆**: 共享知识库（FAQ、政策等）
- **智能检索**: 语义搜索和上下文注入

### 4. 多模态消息处理
- **文本消息**: 标准文本对话
- **图片消息**: 支持图片URL输入和分析
- **混合消息**: 文本+图片的多模态交互

### 5. 流式响应
- **实时输出**: 支持流式文本生成
- **SSE格式**: 标准的Server-Sent Events响应
- **错误处理**: 完善的异常处理和恢复机制

## API接口

### 发送消息
```http
POST /api/chat/service/send
Content-Type: application/json
Authorization: Bearer <token>

{
    "user_id": "user123",
    "session_id": "session456",
    "message": "你好，请介绍一下你自己",
    "images": ["https://example.com/image.jpg"],
    "stream": true,
    "model_name": "deepseek-chat",
    "system_prompt": "你是一个专业的客服助手"
}
```

### 获取会话信息
```http
GET /api/chat/service/session/{session_id}
Authorization: Bearer <token>
```

### 获取用户会话列表
```http
GET /api/chat/service/sessions
Authorization: Bearer <token>
```

### 创建新会话
```http
POST /api/chat/service/session/create
Authorization: Bearer <token>
```

### 关闭会话
```http
DELETE /api/chat/service/session/{session_id}
Authorization: Bearer <token>
```

## 使用示例

### Python代码示例

```python
import asyncio
from app.services.chat_service import chat_service
from app.schemas.chat_service import ChatRequest

async def example_chat():
    # 创建聊天请求
    request = ChatRequest(
        user_id="user123",
        session_id="session456",
        message="你好，请介绍一下你自己",
        stream=True
    )
    
    # 发送消息并处理流式响应
    async for chunk in chat_service.send_message(request):
        if chunk.content:
            print(chunk.content, end='', flush=True)
        
        if chunk.is_final:
            print("\n响应完成")
            break

# 运行示例
asyncio.run(example_chat())
```

### JavaScript前端示例

```javascript
// 发送流式聊天消息
async function sendStreamMessage(message, sessionId) {
    const response = await fetch('/api/chat/service/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            message: message,
            session_id: sessionId,
            stream: true
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') {
                    console.log('响应完成');
                    return;
                }

                try {
                    const parsed = JSON.parse(data);
                    if (parsed.content) {
                        // 显示响应内容
                        displayMessage(parsed.content);
                    }
                } catch (e) {
                    console.error('解析响应失败:', e);
                }
            }
        }
    }
}
```

## 配置说明

### 环境变量
```bash
# Deepseek API配置
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 数据库配置
DATABASE_URL=sqlite:///./db.sqlite3

# 记忆服务配置
CHROMADB_PATH=./chromadb
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

### 服务配置
```python
from app.schemas.chat_service import ChatServiceConfig

config = ChatServiceConfig(
    max_sessions_per_user=10,
    session_timeout_minutes=60,
    max_messages_per_session=100,
    memory_context_limit=10,
    enable_streaming=True,
    enable_multimodal=True,
    default_model="deepseek-chat",
    system_prompt="你是超级智能客服，专业、友好、乐于助人。"
)
```

## 测试

### 运行测试脚本
```bash
cd SuperIntelligentCustomerService
python test_chat_service.py
```

### 测试内容
- 基本聊天功能
- 流式响应
- 多模态交互
- 会话管理
- 记忆集成
- 服务统计

## 部署注意事项

### 依赖安装
```bash
pip install -r requirements.txt
```

### 数据库初始化
```bash
# 数据库迁移
aerich init -t app.settings.config.TORTOISE_ORM
aerich init-db
aerich migrate
aerich upgrade
```

### 服务启动
```bash
# 开发环境
uvicorn app:create_app --reload --host 0.0.0.0 --port 8000

# 生产环境
gunicorn app:create_app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 故障排除

### 常见问题

1. **AutoGen导入失败**
   - 确保安装了正确版本的autogen包
   - 检查Python版本兼容性

2. **记忆服务初始化失败**
   - 检查ChromaDB和sentence-transformers是否正确安装
   - 确认数据库文件权限

3. **模型API调用失败**
   - 验证API密钥是否正确
   - 检查网络连接和API端点

4. **流式响应中断**
   - 检查客户端连接稳定性
   - 确认服务器资源充足

### 日志配置
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chat_service.log'),
        logging.StreamHandler()
    ]
)
```

## 扩展开发

### 添加新的记忆类型
1. 继承`BaseMemoryService`类
2. 实现必要的抽象方法
3. 在`MemoryServiceFactory`中注册

### 自定义智能体
1. 创建新的Agent类
2. 配置模型客户端和工具
3. 集成到ChatSession中

### 添加新的消息类型
1. 扩展`MessageType`枚举
2. 更新消息处理逻辑
3. 适配前端显示组件
