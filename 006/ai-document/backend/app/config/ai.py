"""
AI配置
包含OpenAI和其他AI服务的配置
"""
from typing import Dict, Any, List, Optional
from .base import settings


class AIConfig:
    """AI配置类"""
    
    @staticmethod
    def get_openai_config() -> Dict[str, Any]:
        """获取OpenAI配置"""
        return {
            "api_key": settings.openai_api_key,
            "base_url": settings.openai_base_url,
            "model": settings.openai_model,
            "max_tokens": settings.openai_max_tokens,
            "temperature": settings.openai_temperature,
            "timeout": 30,
            "max_retries": 3,
        }
    
    @staticmethod
    def get_model_configs() -> Dict[str, Dict[str, Any]]:
        """获取不同模型的配置"""
        return {
            "gpt-3.5-turbo": {
                "max_tokens": 2000,
                "temperature": 0.7,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "cost_per_1k_tokens": 0.002,
            },
            "gpt-4": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "cost_per_1k_tokens": 0.03,
            },
            "gpt-4-turbo": {
                "max_tokens": 8000,
                "temperature": 0.7,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "cost_per_1k_tokens": 0.01,
            },
        }
    
    @staticmethod
    def get_streaming_config() -> Dict[str, Any]:
        """获取流式输出配置"""
        return {
            "enabled": True,
            "chunk_delay": 0.05,
            "word_delay": 0.03,
            "enable_typing_effect": True,
            "buffer_size": 1024,
        }
    
    @staticmethod
    def get_content_filter_config() -> Dict[str, Any]:
        """获取内容过滤配置"""
        return {
            "enabled": True,
            "max_length": 10000,
            "forbidden_words": [
                # 添加需要过滤的词汇
            ],
            "sensitive_topics": [
                "violence", "hate", "adult", "illegal"
            ],
        }
    
    @staticmethod
    def get_cache_config() -> Dict[str, Any]:
        """获取缓存配置"""
        return {
            "enabled": True,
            "ttl": 3600,  # 1小时
            "max_size": 1000,
            "key_prefix": "ai_cache:",
        }
    
    @staticmethod
    def get_prompt_templates() -> Dict[str, str]:
        """获取提示模板"""
        return {
            "system_default": "你是一个专业的AI助手，请根据用户需求提供准确、有用的回答。",
            "writer": "你是一位专业的写作助手，擅长创作各种类型的文章和内容。",
            "polisher": "你是一位专业的文本润色专家，擅长改进文本的流畅性和可读性。",
            "researcher": "你是一位专业的研究助手，擅长深入分析和研究各种主题。",
            "reviewer": "你是一位专业的内容评审专家，擅长评估内容质量和提供改进建议。",
        }
    
    @staticmethod
    def get_safety_config() -> Dict[str, Any]:
        """获取安全配置"""
        return {
            "content_moderation": True,
            "rate_limiting": True,
            "input_validation": True,
            "output_filtering": True,
            "audit_logging": True,
        }
    
    @staticmethod
    def get_performance_config() -> Dict[str, Any]:
        """获取性能配置"""
        return {
            "concurrent_requests": 10,
            "request_timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1,
            "circuit_breaker": {
                "failure_threshold": 5,
                "recovery_timeout": 60,
                "expected_exception": Exception,
            },
        }
    
    @staticmethod
    def get_monitoring_config() -> Dict[str, Any]:
        """获取监控配置"""
        return {
            "metrics_enabled": settings.enable_metrics,
            "log_requests": True,
            "log_responses": False,  # 出于隐私考虑默认关闭
            "track_usage": True,
            "track_costs": True,
        }
    
    @staticmethod
    def get_alternative_providers() -> Dict[str, Dict[str, Any]]:
        """获取备用AI服务提供商配置"""
        return {
            "anthropic": {
                "api_key": "",
                "base_url": "https://api.anthropic.com",
                "model": "claude-3-sonnet-20240229",
                "enabled": False,
            },
            "google": {
                "api_key": "",
                "base_url": "https://generativelanguage.googleapis.com",
                "model": "gemini-pro",
                "enabled": False,
            },
            "deepseek": {
                "api_key": "",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-chat",
                "enabled": False,
            },
        }
    
    @staticmethod
    def get_task_specific_configs() -> Dict[str, Dict[str, Any]]:
        """获取任务特定配置"""
        return {
            "writing": {
                "temperature": 0.8,
                "max_tokens": 2000,
                "top_p": 0.9,
            },
            "analysis": {
                "temperature": 0.3,
                "max_tokens": 1500,
                "top_p": 0.8,
            },
            "creative": {
                "temperature": 0.9,
                "max_tokens": 2500,
                "top_p": 0.95,
            },
            "technical": {
                "temperature": 0.2,
                "max_tokens": 1800,
                "top_p": 0.7,
            },
        }
