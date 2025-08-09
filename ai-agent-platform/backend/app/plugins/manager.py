"""
# Copyright (c) 2025 左岚. All rights reserved.

插件管理器

负责插件的加载、激活、停用、卸载等管理功能。
"""

# # Standard library imports
import asyncio
import importlib
import importlib.util
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

# # Local folder imports
from .base import BasePlugin, PluginMetadata, PluginStatus, PluginType
from .loader import PluginLoader
from .registry import plugin_registry

logger = logging.getLogger(__name__)


class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.loaded_plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        self.loader = PluginLoader()
        
        # 确保插件目录存在
        self.plugins_dir.mkdir(exist_ok=True)
        
        # 加载插件配置
        self._load_plugin_configs()
    
    def _load_plugin_configs(self):
        """加载插件配置"""
        config_file = self.plugins_dir / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.plugin_configs = json.load(f)
            except Exception as e:
                logger.error(f"加载插件配置失败: {e}")
                self.plugin_configs = {}
    
    def _save_plugin_configs(self):
        """保存插件配置"""
        config_file = self.plugins_dir / "config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.plugin_configs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存插件配置失败: {e}")
    
    async def discover_plugins(self) -> List[PluginMetadata]:
        """
        发现可用插件
        
        Returns:
            List[PluginMetadata]: 插件元数据列表
        """
        discovered_plugins = []
        
        # 扫描插件目录
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('.'):
                metadata = await self._load_plugin_metadata(plugin_dir)
                if metadata:
                    discovered_plugins.append(metadata)
        
        # 扫描注册的插件类
        for plugin_class in plugin_registry.get_all_plugins():
            try:
                # 创建临时实例获取元数据
                temp_instance = plugin_class()
                discovered_plugins.append(temp_instance.metadata)
            except Exception as e:
                logger.error(f"获取插件元数据失败: {e}")
        
        return discovered_plugins
    
    async def _load_plugin_metadata(self, plugin_dir: Path) -> Optional[PluginMetadata]:
        """加载插件元数据"""
        metadata_file = plugin_dir / "plugin.json"
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
            
            return PluginMetadata(
                name=metadata_dict['name'],
                version=metadata_dict['version'],
                description=metadata_dict['description'],
                author=metadata_dict['author'],
                plugin_type=PluginType(metadata_dict['type']),
                dependencies=metadata_dict.get('dependencies', []),
                config_schema=metadata_dict.get('config_schema', {}),
                permissions=metadata_dict.get('permissions', []),
                min_platform_version=metadata_dict.get('min_platform_version', '1.0.0'),
                max_platform_version=metadata_dict.get('max_platform_version'),
                homepage=metadata_dict.get('homepage'),
                repository=metadata_dict.get('repository'),
                license=metadata_dict.get('license'),
                tags=metadata_dict.get('tags', [])
            )
        except Exception as e:
            logger.error(f"加载插件元数据失败 {plugin_dir}: {e}")
            return None
    
    async def load_plugin(self, plugin_name: str) -> bool:
        """
        加载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 加载是否成功
        """
        if plugin_name in self.loaded_plugins:
            logger.warning(f"插件 {plugin_name} 已经加载")
            return True
        
        try:
            # 尝试从注册表加载
            plugin_class = plugin_registry.get_plugin(plugin_name)
            if plugin_class:
                config = self.plugin_configs.get(plugin_name, {})
                plugin_instance = plugin_class(config)
                self.loaded_plugins[plugin_name] = plugin_instance
                logger.info(f"从注册表加载插件: {plugin_name}")
                return True
            
            # 尝试从文件系统加载
            plugin_dir = self.plugins_dir / plugin_name
            if plugin_dir.exists():
                plugin_instance = await self.loader.load_from_directory(plugin_dir)
                if plugin_instance:
                    config = self.plugin_configs.get(plugin_name, {})
                    plugin_instance.config = config
                    self.loaded_plugins[plugin_name] = plugin_instance
                    logger.info(f"从文件系统加载插件: {plugin_name}")
                    return True
            
            logger.error(f"未找到插件: {plugin_name}")
            return False
            
        except Exception as e:
            logger.error(f"加载插件失败 {plugin_name}: {e}")
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 卸载是否成功
        """
        if plugin_name not in self.loaded_plugins:
            logger.warning(f"插件 {plugin_name} 未加载")
            return True
        
        try:
            plugin = self.loaded_plugins[plugin_name]
            
            # 如果插件处于激活状态，先停用
            if plugin.status == PluginStatus.ACTIVE:
                await self.deactivate_plugin(plugin_name)
            
            # 清理资源
            await plugin.cleanup()
            
            # 从加载列表中移除
            del self.loaded_plugins[plugin_name]
            
            logger.info(f"卸载插件: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"卸载插件失败 {plugin_name}: {e}")
            return False
    
    async def activate_plugin(self, plugin_name: str) -> bool:
        """
        激活插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 激活是否成功
        """
        if plugin_name not in self.loaded_plugins:
            # 尝试先加载插件
            if not await self.load_plugin(plugin_name):
                return False
        
        plugin = self.loaded_plugins[plugin_name]
        
        # 检查依赖
        if not await self._check_dependencies(plugin):
            logger.error(f"插件 {plugin_name} 依赖检查失败")
            return False
        
        return await plugin.activate()
    
    async def deactivate_plugin(self, plugin_name: str) -> bool:
        """
        停用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 停用是否成功
        """
        if plugin_name not in self.loaded_plugins:
            logger.warning(f"插件 {plugin_name} 未加载")
            return True
        
        plugin = self.loaded_plugins[plugin_name]
        return await plugin.deactivate()
    
    async def _check_dependencies(self, plugin: BasePlugin) -> bool:
        """检查插件依赖"""
        for dependency in plugin.metadata.dependencies:
            if dependency not in self.loaded_plugins:
                logger.error(f"缺少依赖插件: {dependency}")
                return False
            
            dep_plugin = self.loaded_plugins[dependency]
            if dep_plugin.status != PluginStatus.ACTIVE:
                logger.error(f"依赖插件未激活: {dependency}")
                return False
        
        return True
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取插件实例"""
        return self.loaded_plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """根据类型获取插件列表"""
        return [
            plugin for plugin in self.loaded_plugins.values()
            if plugin.metadata.plugin_type == plugin_type
        ]
    
    def get_active_plugins(self) -> List[BasePlugin]:
        """获取激活的插件列表"""
        return [
            plugin for plugin in self.loaded_plugins.values()
            if plugin.status == PluginStatus.ACTIVE
        ]
    
    def get_plugin_status(self, plugin_name: str) -> Optional[PluginStatus]:
        """获取插件状态"""
        plugin = self.loaded_plugins.get(plugin_name)
        return plugin.status if plugin else None
    
    async def update_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """
        更新插件配置
        
        Args:
            plugin_name: 插件名称
            config: 新配置
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 更新内存中的配置
            self.plugin_configs[plugin_name] = config
            
            # 如果插件已加载，更新插件实例的配置
            if plugin_name in self.loaded_plugins:
                plugin = self.loaded_plugins[plugin_name]
                if not plugin.update_config(config):
                    return False
            
            # 保存配置到文件
            self._save_plugin_configs()
            
            logger.info(f"更新插件配置: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"更新插件配置失败 {plugin_name}: {e}")
            return False
    
    async def install_plugin(self, plugin_path: str) -> bool:
        """
        安装插件
        
        Args:
            plugin_path: 插件文件路径或URL
            
        Returns:
            bool: 安装是否成功
        """
        try:
            # 这里可以实现从文件或URL安装插件的逻辑
            # 包括解压、验证、复制文件等
            logger.info(f"安装插件: {plugin_path}")
            return True
            
        except Exception as e:
            logger.error(f"安装插件失败 {plugin_path}: {e}")
            return False
    
    async def uninstall_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 卸载是否成功
        """
        try:
            # 先停用和卸载插件
            await self.unload_plugin(plugin_name)
            
            # 删除插件文件
            plugin_dir = self.plugins_dir / plugin_name
            if plugin_dir.exists():
                # # Standard library imports
                import shutil
                shutil.rmtree(plugin_dir)
            
            # 删除配置
            if plugin_name in self.plugin_configs:
                del self.plugin_configs[plugin_name]
                self._save_plugin_configs()
            
            logger.info(f"卸载插件: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"卸载插件失败 {plugin_name}: {e}")
            return False
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """
        重新加载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 重新加载是否成功
        """
        try:
            # 先卸载
            await self.unload_plugin(plugin_name)
            
            # 重新加载
            if await self.load_plugin(plugin_name):
                # 如果配置中标记为自动激活，则激活插件
                config = self.plugin_configs.get(plugin_name, {})
                if config.get('auto_activate', False):
                    await self.activate_plugin(plugin_name)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"重新加载插件失败 {plugin_name}: {e}")
            return False
    
    async def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件详细信息"""
        plugin = self.loaded_plugins.get(plugin_name)
        if not plugin:
            return None
        
        return {
            'name': plugin.metadata.name,
            'version': plugin.metadata.version,
            'description': plugin.metadata.description,
            'author': plugin.metadata.author,
            'type': plugin.metadata.plugin_type.value,
            'status': plugin.status.value,
            'dependencies': plugin.metadata.dependencies,
            'permissions': plugin.metadata.permissions,
            'config': plugin.config,
            'tags': plugin.metadata.tags
        }


# 全局插件管理器实例
plugin_manager = PluginManager()
