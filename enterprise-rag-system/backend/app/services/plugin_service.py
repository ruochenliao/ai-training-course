"""
插件系统服务
"""

import asyncio
import importlib
import inspect
import json
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

from loguru import logger

from app.core.exceptions import PluginException


class PluginStatus(Enum):
    """插件状态"""
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UPDATING = "updating"


class PluginType(Enum):
    """插件类型"""
    DOCUMENT_PROCESSOR = "document_processor"
    EMBEDDING_PROVIDER = "embedding_provider"
    LLM_PROVIDER = "llm_provider"
    SEARCH_ENHANCER = "search_enhancer"
    UI_COMPONENT = "ui_component"
    WORKFLOW_TASK = "workflow_task"
    NOTIFICATION_CHANNEL = "notification_channel"
    AUTHENTICATION = "authentication"
    INTEGRATION = "integration"
    CUSTOM = "custom"


@dataclass
class PluginManifest:
    """插件清单"""
    id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    entry_point: str
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    min_system_version: str = "1.0.0"
    max_system_version: str = ""
    homepage: str = ""
    repository: str = ""
    license: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class PluginInfo:
    """插件信息"""
    manifest: PluginManifest
    status: PluginStatus
    installed_at: datetime
    enabled_at: Optional[datetime] = None
    disabled_at: Optional[datetime] = None
    error_message: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    instance: Optional[Any] = None


class PluginHook:
    """插件钩子"""
    
    def __init__(self, name: str):
        self.name = name
        self.callbacks: List[Callable] = []
    
    def register(self, callback: Callable):
        """注册回调函数"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def unregister(self, callback: Callable):
        """注销回调函数"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    async def execute(self, *args, **kwargs) -> List[Any]:
        """执行所有回调函数"""
        results = []
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    result = await callback(*args, **kwargs)
                else:
                    result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"插件钩子执行失败: {self.name} - {e}")
                results.append(None)
        return results


class BasePlugin:
    """插件基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.hooks: Dict[str, PluginHook] = {}
    
    async def initialize(self):
        """初始化插件"""
        pass
    
    async def cleanup(self):
        """清理插件"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        return {
            "name": self.__class__.__name__,
            "version": "1.0.0",
            "description": "基础插件"
        }
    
    def register_hook(self, hook_name: str, callback: Callable):
        """注册钩子"""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = PluginHook(hook_name)
        self.hooks[hook_name].register(callback)
    
    async def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """执行钩子"""
        if hook_name in self.hooks:
            return await self.hooks[hook_name].execute(*args, **kwargs)
        return []


