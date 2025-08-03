"""
插件系统

提供插件的注册、加载、管理功能。
"""

from .manager import PluginManager
from .base import BasePlugin, PluginMetadata
from .registry import plugin_registry
from .loader import PluginLoader

__all__ = [
    'PluginManager',
    'BasePlugin', 
    'PluginMetadata',
    'plugin_registry',
    'PluginLoader'
]
