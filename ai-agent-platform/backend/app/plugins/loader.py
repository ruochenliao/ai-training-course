"""
插件加载器

负责从文件系统动态加载插件。
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from .base import BasePlugin

logger = logging.getLogger(__name__)


class PluginLoader:
    """插件加载器"""
    
    def __init__(self):
        self._loaded_modules: Dict[str, Any] = {}
    
    async def load_from_directory(self, plugin_dir: Path) -> Optional[BasePlugin]:
        """
        从目录加载插件
        
        Args:
            plugin_dir: 插件目录路径
            
        Returns:
            Optional[BasePlugin]: 插件实例
        """
        try:
            # 检查插件目录结构
            if not self._validate_plugin_directory(plugin_dir):
                return None
            
            # 加载插件模块
            plugin_module = await self._load_plugin_module(plugin_dir)
            if not plugin_module:
                return None
            
            # 查找插件类
            plugin_class = self._find_plugin_class(plugin_module)
            if not plugin_class:
                logger.error(f"在模块中未找到插件类: {plugin_dir}")
                return None
            
            # 创建插件实例
            plugin_instance = plugin_class()
            
            logger.info(f"成功加载插件: {plugin_instance.metadata.name}")
            return plugin_instance
            
        except Exception as e:
            logger.error(f"加载插件失败 {plugin_dir}: {e}")
            return None
    
    def _validate_plugin_directory(self, plugin_dir: Path) -> bool:
        """验证插件目录结构"""
        # 检查必需文件
        required_files = ['plugin.json', '__init__.py']
        for file_name in required_files:
            if not (plugin_dir / file_name).exists():
                logger.error(f"插件目录缺少必需文件: {file_name}")
                return False
        
        return True
    
    async def _load_plugin_module(self, plugin_dir: Path) -> Optional[Any]:
        """加载插件模块"""
        try:
            plugin_name = plugin_dir.name
            module_path = plugin_dir / '__init__.py'
            
            # 创建模块规范
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_name}", 
                module_path
            )
            
            if not spec or not spec.loader:
                logger.error(f"无法创建模块规范: {plugin_dir}")
                return None
            
            # 加载模块
            module = importlib.util.module_from_spec(spec)
            
            # 添加到sys.modules以支持相对导入
            sys.modules[f"plugin_{plugin_name}"] = module
            
            # 执行模块
            spec.loader.exec_module(module)
            
            # 缓存模块
            self._loaded_modules[plugin_name] = module
            
            return module
            
        except Exception as e:
            logger.error(f"加载插件模块失败: {e}")
            return None
    
    def _find_plugin_class(self, module: Any) -> Optional[type]:
        """在模块中查找插件类"""
        try:
            # 查找继承自BasePlugin的类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                if (isinstance(attr, type) and 
                    issubclass(attr, BasePlugin) and 
                    attr != BasePlugin):
                    return attr
            
            # 如果没找到，尝试查找名为Plugin的类
            if hasattr(module, 'Plugin'):
                plugin_class = getattr(module, 'Plugin')
                if isinstance(plugin_class, type) and issubclass(plugin_class, BasePlugin):
                    return plugin_class
            
            return None
            
        except Exception as e:
            logger.error(f"查找插件类失败: {e}")
            return None
    
    async def load_from_file(self, plugin_file: Path) -> Optional[BasePlugin]:
        """
        从单个文件加载插件
        
        Args:
            plugin_file: 插件文件路径
            
        Returns:
            Optional[BasePlugin]: 插件实例
        """
        try:
            if not plugin_file.exists() or plugin_file.suffix != '.py':
                logger.error(f"无效的插件文件: {plugin_file}")
                return None
            
            plugin_name = plugin_file.stem
            
            # 创建模块规范
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_name}", 
                plugin_file
            )
            
            if not spec or not spec.loader:
                logger.error(f"无法创建模块规范: {plugin_file}")
                return None
            
            # 加载模块
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"plugin_{plugin_name}"] = module
            spec.loader.exec_module(module)
            
            # 查找插件类
            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                logger.error(f"在文件中未找到插件类: {plugin_file}")
                return None
            
            # 创建插件实例
            plugin_instance = plugin_class()
            
            # 缓存模块
            self._loaded_modules[plugin_name] = module
            
            logger.info(f"成功从文件加载插件: {plugin_instance.metadata.name}")
            return plugin_instance
            
        except Exception as e:
            logger.error(f"从文件加载插件失败 {plugin_file}: {e}")
            return None
    
    def unload_module(self, plugin_name: str) -> bool:
        """
        卸载插件模块
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 卸载是否成功
        """
        try:
            # 从缓存中移除
            if plugin_name in self._loaded_modules:
                del self._loaded_modules[plugin_name]
            
            # 从sys.modules中移除
            module_name = f"plugin_{plugin_name}"
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            logger.info(f"卸载插件模块: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"卸载插件模块失败 {plugin_name}: {e}")
            return False
    
    def reload_module(self, plugin_name: str) -> bool:
        """
        重新加载插件模块
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 重新加载是否成功
        """
        try:
            if plugin_name not in self._loaded_modules:
                logger.warning(f"插件模块未加载: {plugin_name}")
                return False
            
            module = self._loaded_modules[plugin_name]
            importlib.reload(module)
            
            logger.info(f"重新加载插件模块: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"重新加载插件模块失败 {plugin_name}: {e}")
            return False
    
    def get_loaded_modules(self) -> Dict[str, Any]:
        """获取已加载的模块"""
        return self._loaded_modules.copy()
    
    def is_module_loaded(self, plugin_name: str) -> bool:
        """检查模块是否已加载"""
        return plugin_name in self._loaded_modules
    
    def clear_cache(self):
        """清空模块缓存"""
        for plugin_name in list(self._loaded_modules.keys()):
            self.unload_module(plugin_name)
        
        logger.info("插件模块缓存已清空")