class PluginService:
    """插件系统服务类"""
    
    def __init__(self):
        """初始化插件服务"""
        self.plugins_dir = Path("plugins")
        self.plugins_dir.mkdir(exist_ok=True)
        
        self.installed_plugins: Dict[str, PluginInfo] = {}
        self.enabled_plugins: Dict[str, PluginInfo] = {}
        self.global_hooks: Dict[str, PluginHook] = {}
        
        # 初始化系统钩子
        self._init_system_hooks()
        
        logger.info("插件系统服务初始化完成")
    
    def _init_system_hooks(self):
        """初始化系统钩子"""
        system_hooks = [
            "before_document_process",
            "after_document_process",
            "before_search",
            "after_search",
            "before_chat",
            "after_chat",
            "user_login",
            "user_logout",
            "system_startup",
            "system_shutdown"
        ]
        
        for hook_name in system_hooks:
            self.global_hooks[hook_name] = PluginHook(hook_name)
    
    async def install_plugin(self, plugin_file: str) -> bool:
        """安装插件"""
        try:
            plugin_path = Path(plugin_file)
            if not plugin_path.exists():
                raise PluginException(f"插件文件不存在: {plugin_file}")
            
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # 解压插件
                if plugin_path.suffix == '.zip':
                    with zipfile.ZipFile(plugin_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_path)
                else:
                    raise PluginException("不支持的插件格式，请使用ZIP文件")
                
                # 读取插件清单
                manifest_file = temp_path / "manifest.json"
                if not manifest_file.exists():
                    raise PluginException("插件清单文件不存在")
                
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)
                
                manifest = PluginManifest(**manifest_data)
                
                # 验证插件
                await self._validate_plugin(manifest, temp_path)
                
                # 检查是否已安装
                if manifest.id in self.installed_plugins:
                    raise PluginException(f"插件已安装: {manifest.id}")
                
                # 复制插件文件
                plugin_install_dir = self.plugins_dir / manifest.id
                plugin_install_dir.mkdir(exist_ok=True)
                
                import shutil
                for item in temp_path.iterdir():
                    if item.is_file():
                        shutil.copy2(item, plugin_install_dir)
                    elif item.is_dir():
                        shutil.copytree(item, plugin_install_dir / item.name, dirs_exist_ok=True)
                
                # 创建插件信息
                plugin_info = PluginInfo(
                    manifest=manifest,
                    status=PluginStatus.INSTALLED,
                    installed_at=datetime.now()
                )
                
                self.installed_plugins[manifest.id] = plugin_info
                
                logger.info(f"插件安装成功: {manifest.name} ({manifest.id})")
                return True
                
        except Exception as e:
            logger.error(f"安装插件失败: {e}")
            raise PluginException(f"安装插件失败: {e}")
    
    async def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件"""
        try:
            if plugin_id not in self.installed_plugins:
                raise PluginException(f"插件未安装: {plugin_id}")
            
            plugin_info = self.installed_plugins[plugin_id]
            
            if plugin_info.status == PluginStatus.ENABLED:
                logger.warning(f"插件已启用: {plugin_id}")
                return True
            
            # 加载插件
            plugin_instance = await self._load_plugin(plugin_info)
            
            # 初始化插件
            await plugin_instance.initialize()
            
            # 更新插件信息
            plugin_info.instance = plugin_instance
            plugin_info.status = PluginStatus.ENABLED
            plugin_info.enabled_at = datetime.now()
            plugin_info.error_message = None
            
            self.enabled_plugins[plugin_id] = plugin_info
            
            # 执行启用钩子
            await self.execute_hook("plugin_enabled", plugin_id, plugin_info)
            
            logger.info(f"插件启用成功: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"启用插件失败: {plugin_id} - {e}")
            
            # 更新错误状态
            if plugin_id in self.installed_plugins:
                self.installed_plugins[plugin_id].status = PluginStatus.ERROR
                self.installed_plugins[plugin_id].error_message = str(e)
            
            return False
    
    async def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件"""
        try:
            if plugin_id not in self.enabled_plugins:
                logger.warning(f"插件未启用: {plugin_id}")
                return True
            
            plugin_info = self.enabled_plugins[plugin_id]
            
            # 清理插件
            if plugin_info.instance:
                await plugin_info.instance.cleanup()
            
            # 更新插件信息
            plugin_info.status = PluginStatus.DISABLED
            plugin_info.disabled_at = datetime.now()
            plugin_info.instance = None
            
            # 从启用列表中移除
            del self.enabled_plugins[plugin_id]
            
            # 执行禁用钩子
            await self.execute_hook("plugin_disabled", plugin_id, plugin_info)
            
            logger.info(f"插件禁用成功: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"禁用插件失败: {plugin_id} - {e}")
            return False
    
    async def uninstall_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        try:
            # 先禁用插件
            if plugin_id in self.enabled_plugins:
                await self.disable_plugin(plugin_id)
            
            if plugin_id not in self.installed_plugins:
                logger.warning(f"插件未安装: {plugin_id}")
                return True
            
            # 删除插件文件
            plugin_dir = self.plugins_dir / plugin_id
            if plugin_dir.exists():
                import shutil
                shutil.rmtree(plugin_dir)
            
            # 从安装列表中移除
            del self.installed_plugins[plugin_id]
            
            logger.info(f"插件卸载成功: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"卸载插件失败: {plugin_id} - {e}")
            return False
    
    async def get_plugin_info(self, plugin_id: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        return self.installed_plugins.get(plugin_id)
    
    async def list_plugins(
        self,
        status: Optional[PluginStatus] = None,
        plugin_type: Optional[PluginType] = None
    ) -> List[PluginInfo]:
        """列出插件"""
        plugins = list(self.installed_plugins.values())
        
        if status:
            plugins = [p for p in plugins if p.status == status]
        
        if plugin_type:
            plugins = [p for p in plugins if p.manifest.plugin_type == plugin_type]
        
        return plugins
    
    async def update_plugin_config(
        self,
        plugin_id: str,
        config: Dict[str, Any]
    ) -> bool:
        """更新插件配置"""
        try:
            if plugin_id not in self.installed_plugins:
                raise PluginException(f"插件未安装: {plugin_id}")
            
            plugin_info = self.installed_plugins[plugin_id]
            
            # 验证配置
            if not self._validate_config(plugin_info.manifest.config_schema, config):
                raise PluginException("配置验证失败")
            
            # 更新配置
            plugin_info.config = config
            
            # 如果插件已启用，重新配置
            if plugin_info.status == PluginStatus.ENABLED and plugin_info.instance:
                plugin_info.instance.config = config
                # 可以添加重新配置的逻辑
            
            logger.info(f"插件配置更新成功: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新插件配置失败: {plugin_id} - {e}")
            return False
    
    def register_hook(self, hook_name: str, callback: Callable):
        """注册全局钩子"""
        if hook_name not in self.global_hooks:
            self.global_hooks[hook_name] = PluginHook(hook_name)
        
        self.global_hooks[hook_name].register(callback)
    
    async def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """执行全局钩子"""
        if hook_name in self.global_hooks:
            return await self.global_hooks[hook_name].execute(*args, **kwargs)
        return []
    
    async def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInfo]:
        """按类型获取插件"""
        return [
            plugin for plugin in self.enabled_plugins.values()
            if plugin.manifest.plugin_type == plugin_type
        ]
    
    # 私有方法
    async def _validate_plugin(self, manifest: PluginManifest, plugin_path: Path):
        """验证插件"""
        # 检查入口点文件是否存在
        entry_file = plugin_path / manifest.entry_point
        if not entry_file.exists():
            raise PluginException(f"入口点文件不存在: {manifest.entry_point}")
        
        # 检查依赖
        for dependency in manifest.dependencies:
            try:
                importlib.import_module(dependency)
            except ImportError:
                raise PluginException(f"缺少依赖: {dependency}")
        
        # 检查系统版本兼容性
        # 这里可以添加版本检查逻辑
        
        logger.info(f"插件验证通过: {manifest.id}")
    
    async def _load_plugin(self, plugin_info: PluginInfo) -> BasePlugin:
        """加载插件"""
        try:
            plugin_dir = self.plugins_dir / plugin_info.manifest.id
            
            # 添加插件目录到Python路径
            if str(plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin_dir))
            
            # 导入插件模块
            module_name = plugin_info.manifest.entry_point.replace('.py', '')
            module = importlib.import_module(module_name)
            
            # 查找插件类
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BasePlugin) and 
                    obj != BasePlugin):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                raise PluginException("未找到插件类")
            
            # 创建插件实例
            plugin_instance = plugin_class(plugin_info.config)
            
            return plugin_instance
            
        except Exception as e:
            logger.error(f"加载插件失败: {plugin_info.manifest.id} - {e}")
            raise PluginException(f"加载插件失败: {e}")
    
    def _validate_config(self, schema: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """验证配置"""
        try:
            # 简单的配置验证
            # 实际应用中可以使用jsonschema等库
            for key, value_type in schema.items():
                if key in config:
                    if not isinstance(config[key], eval(value_type)):
                        return False
            return True
        except Exception:
            return False


# 全局插件服务实例
plugin_service = PluginService()


# 示例插件类
class DocumentProcessorPlugin(BasePlugin):
    """文档处理插件示例"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.processor_name = config.get("processor_name", "default")
    
    async def initialize(self):
        """初始化插件"""
        logger.info(f"文档处理插件初始化: {self.processor_name}")
        
        # 注册钩子
        plugin_service.register_hook("before_document_process", self.before_process)
        plugin_service.register_hook("after_document_process", self.after_process)
    
    async def cleanup(self):
        """清理插件"""
        logger.info(f"文档处理插件清理: {self.processor_name}")
    
    async def before_process(self, document_path: str, **kwargs):
        """文档处理前钩子"""
        logger.info(f"文档处理前: {document_path}")
        return {"processed_by": self.processor_name}
    
    async def after_process(self, document_path: str, result: Any, **kwargs):
        """文档处理后钩子"""
        logger.info(f"文档处理后: {document_path}")
        return {"enhanced_result": result}
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        return {
            "name": "文档处理插件",
            "version": "1.0.0",
            "description": "增强文档处理功能",
            "processor_name": self.processor_name
        }
