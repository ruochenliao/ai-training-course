"""
AutoGen配置管理类
"""
from typing import Dict, Any, List
from .base import settings
from .autogen_config import (
    AGENT_CONFIGS,
    COLLABORATION_MODES,
    TASK_AGENT_MAPPING,
    COLLABORATIVE_TASK_MAPPING,
    MODEL_CONFIG,
    STREAMING_CONFIG
)


class AutoGenConfig:
    """AutoGen配置管理类"""
    
    @staticmethod
    def get_base_config() -> Dict[str, Any]:
        """获取AutoGen基础配置"""
        return {
            "enabled": settings.autogen_enabled,
            "cache_enabled": settings.autogen_cache_enabled,
            "cache_duration": settings.autogen_cache_duration,
            "max_rounds": settings.autogen_max_rounds,
            "timeout": settings.autogen_timeout,
            "model_config": MODEL_CONFIG,
            "streaming_config": STREAMING_CONFIG,
        }
    
    @staticmethod
    def get_agent_configs() -> Dict[str, Dict[str, Any]]:
        """获取智能体配置"""
        return AGENT_CONFIGS
    
    @staticmethod
    def get_collaboration_modes() -> Dict[str, Dict[str, Any]]:
        """获取协作模式配置"""
        return COLLABORATION_MODES
    
    @staticmethod
    def get_task_mappings() -> Dict[str, Dict[str, str]]:
        """获取任务映射配置"""
        return {
            "single_agent": TASK_AGENT_MAPPING,
            "collaborative": COLLABORATIVE_TASK_MAPPING,
        }
    
    @staticmethod
    def get_model_client_config() -> Dict[str, Any]:
        """获取模型客户端配置"""
        return {
            "model": MODEL_CONFIG["model"],
            "api_key": settings.openai_api_key,
            "base_url": settings.openai_base_url,
            "max_tokens": MODEL_CONFIG["max_tokens"],
            "temperature": MODEL_CONFIG["temperature"],
            "top_p": MODEL_CONFIG.get("top_p", 1.0),
            "frequency_penalty": MODEL_CONFIG.get("frequency_penalty", 0.0),
            "presence_penalty": MODEL_CONFIG.get("presence_penalty", 0.0),
        }
    
    @staticmethod
    def get_team_config() -> Dict[str, Any]:
        """获取团队配置"""
        return {
            "max_participants": 5,
            "default_workflow": "sequential",
            "enable_user_proxy": True,
            "enable_message_filtering": True,
            "conversation_history_limit": 50,
        }
    
    @staticmethod
    def get_performance_config() -> Dict[str, Any]:
        """获取性能配置"""
        return {
            "parallel_execution": True,
            "max_concurrent_agents": 3,
            "agent_timeout": 60,
            "team_timeout": settings.autogen_timeout,
            "memory_limit": "1GB",
        }
    
    @staticmethod
    def get_safety_config() -> Dict[str, Any]:
        """获取安全配置"""
        return {
            "content_filtering": True,
            "max_message_length": 10000,
            "rate_limiting": True,
            "audit_logging": True,
            "sandbox_mode": False,
        }
    
    @staticmethod
    def get_workflow_configs() -> Dict[str, Dict[str, Any]]:
        """获取工作流配置"""
        return {
            "sequential": {
                "description": "顺序执行工作流",
                "max_rounds": 3,
                "allow_interruption": True,
            },
            "parallel": {
                "description": "并行执行工作流",
                "max_concurrent": 3,
                "synchronization_points": ["review", "final"],
            },
            "graph": {
                "description": "图形化工作流",
                "enable_conditions": True,
                "enable_loops": True,
                "max_depth": 5,
            },
        }
    
    @staticmethod
    def get_agent_specific_config(agent_type: str) -> Dict[str, Any]:
        """获取特定智能体的配置"""
        base_config = AGENT_CONFIGS.get(agent_type, {})
        
        # 合并全局配置
        config = {
            **base_config,
            "model_config": AutoGenConfig.get_model_client_config(),
            "performance": {
                "timeout": 60,
                "max_retries": 3,
                "memory_limit": "256MB",
            },
            "safety": {
                "content_filter": True,
                "rate_limit": True,
            },
        }
        
        return config
    
    @staticmethod
    def get_collaboration_config(mode: str) -> Dict[str, Any]:
        """获取协作模式的详细配置"""
        base_config = COLLABORATION_MODES.get(mode, COLLABORATION_MODES["writing"])
        
        config = {
            **base_config,
            "workflow_type": "graph",
            "enable_streaming": True,
            "enable_interruption": True,
            "quality_threshold": 0.8,
            "auto_review": True,
        }
        
        return config
    
    @staticmethod
    def get_monitoring_config() -> Dict[str, Any]:
        """获取监控配置"""
        return {
            "enable_metrics": settings.enable_metrics,
            "track_performance": True,
            "track_costs": True,
            "log_conversations": True,
            "export_format": "json",
        }
    
    @staticmethod
    def validate_config() -> Dict[str, bool]:
        """验证配置有效性"""
        validation_results = {
            "api_key_valid": bool(settings.openai_api_key),
            "agents_configured": len(AGENT_CONFIGS) > 0,
            "modes_configured": len(COLLABORATION_MODES) > 0,
            "mappings_configured": len(TASK_AGENT_MAPPING) > 0,
            "streaming_enabled": STREAMING_CONFIG.get("enable_typing_effect", False),
        }
        
        return validation_results
    
    @staticmethod
    def get_environment_specific_config() -> Dict[str, Any]:
        """获取环境特定配置"""
        if settings.is_development:
            return {
                "debug_mode": True,
                "verbose_logging": True,
                "enable_profiling": True,
                "mock_responses": False,
            }
        elif settings.is_production:
            return {
                "debug_mode": False,
                "verbose_logging": False,
                "enable_profiling": False,
                "mock_responses": False,
                "optimize_performance": True,
            }
        else:  # testing
            return {
                "debug_mode": True,
                "verbose_logging": True,
                "enable_profiling": False,
                "mock_responses": True,
            }
