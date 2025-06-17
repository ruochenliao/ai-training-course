"""
聊天记忆服务
基于现有ChatMessage模型扩展，提供聊天历史记忆功能
"""
import json
import sqlite3
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

from .base import MemoryItem
from app.settings import settings

logger = logging.getLogger(__name__)


class ChatMemoryService:
    """聊天历史记忆服务"""

    def __init__(self, user_id: str, db_path: str = None):
        self.user_id = user_id
        if db_path is None:
            # 使用项目配置的数据库路径
            db_path = settings.TORTOISE_ORM["connections"]["sqlite"]["credentials"]["file_path"]
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化聊天记忆数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            # 创建聊天记忆扩展表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_memories (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_user_session 
                ON chat_memories(user_id, session_id, created_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_user_time 
                ON chat_memories(user_id, created_at DESC)
            """)
    
    async def add_message(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加聊天消息到记忆"""
        memory_id = f"chat_{self.user_id}_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # 提取文本内容
        text_content = self._extract_text_content(content)
        
        # 构建元数据
        message_metadata = {
            "session_id": session_id,
            "role": role,
            "timestamp": datetime.now().isoformat(),
            "content_type": "multimodal" if isinstance(content, list) else "text"
        }
        
        if metadata:
            message_metadata.update(metadata)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO chat_memories 
                   (id, user_id, session_id, role, content, metadata) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    memory_id,
                    self.user_id,
                    session_id,
                    role,
                    text_content,
                    json.dumps(message_metadata)
                )
            )
        
        return memory_id
    
    async def get_session_history(self, session_id: str, limit: int = 50) -> List[MemoryItem]:
        """获取会话历史"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT * FROM chat_memories 
                   WHERE user_id = ? AND session_id = ? 
                   ORDER BY created_at ASC 
                   LIMIT ?""",
                (self.user_id, session_id, limit)
            )
            rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                try:
                    metadata = json.loads(row["metadata"])
                    memory = MemoryItem(
                        id=row["id"],
                        content=row["content"],
                        metadata=metadata,
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"])
                    )
                    memories.append(memory)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse chat memory: {e}")
                    continue
            
            return memories
    
    async def get_recent_context(self, limit: int = 10) -> List[MemoryItem]:
        """获取最近的对话上下文"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT * FROM chat_memories 
                   WHERE user_id = ? 
                   ORDER BY created_at DESC 
                   LIMIT ?""",
                (self.user_id, limit)
            )
            rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                try:
                    metadata = json.loads(row["metadata"])
                    memory = MemoryItem(
                        id=row["id"],
                        content=row["content"],
                        metadata=metadata,
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"])
                    )
                    memories.append(memory)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse memory item: {e}")
                    continue
            
            return memories
    
    async def search_conversations(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """搜索相关对话"""
        query_lower = query.lower()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT * FROM chat_memories 
                   WHERE user_id = ? AND LOWER(content) LIKE ? 
                   ORDER BY created_at DESC 
                   LIMIT ?""",
                (self.user_id, f"%{query_lower}%", limit * 2)  # 获取更多结果用于排序
            )
            rows = cursor.fetchall()
            
            # 简单的相关性评分
            scored_memories = []
            for row in rows:
                content_lower = row["content"].lower()
                score = self._calculate_relevance_score(query_lower, content_lower)
                
                if score > 0:
                    try:
                        metadata = json.loads(row["metadata"])
                        memory = MemoryItem(
                            id=row["id"],
                            content=row["content"],
                            metadata={**metadata, "relevance_score": score},
                            created_at=datetime.fromisoformat(row["created_at"]),
                            updated_at=datetime.fromisoformat(row["updated_at"])
                        )
                        scored_memories.append(memory)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Failed to parse memory item: {e}")
                        continue
            
            # 按相关性排序并返回前N个
            scored_memories.sort(key=lambda x: x.metadata.get("relevance_score", 0), reverse=True)
            return scored_memories[:limit]
    
    def _extract_text_content(self, content: Union[str, List[Dict[str, Any]]]) -> str:
        """从消息内容中提取文本"""
        if isinstance(content, str):
            return content
        
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            return " ".join(text_parts)
        
        return str(content)
    
    # 实现基类抽象方法
    async def add_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加通用记忆（用于兼容基类接口）"""
        session_id = metadata.get("session_id", "default") if metadata else "default"
        role = metadata.get("role", "user") if metadata else "user"
        return await self.add_message(session_id, role, content, metadata)
    
    async def retrieve_memories(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """检索相关记忆"""
        return await self.search_conversations(query, limit)
    
    async def update_memory(self, memory_id: str, content: str = None, metadata: Dict[str, Any] = None) -> bool:
        """更新记忆"""
        updates = []
        params = []
        
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(memory_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"UPDATE chat_memories SET {', '.join(updates)} WHERE id = ?",
                params
            )
            return cursor.rowcount > 0
    
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM chat_memories WHERE id = ? AND user_id = ?",
                (memory_id, self.user_id)
            )
            return cursor.rowcount > 0
    
    async def cleanup_old_memories(self, days: int = 30) -> int:
        """清理过期记忆"""
        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM chat_memories WHERE user_id = ? AND created_at < ?",
                (self.user_id, cutoff_date.isoformat())
            )
            return cursor.rowcount

    def _calculate_relevance_score(self, query: str, content: str) -> float:
        """计算相关性评分"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())

        if not query_words:
            return 0.0

        # 计算词汇重叠度
        intersection = query_words.intersection(content_words)
        union = query_words.union(content_words)

        jaccard_score = len(intersection) / len(union) if union else 0.0

        # 考虑完整匹配
        exact_match_bonus = 0.5 if query.lower() in content.lower() else 0.0

        return jaccard_score + exact_match_bonus
