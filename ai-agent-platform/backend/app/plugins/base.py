"""
插件基类

定义插件的基础接口和元数据结构。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """插件类型"""
    AGENT = "agent"
    TOOL = "tool"
    INTEGRATION = "integration"
    MIDDLEWARE = "middleware"
    WORKFLOW = "workflow"
    UI_COMPONENT = "ui_component"


class PluginStatus(Enum):
    """插件状态"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    ERROR = "error"
    LOADING = "loading"


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = None
    config_schema: Dict[str, Any] = None
    permissions: List[str] = None
    min_platform_version: str = "1.0.0"
    max_platform_version: str = None
    homepage: str = None
    repository: str = None
    license: str = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.config_schema is None:
            self.config_schema = {}
        if self.permissions is None:
            self.permissions = []
        if self.tags is None:
            self.tags = []


class BasePlugin(ABC):
    """插件基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.status = PluginStatus.INACTIVE
        self.logger = logging.getLogger(f"plugin.{self.metadata.name}")
        self._hooks = {}
        
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """插件元数据"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化插件
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """
        清理插件资源
        
        Returns:
            bool: 清理是否成功
        """
        pass
    
    async def activate(self) -> bool:
        """
        激活插件
        
        Returns:
            bool: 激活是否成功
        """
        try:
            self.status = PluginStatus.LOADING
            success = await self.initialize()
            
            if success:
                self.status = PluginStatus.ACTIVE
                self.logger.info(f"插件 {self.metadata.name} 激活成功")
                await self.on_activate()
            else:
                self.status = PluginStatus.ERROR
                self.logger.error(f"插件 {self.metadata.name} 激活失败")
                
            return success
            
        except Exception as e:
            self.status = PluginStatus.ERROR
            self.logger.error(f"插件 {self.metadata.name} 激活异常: {e}")
            return False
    
    async def deactivate(self) -> bool:
        """
        停用插件
        
        Returns:
            bool: 停用是否成功
        """
        try:
            success = await self.cleanup()
            
            if success:
                self.status = PluginStatus.INACTIVE
                self.logger.info(f"插件 {self.metadata.name} 停用成功")
                await self.on_deactivate()
            else:
                self.logger.error(f"插件 {self.metadata.name} 停用失败")
                
            return success
            
        except Exception as e:
            self.logger.error(f"插件 {self.metadata.name} 停用异常: {e}")
            return False
    
    async def on_activate(self):
        """插件激活后的回调"""
        pass
    
    async def on_deactivate(self):
        """插件停用后的回调"""
        pass
    
    def register_hook(self, event: str, callback):
        """注册事件钩子"""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)
    
    async def trigger_hook(self, event: str, *args, **kwargs):
        """触发事件钩子"""
        if event in self._hooks:
            for callback in self._hooks[event]:
                try:
                    await callback(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"钩子回调执行失败: {e}")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            bool: 配置是否有效
        """
        if not self.metadata.config_schema:
            return True
            
        # 这里可以使用jsonschema等库进行验证
        # 暂时简单验证必需字段
        required_fields = self.metadata.config_schema.get('required', [])
        for field in required_fields:
            if field not in config:
                self.logger.error(f"缺少必需配置字段: {field}")
                return False
                
        return True
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        if self.validate_config(config):
            self.config.update(config)
            return True
        return False


class AgentPlugin(BasePlugin):
    """智能体插件基类"""
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据
        
        Args:
            input_data: 输入数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        pass


class ToolPlugin(BasePlugin):
    """工具插件基类"""
    
    @abstractmethod
    async def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具操作
        
        Args:
            action: 操作名称
            parameters: 操作参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass
    
    @abstractmethod
    def get_available_actions(self) -> List[str]:
        """获取可用操作列表"""
        pass


class IntegrationPlugin(BasePlugin):
    """集成插件基类"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """建立连接"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass
    
    @abstractmethod
    async def sync_data(self, data_type: str, direction: str = "both") -> bool:
        """
        同步数据
        
        Args:
            data_type: 数据类型
            direction: 同步方向 (import/export/both)
            
        Returns:
            bool: 同步是否成功
        """
        pass


class MiddlewarePlugin(BasePlugin):
    """中间件插件基类"""
    
    @abstractmethod
    async def before_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """请求前处理"""
        pass
    
    @abstractmethod
    async def after_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """响应后处理"""
        pass


class WorkflowPlugin(BasePlugin):
    """工作流插件基类"""
    
    @abstractmethod
    async def execute_step(self, step_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工作流步骤
        
        Args:
            step_config: 步骤配置
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass
    
    @abstractmethod
    def get_step_schema(self) -> Dict[str, Any]:
        """获取步骤配置模式"""
        pass


class UIComponentPlugin(BasePlugin):
    """UI组件插件基类"""
    
    @abstractmethod
    def get_component_definition(self) -> Dict[str, Any]:
        """获取组件定义"""
        pass
    
    @abstractmethod
    def get_component_assets(self) -> Dict[str, str]:
        """获取组件资源文件"""
        pass
