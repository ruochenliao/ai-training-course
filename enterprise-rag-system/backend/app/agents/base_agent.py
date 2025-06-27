"""
基础智能体类

定义了所有智能体的基础接口和通用功能
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """智能体基类"""
    
    def __init__(self, name: str, description: str = "", config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.description = description
        self.config = config or {}
        self.created_at = datetime.now()
        self.last_active = None
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        }
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据并返回结果
        
        Args:
            input_data: 输入数据
            
        Returns:
            处理结果
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        获取智能体的能力列表
        
        Returns:
            能力列表
        """
        pass
    
    def update_metrics(self, success: bool, response_time: float):
        """更新性能指标"""
        self.metrics["total_requests"] += 1
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
            
        # 更新平均响应时间
        total_time = self.metrics["average_response_time"] * (self.metrics["total_requests"] - 1)
        self.metrics["average_response_time"] = (total_time + response_time) / self.metrics["total_requests"]
        
        self.last_active = datetime.now()
    
    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "metrics": self.metrics,
            "capabilities": self.get_capabilities()
        }
    
    def reset_metrics(self):
        """重置性能指标"""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        }
        
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
    
    def __repr__(self) -> str:
        return self.__str__()
