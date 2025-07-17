"""
配置工厂类
统一管理和提供所有配置
"""
from typing import Dict, Any, Optional
from .base import settings
from .database import DatabaseConfig
from .auth import AuthConfig
from .ai import AIConfig
from .autogen import AutoGenConfig


class ConfigFactory:
    """配置工厂类"""
    
    _instance = None
    _configs = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_configs()
        return cls._instance
    
    def _initialize_configs(self):
        """初始化所有配置"""
        self._configs = {
            "app": self._get_app_config(),
            "database": DatabaseConfig.get_engine_config(),
            "auth": AuthConfig.get_jwt_config(),
            "ai": AIConfig.get_openai_config(),
            "autogen": AutoGenConfig.get_base_config(),
            "cors": AuthConfig.get_cors_config(),
            "security": AuthConfig.get_security_headers(),
            "monitoring": self._get_monitoring_config(),
            "logging": self._get_logging_config(),
        }
    
    def _get_app_config(self) -> Dict[str, Any]:
        """获取应用配置"""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": settings.app_description,
            "environment": settings.environment,
            "debug": settings.debug,
            "host": settings.host,
            "port": settings.port,
            "reload": settings.reload,
        }
    
    def _get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return {
            "metrics_enabled": settings.enable_metrics,
            "metrics_endpoint": settings.metrics_endpoint,
            "health_endpoint": settings.health_check_endpoint,
            "log_level": settings.log_level,
        }
    
    def _get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return {
            "level": settings.log_level,
            "file": settings.log_file,
            "rotation": settings.log_rotation,
            "retention": settings.log_retention,
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        }
    
    def get_config(self, config_type: str) -> Dict[str, Any]:
        """获取指定类型的配置"""
        return self._configs.get(config_type, {})
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有配置"""
        return self._configs.copy()
    
    def update_config(self, config_type: str, updates: Dict[str, Any]):
        """更新配置"""
        if config_type in self._configs:
            self._configs[config_type].update(updates)
    
    def reload_configs(self):
        """重新加载配置"""
        self._initialize_configs()
    
    # 便捷方法
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return DatabaseConfig.get_engine_config()
    
    def get_auth_config(self) -> Dict[str, Any]:
        """获取认证配置"""
        return AuthConfig.get_jwt_config()
    
    def get_ai_config(self) -> Dict[str, Any]:
        """获取AI配置"""
        return AIConfig.get_openai_config()
    
    def get_autogen_config(self) -> Dict[str, Any]:
        """获取AutoGen配置"""
        return AutoGenConfig.get_base_config()
    
    def get_cors_config(self) -> Dict[str, Any]:
        """获取CORS配置"""
        return AuthConfig.get_cors_config()
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return AuthConfig.get_security_headers()
    
    def is_feature_enabled(self, feature: str) -> bool:
        """检查功能是否启用"""
        feature_flags = {
            "autogen": settings.autogen_enabled,
            "metrics": settings.enable_metrics,
            "rate_limit": settings.rate_limit_enabled,
            "cache": settings.autogen_cache_enabled,
            "debug": settings.debug,
        }
        return feature_flags.get(feature, False)
    
    def get_environment_info(self) -> Dict[str, Any]:
        """获取环境信息"""
        return {
            "environment": settings.environment,
            "is_development": settings.is_development,
            "is_production": settings.is_production,
            "is_testing": settings.is_testing,
            "debug": settings.debug,
        }
    
    def validate_all_configs(self) -> Dict[str, Any]:
        """验证所有配置"""
        validation_results = {
            "database": self._validate_database_config(),
            "auth": self._validate_auth_config(),
            "ai": self._validate_ai_config(),
            "autogen": AutoGenConfig.validate_config(),
        }
        
        # 计算总体状态
        all_valid = all(
            isinstance(result, dict) and all(result.values()) if isinstance(result, dict) else result
            for result in validation_results.values()
        )
        
        validation_results["overall_status"] = "valid" if all_valid else "invalid"
        return validation_results
    
    def _validate_database_config(self) -> bool:
        """验证数据库配置"""
        try:
            db_config = self.get_database_config()
            return bool(db_config.get("url"))
        except Exception:
            return False
    
    def _validate_auth_config(self) -> bool:
        """验证认证配置"""
        try:
            auth_config = self.get_auth_config()
            return bool(auth_config.get("secret_key")) and len(auth_config.get("secret_key", "")) > 10
        except Exception:
            return False
    
    def _validate_ai_config(self) -> bool:
        """验证AI配置"""
        try:
            ai_config = self.get_ai_config()
            return bool(ai_config.get("api_key"))
        except Exception:
            return False
    
    def export_config(self, config_type: Optional[str] = None, format: str = "dict") -> Any:
        """导出配置"""
        if config_type:
            data = self.get_config(config_type)
        else:
            data = self.get_all_configs()
        
        if format == "json":
            import json
            return json.dumps(data, indent=2, default=str)
        elif format == "yaml":
            try:
                import yaml
                return yaml.dump(data, default_flow_style=False)
            except ImportError:
                raise ImportError("PyYAML is required for YAML export")
        else:
            return data
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "debug_mode": settings.debug,
            "database_type": "MySQL" if DatabaseConfig.is_mysql() else "Other",
            "ai_provider": "OpenAI",
            "autogen_enabled": settings.autogen_enabled,
            "features_enabled": {
                "metrics": settings.enable_metrics,
                "rate_limit": settings.rate_limit_enabled,
                "cache": settings.autogen_cache_enabled,
            },
            "config_status": self.validate_all_configs()["overall_status"],
        }


# 全局配置工厂实例
config_factory = ConfigFactory()
