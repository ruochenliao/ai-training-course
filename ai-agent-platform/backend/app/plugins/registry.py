"""
插件注册表

管理插件类的注册和查找。
"""

from typing import Dict, Type, List, Optional
import logging

from .base import BasePlugin, PluginType

logger = logging.getLogger(__name__)


class PluginRegistry:
    """插件注册表"""
    
    def __init__(self):
        self._plugins: Dict[str, Type[BasePlugin]] = {}
        self._plugins_by_type: Dict[PluginType, List[Type[BasePlugin]]] = {
            plugin_type: [] for plugin_type in PluginType
        }
    
    def register(self, plugin_class: Type[BasePlugin]) -> bool:
        """
        注册插件类
        
        Args:
            plugin_class: 插件类
            
        Returns:
            bool: 注册是否成功
        """
        try:
            # 创建临时实例获取元数据
            temp_instance = plugin_class()
            plugin_name = temp_instance.metadata.name
            plugin_type = temp_instance.metadata.plugin_type
            
            if plugin_name in self._plugins:
                logger.warning(f"插件 {plugin_name} 已存在，将被覆盖")
            
            self._plugins[plugin_name] = plugin_class
            
            # 按类型分类
            if plugin_class not in self._plugins_by_type[plugin_type]:
                self._plugins_by_type[plugin_type].append(plugin_class)
            
            logger.info(f"注册插件: {plugin_name} ({plugin_type.value})")
            return True
            
        except Exception as e:
            logger.error(f"注册插件失败: {e}")
            return False
    
    def unregister(self, plugin_name: str) -> bool:
        """
        取消注册插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 取消注册是否成功
        """
        if plugin_name not in self._plugins:
            logger.warning(f"插件 {plugin_name} 未注册")
            return True
        
        try:
            plugin_class = self._plugins[plugin_name]
            temp_instance = plugin_class()
            plugin_type = temp_instance.metadata.plugin_type
            
            # 从主注册表移除
            del self._plugins[plugin_name]
            
            # 从类型分类中移除
            if plugin_class in self._plugins_by_type[plugin_type]:
                self._plugins_by_type[plugin_type].remove(plugin_class)
            
            logger.info(f"取消注册插件: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"取消注册插件失败: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[Type[BasePlugin]]:
        """
        获取插件类
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[Type[BasePlugin]]: 插件类
        """
        return self._plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Type[BasePlugin]]:
        """
        根据类型获取插件类列表
        
        Args:
            plugin_type: 插件类型
            
        Returns:
            List[Type[BasePlugin]]: 插件类列表
        """
        return self._plugins_by_type.get(plugin_type, [])
    
    def get_all_plugins(self) -> List[Type[BasePlugin]]:
        """获取所有插件类"""
        return list(self._plugins.values())
    
    def get_plugin_names(self) -> List[str]:
        """获取所有插件名称"""
        return list(self._plugins.keys())
    
    def is_registered(self, plugin_name: str) -> bool:
        """检查插件是否已注册"""
        return plugin_name in self._plugins
    
    def get_plugin_count(self) -> int:
        """获取插件总数"""
        return len(self._plugins)
    
    def get_plugin_count_by_type(self, plugin_type: PluginType) -> int:
        """获取指定类型的插件数量"""
        return len(self._plugins_by_type.get(plugin_type, []))
    
    def search_plugins(self, keyword: str) -> List[Type[BasePlugin]]:
        """
        搜索插件
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[Type[BasePlugin]]: 匹配的插件类列表
        """
        results = []
        keyword_lower = keyword.lower()
        
        for plugin_class in self._plugins.values():
            try:
                temp_instance = plugin_class()
                metadata = temp_instance.metadata
                
                # 在名称、描述、标签中搜索
                if (keyword_lower in metadata.name.lower() or
                    keyword_lower in metadata.description.lower() or
                    any(keyword_lower in tag.lower() for tag in metadata.tags)):
                    results.append(plugin_class)
                    
            except Exception as e:
                logger.error(f"搜索插件时出错: {e}")
        
        return results
    
    def validate_plugin_class(self, plugin_class: Type[BasePlugin]) -> bool:
        """
        验证插件类是否有效
        
        Args:
            plugin_class: 插件类
            
        Returns:
            bool: 插件类是否有效
        """
        try:
            # 检查是否继承自BasePlugin
            if not issubclass(plugin_class, BasePlugin):
                logger.error("插件类必须继承自BasePlugin")
                return False
            
            # 尝试创建实例
            temp_instance = plugin_class()
            
            # 检查必需的属性和方法
            if not hasattr(temp_instance, 'metadata'):
                logger.error("插件类必须有metadata属性")
                return False
            
            metadata = temp_instance.metadata
            if not metadata.name or not metadata.version:
                logger.error("插件元数据必须包含name和version")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证插件类失败: {e}")
            return False
    
    def clear(self):
        """清空注册表"""
        self._plugins.clear()
        for plugin_type in PluginType:
            self._plugins_by_type[plugin_type].clear()
        logger.info("插件注册表已清空")


def plugin(plugin_class: Type[BasePlugin]) -> Type[BasePlugin]:
    """
    插件装饰器
    
    Args:
        plugin_class: 插件类
        
    Returns:
        Type[BasePlugin]: 插件类
    """
    plugin_registry.register(plugin_class)
    return plugin_class


# 全局插件注册表实例
plugin_registry = PluginRegistry()
