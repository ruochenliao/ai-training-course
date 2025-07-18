"""
系统配置管理服务 - 第四阶段核心组件
提供动态配置管理、配置验证、配置热更新等功能
"""

import json
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
from loguru import logger
import redis
from sqlalchemy.orm import Session

from app.core import settings
from app.core.database import get_db


@dataclass
class ConfigItem:
    """配置项数据类"""
    key: str
    value: Any
    description: str
    category: str
    data_type: str  # string, int, float, bool, json
    is_sensitive: bool = False
    requires_restart: bool = False
    created_at: str = None
    updated_at: str = None
    updated_by: Optional[int] = None


@dataclass
class ConfigCategory:
    """配置分类"""
    name: str
    description: str
    items: List[ConfigItem]


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.redis_client = None
        self.config_cache = {}
        self.config_file_path = Path("config/dynamic_config.json")
        
        # 初始化Redis连接
        try:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                decode_responses=True
            )
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis连接失败，将使用文件存储: {e}")
            self.redis_client = None
        
        # 确保配置目录存在
        self.config_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载默认配置
        self._load_default_configs()
        
        # 从存储加载配置
        self._load_configs()
    
    def _load_default_configs(self):
        """加载默认配置"""
        default_configs = {
            # 系统配置
            "system.max_upload_size": ConfigItem(
                key="system.max_upload_size",
                value=100 * 1024 * 1024,  # 100MB
                description="最大文件上传大小（字节）",
                category="system",
                data_type="int"
            ),
            "system.session_timeout": ConfigItem(
                key="system.session_timeout",
                value=3600,  # 1小时
                description="会话超时时间（秒）",
                category="system",
                data_type="int"
            ),
            "system.max_concurrent_users": ConfigItem(
                key="system.max_concurrent_users",
                value=1000,
                description="最大并发用户数",
                category="system",
                data_type="int"
            ),
            
            # 安全配置
            "security.password_min_length": ConfigItem(
                key="security.password_min_length",
                value=8,
                description="密码最小长度",
                category="security",
                data_type="int"
            ),
            "security.max_login_attempts": ConfigItem(
                key="security.max_login_attempts",
                value=5,
                description="最大登录尝试次数",
                category="security",
                data_type="int"
            ),
            "security.lockout_duration": ConfigItem(
                key="security.lockout_duration",
                value=900,  # 15分钟
                description="账户锁定时间（秒）",
                category="security",
                data_type="int"
            ),
            "security.enable_2fa": ConfigItem(
                key="security.enable_2fa",
                value=False,
                description="启用双因素认证",
                category="security",
                data_type="bool"
            ),
            
            # RAG配置
            "rag.default_top_k": ConfigItem(
                key="rag.default_top_k",
                value=10,
                description="默认检索结果数量",
                category="rag",
                data_type="int"
            ),
            "rag.similarity_threshold": ConfigItem(
                key="rag.similarity_threshold",
                value=0.7,
                description="相似度阈值",
                category="rag",
                data_type="float"
            ),
            "rag.enable_rerank": ConfigItem(
                key="rag.enable_rerank",
                value=True,
                description="启用重排序",
                category="rag",
                data_type="bool"
            ),
            "rag.max_context_length": ConfigItem(
                key="rag.max_context_length",
                value=4000,
                description="最大上下文长度",
                category="rag",
                data_type="int"
            ),
            
            # 缓存配置
            "cache.ttl_default": ConfigItem(
                key="cache.ttl_default",
                value=3600,  # 1小时
                description="默认缓存过期时间（秒）",
                category="cache",
                data_type="int"
            ),
            "cache.max_memory_usage": ConfigItem(
                key="cache.max_memory_usage",
                value=512 * 1024 * 1024,  # 512MB
                description="最大缓存内存使用（字节）",
                category="cache",
                data_type="int"
            ),
            
            # 监控配置
            "monitoring.metrics_retention_days": ConfigItem(
                key="monitoring.metrics_retention_days",
                value=30,
                description="指标数据保留天数",
                category="monitoring",
                data_type="int"
            ),
            "monitoring.alert_threshold_cpu": ConfigItem(
                key="monitoring.alert_threshold_cpu",
                value=80.0,
                description="CPU使用率告警阈值（%）",
                category="monitoring",
                data_type="float"
            ),
            "monitoring.alert_threshold_memory": ConfigItem(
                key="monitoring.alert_threshold_memory",
                value=85.0,
                description="内存使用率告警阈值（%）",
                category="monitoring",
                data_type="float"
            ),
            
            # API配置
            "api.rate_limit_per_minute": ConfigItem(
                key="api.rate_limit_per_minute",
                value=100,
                description="每分钟API调用限制",
                category="api",
                data_type="int"
            ),
            "api.enable_cors": ConfigItem(
                key="api.enable_cors",
                value=True,
                description="启用CORS",
                category="api",
                data_type="bool"
            ),
            "api.request_timeout": ConfigItem(
                key="api.request_timeout",
                value=30,
                description="API请求超时时间（秒）",
                category="api",
                data_type="int"
            )
        }
        
        # 设置创建时间
        now = datetime.utcnow().isoformat()
        for config in default_configs.values():
            config.created_at = now
            config.updated_at = now
        
        self.config_cache.update(default_configs)
    
    def _load_configs(self):
        """从存储加载配置"""
        # 从Redis加载
        if self.redis_client:
            try:
                keys = self.redis_client.keys("config:*")
                for key in keys:
                    config_key = key.replace("config:", "")
                    config_data = self.redis_client.get(key)
                    if config_data:
                        config_dict = json.loads(config_data)
                        self.config_cache[config_key] = ConfigItem(**config_dict)
                logger.info(f"从Redis加载了{len(keys)}个配置项")
                return
            except Exception as e:
                logger.error(f"从Redis加载配置失败: {e}")
        
        # 从文件加载
        if self.config_file_path.exists():
            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                for key, data in config_data.items():
                    self.config_cache[key] = ConfigItem(**data)
                
                logger.info(f"从文件加载了{len(config_data)}个配置项")
            except Exception as e:
                logger.error(f"从文件加载配置失败: {e}")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        config_item = self.config_cache.get(key)
        if config_item:
            return config_item.value
        return default
    
    def get_config_item(self, key: str) -> Optional[ConfigItem]:
        """获取配置项"""
        return self.config_cache.get(key)
    
    def set_config(self, key: str, value: Any, user_id: Optional[int] = None) -> bool:
        """设置配置值"""
        try:
            config_item = self.config_cache.get(key)
            if not config_item:
                logger.warning(f"配置项不存在: {key}")
                return False
            
            # 验证数据类型
            if not self._validate_config_value(config_item.data_type, value):
                logger.error(f"配置值类型不匹配: {key} = {value}")
                return False
            
            # 更新配置
            config_item.value = value
            config_item.updated_at = datetime.utcnow().isoformat()
            config_item.updated_by = user_id
            
            # 保存到存储
            self._save_config(config_item)
            
            logger.info(f"配置已更新: {key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"设置配置失败: {e}")
            return False
    
    def _validate_config_value(self, data_type: str, value: Any) -> bool:
        """验证配置值类型"""
        try:
            if data_type == "string":
                return isinstance(value, str)
            elif data_type == "int":
                return isinstance(value, int) or (isinstance(value, str) and value.isdigit())
            elif data_type == "float":
                return isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '').isdigit())
            elif data_type == "bool":
                return isinstance(value, bool) or value in ["true", "false", "True", "False", 1, 0]
            elif data_type == "json":
                if isinstance(value, str):
                    json.loads(value)  # 验证JSON格式
                return True
            return False
        except:
            return False
    
    def _save_config(self, config_item: ConfigItem):
        """保存配置到存储"""
        config_data = asdict(config_item)
        
        # 保存到Redis
        if self.redis_client:
            try:
                self.redis_client.set(
                    f"config:{config_item.key}",
                    json.dumps(config_data, ensure_ascii=False)
                )
            except Exception as e:
                logger.error(f"保存配置到Redis失败: {e}")
        
        # 保存到文件
        self._save_configs_to_file()
    
    def _save_configs_to_file(self):
        """保存所有配置到文件"""
        try:
            config_data = {}
            for key, config_item in self.config_cache.items():
                config_data[key] = asdict(config_item)
            
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存配置到文件失败: {e}")
    
    def get_configs_by_category(self, category: str) -> List[ConfigItem]:
        """按分类获取配置"""
        return [config for config in self.config_cache.values() if config.category == category]
    
    def get_all_categories(self) -> List[ConfigCategory]:
        """获取所有配置分类"""
        categories = {}
        
        for config_item in self.config_cache.values():
            category_name = config_item.category
            if category_name not in categories:
                categories[category_name] = ConfigCategory(
                    name=category_name,
                    description=self._get_category_description(category_name),
                    items=[]
                )
            categories[category_name].items.append(config_item)
        
        return list(categories.values())
    
    def _get_category_description(self, category: str) -> str:
        """获取分类描述"""
        descriptions = {
            "system": "系统基础配置",
            "security": "安全相关配置",
            "rag": "RAG检索配置",
            "cache": "缓存配置",
            "monitoring": "监控配置",
            "api": "API接口配置"
        }
        return descriptions.get(category, f"{category}配置")
    
    def reset_config(self, key: str, user_id: Optional[int] = None) -> bool:
        """重置配置为默认值"""
        try:
            # 重新加载默认配置
            temp_manager = ConfigManager.__new__(ConfigManager)
            temp_manager.config_cache = {}
            temp_manager._load_default_configs()
            
            default_config = temp_manager.config_cache.get(key)
            if not default_config:
                logger.warning(f"默认配置不存在: {key}")
                return False
            
            # 重置配置
            config_item = self.config_cache.get(key)
            if config_item:
                config_item.value = default_config.value
                config_item.updated_at = datetime.utcnow().isoformat()
                config_item.updated_by = user_id
                
                # 保存到存储
                self._save_config(config_item)
                
                logger.info(f"配置已重置: {key}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"重置配置失败: {e}")
            return False
    
    def validate_all_configs(self) -> Dict[str, List[str]]:
        """验证所有配置"""
        validation_errors = {}
        
        for key, config_item in self.config_cache.items():
            errors = []
            
            # 验证数据类型
            if not self._validate_config_value(config_item.data_type, config_item.value):
                errors.append(f"数据类型不匹配，期望: {config_item.data_type}")
            
            # 验证特定配置的业务规则
            business_errors = self._validate_business_rules(config_item)
            errors.extend(business_errors)
            
            if errors:
                validation_errors[key] = errors
        
        return validation_errors
    
    def _validate_business_rules(self, config_item: ConfigItem) -> List[str]:
        """验证业务规则"""
        errors = []
        key = config_item.key
        value = config_item.value
        
        # 系统配置验证
        if key == "system.max_upload_size" and value <= 0:
            errors.append("最大上传大小必须大于0")
        elif key == "system.session_timeout" and value < 300:  # 最少5分钟
            errors.append("会话超时时间不能少于300秒")
        elif key == "system.max_concurrent_users" and value <= 0:
            errors.append("最大并发用户数必须大于0")
        
        # 安全配置验证
        elif key == "security.password_min_length" and value < 6:
            errors.append("密码最小长度不能少于6位")
        elif key == "security.max_login_attempts" and value <= 0:
            errors.append("最大登录尝试次数必须大于0")
        elif key == "security.lockout_duration" and value < 60:
            errors.append("锁定时间不能少于60秒")
        
        # RAG配置验证
        elif key == "rag.default_top_k" and (value <= 0 or value > 100):
            errors.append("默认检索结果数量必须在1-100之间")
        elif key == "rag.similarity_threshold" and (value < 0 or value > 1):
            errors.append("相似度阈值必须在0-1之间")
        elif key == "rag.max_context_length" and value <= 0:
            errors.append("最大上下文长度必须大于0")
        
        return errors
    
    def export_configs(self) -> Dict[str, Any]:
        """导出所有配置"""
        export_data = {}
        for key, config_item in self.config_cache.items():
            # 敏感配置不导出值
            if config_item.is_sensitive:
                export_data[key] = {**asdict(config_item), "value": "***"}
            else:
                export_data[key] = asdict(config_item)
        
        return export_data
    
    def import_configs(self, config_data: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, str]:
        """导入配置"""
        results = {}
        
        for key, data in config_data.items():
            try:
                if key in self.config_cache:
                    # 跳过敏感配置
                    if self.config_cache[key].is_sensitive and data.get("value") == "***":
                        results[key] = "跳过敏感配置"
                        continue
                    
                    # 更新配置
                    if self.set_config(key, data["value"], user_id):
                        results[key] = "成功"
                    else:
                        results[key] = "失败"
                else:
                    results[key] = "配置不存在"
            except Exception as e:
                results[key] = f"错误: {str(e)}"
        
        return results


# 全局配置管理器实例
config_manager = ConfigManager()
