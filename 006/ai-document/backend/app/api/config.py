"""
配置管理API
提供配置查看和管理功能
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from app.config.factory import config_factory
from app.schemas.user import User
from app.api.deps import get_current_active_user

router = APIRouter()


@router.get("/summary")
def get_config_summary(
    current_user: User = Depends(get_current_active_user)
):
    """获取配置摘要"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    return config_factory.get_config_summary()


@router.get("/validation")
def validate_configs(
    current_user: User = Depends(get_current_active_user)
):
    """验证所有配置"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    return config_factory.validate_all_configs()


@router.get("/environment")
def get_environment_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取环境信息"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    return config_factory.get_environment_info()


@router.get("/features")
def get_feature_flags():
    """获取功能开关状态（公开接口）"""
    return {
        "autogen_enabled": config_factory.is_feature_enabled("autogen"),
        "metrics_enabled": config_factory.is_feature_enabled("metrics"),
        "rate_limit_enabled": config_factory.is_feature_enabled("rate_limit"),
        "cache_enabled": config_factory.is_feature_enabled("cache"),
    }


@router.get("/{config_type}")
def get_specific_config(
    config_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取特定类型的配置"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 安全检查：不允许获取敏感配置
    sensitive_configs = ["auth", "security"]
    if config_type in sensitive_configs:
        raise HTTPException(status_code=403, detail="无法访问敏感配置")
    
    config = config_factory.get_config(config_type)
    if not config:
        raise HTTPException(status_code=404, detail=f"配置类型 '{config_type}' 不存在")
    
    return config


@router.post("/reload")
def reload_configs(
    current_user: User = Depends(get_current_active_user)
):
    """重新加载配置"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        config_factory.reload_configs()
        return {"message": "配置重新加载成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载配置失败: {str(e)}")


@router.get("/export/{config_type}")
def export_config(
    config_type: str,
    format: str = "json",
    current_user: User = Depends(get_current_active_user)
):
    """导出配置"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 安全检查
    sensitive_configs = ["auth", "security"]
    if config_type in sensitive_configs:
        raise HTTPException(status_code=403, detail="无法导出敏感配置")
    
    try:
        exported_config = config_factory.export_config(config_type, format)
        return {
            "config_type": config_type,
            "format": format,
            "data": exported_config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出配置失败: {str(e)}")


@router.get("/health/database")
def check_database_health():
    """检查数据库连接健康状态"""
    try:
        from app.database.connection import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {"status": "healthy", "message": "数据库连接正常"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"数据库连接失败: {str(e)}"}


@router.get("/health/ai")
def check_ai_health():
    """检查AI服务健康状态"""
    try:
        from app.config.ai import AIConfig
        ai_config = AIConfig.get_openai_config()
        
        if not ai_config.get("api_key"):
            return {"status": "unhealthy", "message": "OpenAI API密钥未配置"}
        
        return {"status": "healthy", "message": "AI服务配置正常"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"AI服务检查失败: {str(e)}"}


@router.get("/health/autogen")
def check_autogen_health():
    """检查AutoGen服务健康状态"""
    try:
        from app.config.autogen import AutoGenConfig
        validation = AutoGenConfig.validate_config()
        
        if validation.get("api_key_valid") and validation.get("agents_configured"):
            return {"status": "healthy", "message": "AutoGen服务配置正常", "details": validation}
        else:
            return {"status": "unhealthy", "message": "AutoGen服务配置不完整", "details": validation}
    except Exception as e:
        return {"status": "unhealthy", "message": f"AutoGen服务检查失败: {str(e)}"}


@router.get("/health/all")
def check_all_health():
    """检查所有服务健康状态"""
    health_checks = {
        "database": check_database_health(),
        "ai": check_ai_health(),
        "autogen": check_autogen_health(),
    }
    
    overall_status = "healthy" if all(
        check["status"] == "healthy" for check in health_checks.values()
    ) else "unhealthy"
    
    return {
        "overall_status": overall_status,
        "services": health_checks,
        "timestamp": config_factory.get_environment_info()
    }
