"""
系统配置管理服务
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional

import redis.asyncio as redis
from app.core.config import settings
from loguru import logger

from app.core.exceptions import ConfigException


class ConfigType(Enum):
    """配置类型"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"
    PASSWORD = "password"


class ConfigCategory(Enum):
    """配置分类"""
    SYSTEM = "system"
    DATABASE = "database"
    AI_MODEL = "ai_model"
    SECURITY = "security"
    NOTIFICATION = "notification"
    BACKUP = "backup"
    CACHE = "cache"
    SEARCH = "search"
    UI = "ui"
    INTEGRATION = "integration"


@dataclass
class ConfigItem:
    """配置项"""
    key: str
    value: Any
    type: ConfigType
    category: ConfigCategory
    description: str = ""
    default_value: Any = None
    required: bool = False
    readonly: bool = False
    sensitive: bool = False
    validation_rule: Optional[str] = None
    options: List[Any] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.now)
    updated_by: Optional[str] = None


@dataclass
class ConfigChange:
    """配置变更记录"""
    id: str
    config_key: str
    old_value: Any
    new_value: Any
    changed_at: datetime
    changed_by: str
    reason: str = ""


class ConfigService:
    """系统配置管理服务类"""
    
    def __init__(self):
        """初始化配置服务"""
        self.redis_client = None
        self.config_cache: Dict[str, ConfigItem] = {}
        self.change_history: List[ConfigChange] = []
        
        # 初始化默认配置
        self._init_default_configs()
        
        logger.info("系统配置管理服务初始化完成")
    
    async def initialize(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=5,  # 使用专门的数据库
                decode_responses=True
            )
            
            await self.redis_client.ping()
            
            # 加载配置
            await self._load_configs()
            
            logger.info("配置服务Redis连接初始化成功")
            
        except Exception as e:
            logger.error(f"配置服务Redis连接初始化失败: {e}")
            raise ConfigException(f"配置服务初始化失败: {e}")
    
    def _init_default_configs(self):
        """初始化默认配置"""
        default_configs = [
            # 系统配置
            ConfigItem(
                key="system.app_name",
                value="企业级RAG知识库系统",
                type=ConfigType.STRING,
                category=ConfigCategory.SYSTEM,
                description="应用程序名称",
                default_value="企业级RAG知识库系统"
            ),
            ConfigItem(
                key="system.version",
                value="1.0.0",
                type=ConfigType.STRING,
                category=ConfigCategory.SYSTEM,
                description="系统版本",
                readonly=True
            ),
            ConfigItem(
                key="system.debug_mode",
                value=False,
                type=ConfigType.BOOLEAN,
                category=ConfigCategory.SYSTEM,
                description="调试模式",
                default_value=False
            ),
            ConfigItem(
                key="system.max_upload_size",
                value=100,
                type=ConfigType.INTEGER,
                category=ConfigCategory.SYSTEM,
                description="最大上传文件大小(MB)",
                default_value=100,
                validation_rule="min:1,max:1000"
            ),
            
            # AI模型配置
            ConfigItem(
                key="ai.embedding_model",
                value="text-embedding-ada-002",
                type=ConfigType.STRING,
                category=ConfigCategory.AI_MODEL,
                description="嵌入模型",
                options=["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"]
            ),
            ConfigItem(
                key="ai.chat_model",
                value="gpt-3.5-turbo",
                type=ConfigType.STRING,
                category=ConfigCategory.AI_MODEL,
                description="聊天模型",
                options=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
            ),
            ConfigItem(
                key="ai.max_tokens",
                value=4000,
                type=ConfigType.INTEGER,
                category=ConfigCategory.AI_MODEL,
                description="最大token数",
                default_value=4000,
                validation_rule="min:100,max:32000"
            ),
            ConfigItem(
                key="ai.temperature",
                value=0.7,
                type=ConfigType.FLOAT,
                category=ConfigCategory.AI_MODEL,
                description="模型温度",
                default_value=0.7,
                validation_rule="min:0,max:2"
            ),
            
            # 安全配置
            ConfigItem(
                key="security.session_timeout",
                value=3600,
                type=ConfigType.INTEGER,
                category=ConfigCategory.SECURITY,
                description="会话超时时间(秒)",
                default_value=3600,
                validation_rule="min:300,max:86400"
            ),
            ConfigItem(
                key="security.password_min_length",
                value=8,
                type=ConfigType.INTEGER,
                category=ConfigCategory.SECURITY,
                description="密码最小长度",
                default_value=8,
                validation_rule="min:6,max:128"
            ),
            ConfigItem(
                key="security.max_login_attempts",
                value=5,
                type=ConfigType.INTEGER,
                category=ConfigCategory.SECURITY,
                description="最大登录尝试次数",
                default_value=5,
                validation_rule="min:3,max:10"
            ),
            
            # 通知配置
            ConfigItem(
                key="notification.email_enabled",
                value=True,
                type=ConfigType.BOOLEAN,
                category=ConfigCategory.NOTIFICATION,
                description="启用邮件通知",
                default_value=True
            ),
            ConfigItem(
                key="notification.smtp_host",
                value="smtp.gmail.com",
                type=ConfigType.STRING,
                category=ConfigCategory.NOTIFICATION,
                description="SMTP服务器",
                default_value="smtp.gmail.com"
            ),
            ConfigItem(
                key="notification.smtp_port",
                value=587,
                type=ConfigType.INTEGER,
                category=ConfigCategory.NOTIFICATION,
                description="SMTP端口",
                default_value=587,
                validation_rule="min:1,max:65535"
            ),
            
            # 备份配置
            ConfigItem(
                key="backup.auto_backup_enabled",
                value=True,
                type=ConfigType.BOOLEAN,
                category=ConfigCategory.BACKUP,
                description="启用自动备份",
                default_value=True
            ),
            ConfigItem(
                key="backup.retention_days",
                value=30,
                type=ConfigType.INTEGER,
                category=ConfigCategory.BACKUP,
                description="备份保留天数",
                default_value=30,
                validation_rule="min:1,max:365"
            ),
            
            # 缓存配置
            ConfigItem(
                key="cache.default_ttl",
                value=3600,
                type=ConfigType.INTEGER,
                category=ConfigCategory.CACHE,
                description="默认缓存过期时间(秒)",
                default_value=3600,
                validation_rule="min:60,max:86400"
            ),
            ConfigItem(
                key="cache.max_memory_usage",
                value=512,
                type=ConfigType.INTEGER,
                category=ConfigCategory.CACHE,
                description="最大内存使用(MB)",
                default_value=512,
                validation_rule="min:64,max:4096"
            ),
            
            # 搜索配置
            ConfigItem(
                key="search.max_results",
                value=20,
                type=ConfigType.INTEGER,
                category=ConfigCategory.SEARCH,
                description="最大搜索结果数",
                default_value=20,
                validation_rule="min:5,max:100"
            ),
            ConfigItem(
                key="search.similarity_threshold",
                value=0.7,
                type=ConfigType.FLOAT,
                category=ConfigCategory.SEARCH,
                description="相似度阈值",
                default_value=0.7,
                validation_rule="min:0,max:1"
            ),
            
            # UI配置
            ConfigItem(
                key="ui.theme",
                value="light",
                type=ConfigType.STRING,
                category=ConfigCategory.UI,
                description="界面主题",
                default_value="light",
                options=["light", "dark", "auto"]
            ),
            ConfigItem(
                key="ui.language",
                value="zh-CN",
                type=ConfigType.STRING,
                category=ConfigCategory.UI,
                description="界面语言",
                default_value="zh-CN",
                options=["zh-CN", "en-US", "ja-JP", "ko-KR"]
            ),
            ConfigItem(
                key="ui.items_per_page",
                value=20,
                type=ConfigType.INTEGER,
                category=ConfigCategory.UI,
                description="每页显示条目数",
                default_value=20,
                validation_rule="min:10,max:100"
            )
        ]
        
        for config in default_configs:
            self.config_cache[config.key] = config
    
    async def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        try:
            # 先从缓存获取
            if key in self.config_cache:
                return self.config_cache[key].value
            
            # 从Redis获取
            if self.redis_client:
                value = await self.redis_client.hget("configs", key)
                if value is not None:
                    # 反序列化值
                    config_data = json.loads(value)
                    config_item = self._deserialize_config(config_data)
                    self.config_cache[key] = config_item
                    return config_item.value
            
            return default
            
        except Exception as e:
            logger.error(f"获取配置失败: {key} - {e}")
            return default
    
    async def set_config(
        self,
        key: str,
        value: Any,
        updated_by: str = "system"
    ) -> bool:
        """设置配置值"""
        try:
            # 检查配置是否存在
            if key not in self.config_cache:
                raise ConfigException(f"配置项不存在: {key}")
            
            config_item = self.config_cache[key]
            
            # 检查是否只读
            if config_item.readonly:
                raise ConfigException(f"配置项为只读: {key}")
            
            # 验证值
            if not self._validate_value(config_item, value):
                raise ConfigException(f"配置值验证失败: {key}")
            
            # 记录变更
            old_value = config_item.value
            change = ConfigChange(
                id=f"change_{datetime.now().timestamp()}",
                config_key=key,
                old_value=old_value,
                new_value=value,
                changed_at=datetime.now(),
                changed_by=updated_by
            )
            self.change_history.append(change)
            
            # 更新配置
            config_item.value = value
            config_item.updated_at = datetime.now()
            config_item.updated_by = updated_by
            
            # 保存到Redis
            if self.redis_client:
                config_data = self._serialize_config(config_item)
                await self.redis_client.hset("configs", key, json.dumps(config_data))
            
            logger.info(f"配置已更新: {key} = {value} (by {updated_by})")
            return True
            
        except Exception as e:
            logger.error(f"设置配置失败: {key} - {e}")
            return False
    
    async def get_configs_by_category(self, category: ConfigCategory) -> Dict[str, Any]:
        """按分类获取配置"""
        try:
            configs = {}
            for key, config_item in self.config_cache.items():
                if config_item.category == category:
                    configs[key] = {
                        "value": config_item.value,
                        "type": config_item.type.value,
                        "description": config_item.description,
                        "readonly": config_item.readonly,
                        "sensitive": config_item.sensitive,
                        "options": config_item.options,
                        "validation_rule": config_item.validation_rule,
                        "updated_at": config_item.updated_at.isoformat(),
                        "updated_by": config_item.updated_by
                    }
            
            return configs
            
        except Exception as e:
            logger.error(f"按分类获取配置失败: {category} - {e}")
            return {}
    
    async def get_all_configs(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """获取所有配置"""
        try:
            configs = {}
            for key, config_item in self.config_cache.items():
                if config_item.sensitive and not include_sensitive:
                    continue
                
                configs[key] = {
                    "value": config_item.value if not config_item.sensitive else "***",
                    "type": config_item.type.value,
                    "category": config_item.category.value,
                    "description": config_item.description,
                    "readonly": config_item.readonly,
                    "sensitive": config_item.sensitive,
                    "options": config_item.options,
                    "validation_rule": config_item.validation_rule,
                    "updated_at": config_item.updated_at.isoformat(),
                    "updated_by": config_item.updated_by
                }
            
            return configs
            
        except Exception as e:
            logger.error(f"获取所有配置失败: {e}")
            return {}
    
    async def reset_config(self, key: str, updated_by: str = "system") -> bool:
        """重置配置为默认值"""
        try:
            if key not in self.config_cache:
                raise ConfigException(f"配置项不存在: {key}")
            
            config_item = self.config_cache[key]
            
            if config_item.readonly:
                raise ConfigException(f"配置项为只读: {key}")
            
            if config_item.default_value is not None:
                return await self.set_config(key, config_item.default_value, updated_by)
            else:
                logger.warning(f"配置项没有默认值: {key}")
                return False
                
        except Exception as e:
            logger.error(f"重置配置失败: {key} - {e}")
            return False
    
    async def export_configs(self, category: Optional[ConfigCategory] = None) -> Dict[str, Any]:
        """导出配置"""
        try:
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "version": "1.0",
                "configs": {}
            }
            
            for key, config_item in self.config_cache.items():
                if category and config_item.category != category:
                    continue
                
                if not config_item.sensitive:  # 不导出敏感配置
                    export_data["configs"][key] = {
                        "value": config_item.value,
                        "type": config_item.type.value,
                        "category": config_item.category.value,
                        "description": config_item.description
                    }
            
            return export_data
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return {}
    
    async def import_configs(
        self,
        config_data: Dict[str, Any],
        updated_by: str = "system",
        overwrite: bool = False
    ) -> Dict[str, bool]:
        """导入配置"""
        try:
            results = {}
            
            configs = config_data.get("configs", {})
            for key, config_info in configs.items():
                try:
                    if key in self.config_cache:
                        if overwrite or self.config_cache[key].value == self.config_cache[key].default_value:
                            success = await self.set_config(key, config_info["value"], updated_by)
                            results[key] = success
                        else:
                            results[key] = False  # 跳过已存在的配置
                    else:
                        logger.warning(f"导入时发现未知配置项: {key}")
                        results[key] = False
                        
                except Exception as e:
                    logger.error(f"导入配置项失败: {key} - {e}")
                    results[key] = False
            
            return results
            
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return {}
    
    async def get_change_history(
        self,
        key: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取配置变更历史"""
        try:
            history = self.change_history
            
            if key:
                history = [change for change in history if change.config_key == key]
            
            # 按时间倒序排列
            history.sort(key=lambda x: x.changed_at, reverse=True)
            
            # 限制数量
            history = history[:limit]
            
            return [
                {
                    "id": change.id,
                    "config_key": change.config_key,
                    "old_value": change.old_value,
                    "new_value": change.new_value,
                    "changed_at": change.changed_at.isoformat(),
                    "changed_by": change.changed_by,
                    "reason": change.reason
                }
                for change in history
            ]
            
        except Exception as e:
            logger.error(f"获取配置变更历史失败: {e}")
            return []
    
    # 私有方法
    async def _load_configs(self):
        """从Redis加载配置"""
        try:
            if not self.redis_client:
                return
            
            configs = await self.redis_client.hgetall("configs")
            for key, value in configs.items():
                try:
                    config_data = json.loads(value)
                    config_item = self._deserialize_config(config_data)
                    self.config_cache[key] = config_item
                except Exception as e:
                    logger.error(f"加载配置项失败: {key} - {e}")
            
            logger.info(f"从Redis加载了 {len(configs)} 个配置项")
            
        except Exception as e:
            logger.error(f"从Redis加载配置失败: {e}")
    
    def _validate_value(self, config_item: ConfigItem, value: Any) -> bool:
        """验证配置值"""
        try:
            # 类型检查
            if config_item.type == ConfigType.STRING and not isinstance(value, str):
                return False
            elif config_item.type == ConfigType.INTEGER and not isinstance(value, int):
                return False
            elif config_item.type == ConfigType.FLOAT and not isinstance(value, (int, float)):
                return False
            elif config_item.type == ConfigType.BOOLEAN and not isinstance(value, bool):
                return False
            elif config_item.type == ConfigType.LIST and not isinstance(value, list):
                return False
            
            # 选项检查
            if config_item.options and value not in config_item.options:
                return False
            
            # 验证规则检查
            if config_item.validation_rule:
                return self._validate_rule(value, config_item.validation_rule)
            
            return True
            
        except Exception as e:
            logger.error(f"验证配置值失败: {e}")
            return False
    
    def _validate_rule(self, value: Any, rule: str) -> bool:
        """验证规则"""
        try:
            rules = rule.split(',')
            for rule_item in rules:
                rule_item = rule_item.strip()
                
                if rule_item.startswith('min:'):
                    min_val = float(rule_item[4:])
                    if value < min_val:
                        return False
                elif rule_item.startswith('max:'):
                    max_val = float(rule_item[4:])
                    if value > max_val:
                        return False
                elif rule_item.startswith('regex:'):
                    import re
                    pattern = rule_item[6:]
                    if not re.match(pattern, str(value)):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证规则失败: {e}")
            return False
    
    def _serialize_config(self, config_item: ConfigItem) -> Dict[str, Any]:
        """序列化配置项"""
        return {
            "key": config_item.key,
            "value": config_item.value,
            "type": config_item.type.value,
            "category": config_item.category.value,
            "description": config_item.description,
            "default_value": config_item.default_value,
            "required": config_item.required,
            "readonly": config_item.readonly,
            "sensitive": config_item.sensitive,
            "validation_rule": config_item.validation_rule,
            "options": config_item.options,
            "updated_at": config_item.updated_at.isoformat(),
            "updated_by": config_item.updated_by
        }
    
    def _deserialize_config(self, data: Dict[str, Any]) -> ConfigItem:
        """反序列化配置项"""
        return ConfigItem(
            key=data["key"],
            value=data["value"],
            type=ConfigType(data["type"]),
            category=ConfigCategory(data["category"]),
            description=data["description"],
            default_value=data["default_value"],
            required=data["required"],
            readonly=data["readonly"],
            sensitive=data["sensitive"],
            validation_rule=data["validation_rule"],
            options=data["options"],
            updated_at=datetime.fromisoformat(data["updated_at"]),
            updated_by=data["updated_by"]
        )


# 全局配置服务实例
config_service = ConfigService()
