"""
记忆服务基础类和数据结构
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """记忆项数据结构"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


# 移除BaseMemoryService抽象类，因为现在只使用向量数据库实现
# 保留MemoryItem数据结构供其他模块使用
