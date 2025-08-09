"""
# Copyright (c) 2025 左岚. All rights reserved.

插件系统

提供插件的注册、加载、管理功能。
"""

# # Local folder imports
from .base import BasePlugin, PluginMetadata
from .loader import PluginLoader
from .manager import PluginManager
from .registry import plugin_registry

__all__ = [
    'PluginManager',
    'BasePlugin', 
    'PluginMetadata',
    'plugin_registry',
    'PluginLoader'
]
