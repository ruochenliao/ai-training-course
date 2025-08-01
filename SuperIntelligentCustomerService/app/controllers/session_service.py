import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.schemas.customer import ChatMessage


class SessionService:
    """会话服务，管理用户聊天会话"""

    def __init__(self):
        """初始化会话服务"""
        self.logger = logging.getLogger("session_service")

        # 获取项目根目录
        from ..settings.config import settings
        self.base_dir = settings.BASE_DIR

        # 确保会话存储目录存在
        self.sessions_dir = os.path.join(self.base_dir, "data", "sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)

        # 初始化日志
        logs_dir = os.path.join(self.base_dir, "logs", "sessions")
        os.makedirs(logs_dir, exist_ok=True)

        file_handler = logging.FileHandler(os.path.join(logs_dir, "sessions.log"))
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)

    def create_session(self, user_id: str) -> Dict[str, Any]:
        """创建新的会话

        Args:
            user_id: 用户ID

        Returns:
            会话信息
        """
        session_id = str(uuid.uuid4())
        created_at = datetime.now()

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": created_at.isoformat(),
            "last_active": created_at.isoformat(),
            "messages": []
        }

        # 保存会话到文件
        self._save_session(session_data)

        self.logger.info(f"Created new session {session_id} for user {user_id}")

        return session_data

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            会话信息，如果不存在则返回None
        """
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")

        if not os.path.exists(session_file):
            self.logger.warning(f"Session {session_id} not found")
            return None

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                return session_data
        except Exception as e:
            self.logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def add_message(self, session_id: str, message: ChatMessage) -> bool:
        """添加消息到会话

        Args:
            session_id: 会话ID
            message: 聊天消息

        Returns:
            是否成功添加
        """
        session_data = self.get_session(session_id)

        if not session_data:
            self.logger.warning(f"Cannot add message to non-existent session {session_id}")
            return False

        # 更新最后活动时间
        session_data["last_active"] = datetime.now().isoformat()

        # 添加消息
        # 处理不同类型的消息内容
        if isinstance(message.content, str):
            # 纯文本消息
            message_data = {
                "role": message.role,
                "content": message.content
            }
        else:
            # 复杂消息内容（如图片）
            message_data = {
                "role": message.role,
                "content": message.content.dict() if hasattr(message.content, "dict") else message.content.model_dump()
            }

        session_data["messages"].append(message_data)

        # 保存会话
        self._save_session(session_data)

        return True

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有会话

        Args:
            user_id: 用户ID

        Returns:
            会话列表
        """
        sessions = []

        # 遍历会话目录
        for filename in os.listdir(self.sessions_dir):
            if not filename.endswith('.json'):
                continue

            try:
                with open(os.path.join(self.sessions_dir, filename), 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                    if session_data.get("user_id") == user_id:
                        sessions.append(session_data)
            except Exception as e:
                self.logger.error(f"Failed to load session file {filename}: {e}")

        # 按最后活动时间排序
        sessions.sort(key=lambda x: x.get("last_active", ""), reverse=True)

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """删除会话

        Args:
            session_id: 会话ID

        Returns:
            是否删除成功
        """
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")

        try:
            if os.path.exists(session_file):
                os.remove(session_file)
                self.logger.info(f"Deleted session file: {session_id}")
                return True
            else:
                self.logger.warning(f"Session file not found: {session_id}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """更新会话信息

        Args:
            session_id: 会话ID
            updates: 要更新的字段

        Returns:
            是否更新成功
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return False

            # 更新字段
            for key, value in updates.items():
                if key in session_data:
                    session_data[key] = value

            # 更新最后活动时间
            session_data["last_active"] = datetime.now().isoformat()

            # 保存会话
            self._save_session(session_data)

            self.logger.info(f"Updated session {session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update session {session_id}: {e}")
            return False

    def _save_session(self, session_data: Dict[str, Any]) -> None:
        """保存会话到文件

        Args:
            session_data: 会话数据
        """
        session_id = session_data["session_id"]
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")

        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save session {session_id}: {e}")


# 创建全局会话服务实例
session_service = SessionService()
