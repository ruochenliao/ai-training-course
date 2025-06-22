"""
系统管理API端点
"""

from datetime import datetime
from typing import Optional, Any

from app.core.security import get_current_user
from app.models.user import User
from app.services.backup_service import backup_service, BackupType, BackupConfig
from app.services.config_service import config_service, ConfigCategory
from app.services.i18n_service import i18n_service, SupportedLanguage
from app.services.notification_service import (
    notification_service,
    NotificationType,
    NotificationChannel,
    NotificationPriority
)
from app.services.plugin_service import plugin_service, PluginType, PluginStatus
from app.services.rate_limit_service import rate_limit_service, SecurityThreatLevel
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Body, Body
from pydantic import BaseModel, Field

router = APIRouter()


class SystemResponse(BaseModel):
    """系统响应基类"""
    success: bool = True
    data: Any = None
    message: str = ""


# 国际化相关接口
@router.get("/i18n/languages")
async def get_supported_languages():
    """获取支持的语言列表"""
    try:
        languages = i18n_service.get_supported_languages()
        return SystemResponse(data=languages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取语言列表失败: {str(e)}")


@router.get("/i18n/translations/{lang_code}")
async def get_translations(
    lang_code: str,
    namespace: str = Query("common", description="命名空间")
):
    """获取翻译"""
    try:
        if not i18n_service.is_language_supported(lang_code):
            raise HTTPException(status_code=400, detail="不支持的语言")
        
        # 这里应该返回完整的翻译数据
        # 目前返回示例数据
        translations = {
            "common.yes": i18n_service.get_translation("yes", lang_code, namespace),
            "common.no": i18n_service.get_translation("no", lang_code, namespace),
            "common.save": i18n_service.get_translation("save", lang_code, namespace),
            "common.cancel": i18n_service.get_translation("cancel", lang_code, namespace)
        }
        
        return SystemResponse(data=translations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取翻译失败: {str(e)}")


# 安全和限流相关接口
@router.get("/security/rate-limits")
async def get_rate_limit_stats(
    current_user: User = Depends(get_current_user)
):
    """获取限流统计"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        stats = await rate_limit_service.get_rate_limit_stats()
        return SystemResponse(data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取限流统计失败: {str(e)}")


@router.get("/security/events")
async def get_security_events(
    threat_level: Optional[SecurityThreatLevel] = Query(None, description="威胁级别"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    current_user: User = Depends(get_current_user)
):
    """获取安全事件"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        events = await rate_limit_service.get_security_events(threat_level, limit=limit)
        return SystemResponse(data=events)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取安全事件失败: {str(e)}")


@router.post("/security/block-ip")
async def block_ip_address(
    ip_address: str = Body(..., description="IP地址"),
    duration: int = Body(3600, description="封禁时长(秒)"),
    reason: str = Body("手动封禁", description="封禁原因"),
    current_user: User = Depends(get_current_user)
):
    """封禁IP地址"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        await rate_limit_service.block_ip(ip_address, duration, reason)
        return SystemResponse(message=f"IP {ip_address} 已被封禁")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"封禁IP失败: {str(e)}")


# 通知相关接口
@router.get("/notifications")
async def get_user_notifications(
    unread_only: bool = Query(False, description="仅未读"),
    limit: int = Query(50, ge=1, le=100, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user)
):
    """获取用户通知"""
    try:
        notifications = await notification_service.get_user_notifications(
            current_user.id, unread_only, limit, offset
        )
        
        return SystemResponse(data=[
            {
                "id": n.id,
                "type": n.type.value,
                "title": n.title,
                "content": n.content,
                "priority": n.priority.value,
                "read": n.read,
                "created_at": n.created_at.isoformat(),
                "data": n.data
            }
            for n in notifications
        ])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取通知失败: {str(e)}")


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """标记通知为已读"""
    try:
        success = await notification_service.mark_notification_read(notification_id, current_user.id)
        if success:
            return SystemResponse(message="通知已标记为已读")
        else:
            raise HTTPException(status_code=400, detail="标记失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标记通知失败: {str(e)}")


@router.get("/notifications/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user)
):
    """获取未读通知数量"""
    try:
        count = await notification_service.get_unread_count(current_user.id)
        return SystemResponse(data={"count": count})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取未读数量失败: {str(e)}")


# 备份相关接口
@router.get("/backup/list")
async def list_backups(
    current_user: User = Depends(get_current_user)
):
    """列出所有备份"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        backups = await backup_service.list_backups()
        return SystemResponse(data=backups)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出备份失败: {str(e)}")


@router.post("/backup/create")
async def create_backup(
    backup_type: BackupType = Body(BackupType.FULL, description="备份类型"),
    name: str = Body("manual_backup", description="备份名称"),
    current_user: User = Depends(get_current_user)
):
    """创建备份"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        config = BackupConfig(
            name=name,
            backup_type=backup_type,
            compression=True,
            encryption=False
        )
        
        job_id = await backup_service.create_backup(config, manual=True)
        return SystemResponse(data={"job_id": job_id}, message="备份任务已创建")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建备份失败: {str(e)}")


@router.get("/backup/status/{job_id}")
async def get_backup_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取备份状态"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        job = await backup_service.get_backup_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="备份任务不存在")
        
        return SystemResponse(data={
            "id": job.id,
            "status": job.status.value,
            "progress": job.progress,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "file_size": job.file_size,
            "error_message": job.error_message
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取备份状态失败: {str(e)}")


@router.post("/backup/restore")
async def restore_backup(
    backup_file: str = Body(..., description="备份文件名"),
    current_user: User = Depends(get_current_user)
):
    """恢复备份"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        job_id = await backup_service.restore_backup(backup_file)
        return SystemResponse(data={"job_id": job_id}, message="恢复任务已创建")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复备份失败: {str(e)}")


# 配置管理相关接口
@router.get("/config/categories/{category}")
async def get_configs_by_category(
    category: ConfigCategory,
    current_user: User = Depends(get_current_user)
):
    """按分类获取配置"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        configs = await config_service.get_configs_by_category(category)
        return SystemResponse(data=configs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.get("/config/all")
async def get_all_configs(
    include_sensitive: bool = Query(False, description="包含敏感配置"),
    current_user: User = Depends(get_current_user)
):
    """获取所有配置"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        configs = await config_service.get_all_configs(include_sensitive)
        return SystemResponse(data=configs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.put("/config/{key}")
async def update_config(
    key: str,
    value: Any = Body(..., description="配置值"),
    current_user: User = Depends(get_current_user)
):
    """更新配置"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        success = await config_service.set_config(key, value, current_user.username)
        if success:
            return SystemResponse(message=f"配置 {key} 已更新")
        else:
            raise HTTPException(status_code=400, detail="配置更新失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.post("/config/{key}/reset")
async def reset_config(
    key: str,
    current_user: User = Depends(get_current_user)
):
    """重置配置"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        success = await config_service.reset_config(key, current_user.username)
        if success:
            return SystemResponse(message=f"配置 {key} 已重置")
        else:
            raise HTTPException(status_code=400, detail="配置重置失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置配置失败: {str(e)}")


@router.post("/config/initialize")
async def initialize_system_configs(
    current_user: User = Depends(get_current_user)
):
    """初始化系统配置"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        from app.models.system import SystemConfig

        # 定义系统配置数据
        configs = [
            ("system.name", "企业级Agent+RAG知识库系统", "system", "系统名称", "应用程序名称"),
            ("system.version", "1.0.0", "system", "系统版本", "当前系统版本号"),
            ("system.description", "基于多智能体协作的企业级知识库系统", "system", "系统描述", "系统功能描述"),
            ("system.logo", "/logo.png", "system", "系统Logo", "系统Logo路径"),
            ("system.favicon", "/favicon.ico", "system", "系统图标", "系统图标路径"),

            # 功能开关配置
            ("feature.registration_enabled", "true", "feature", "用户注册", "是否允许用户注册"),
            ("feature.email_verification", "false", "feature", "邮箱验证", "是否需要邮箱验证"),
            ("feature.guest_access", "true", "feature", "访客访问", "是否允许访客访问"),
            ("feature.auto_backup", "true", "feature", "自动备份", "是否启用自动备份"),

            # 安全配置
            ("security.password_min_length", "8", "security", "密码最小长度", "用户密码最小长度要求"),
            ("security.password_require_special", "true", "security", "密码特殊字符", "密码是否需要特殊字符"),
            ("security.max_login_attempts", "5", "security", "最大登录尝试", "最大登录尝试次数"),
            ("security.lockout_duration", "30", "security", "锁定时长", "账户锁定时长（分钟）"),
            ("security.session_timeout", "24", "security", "会话超时", "会话超时时间（小时）"),

            # 文件上传配置
            ("upload.max_file_size", "104857600", "feature", "最大文件大小", "最大文件大小（字节）"),
            ("upload.allowed_extensions", ".pdf,.docx,.doc,.pptx,.ppt,.txt,.md,.html,.csv,.xlsx,.xls,.json", "feature", "允许的文件扩展名", "允许上传的文件类型"),
            ("upload.auto_process", "true", "feature", "自动处理", "是否自动处理上传的文档"),

            # AI模型配置
            ("ai.default_llm_model", "deepseek-chat", "ai_model", "默认LLM模型", "默认使用的大语言模型"),
            ("ai.default_embedding_model", "text-embedding-v1", "ai_model", "默认嵌入模型", "默认使用的嵌入模型"),
            ("ai.max_tokens", "4000", "ai_model", "最大Token数", "AI模型最大Token数"),
            ("ai.temperature", "0.7", "ai_model", "生成温度", "AI模型生成温度"),

            # 检索配置
            ("retrieval.default_top_k", "10", "feature", "默认检索数量", "默认检索结果数量"),
            ("retrieval.similarity_threshold", "0.7", "feature", "相似度阈值", "检索相似度阈值"),
            ("retrieval.enable_rerank", "true", "feature", "启用重排", "是否启用检索结果重排"),
            ("retrieval.chunk_size", "1000", "feature", "分块大小", "文档分块大小"),
            ("retrieval.chunk_overlap", "200", "feature", "分块重叠", "文档分块重叠大小"),

            # 通知配置
            ("notification.email_enabled", "false", "feature", "邮件通知", "是否启用邮件通知"),
            ("notification.sms_enabled", "false", "feature", "短信通知", "是否启用短信通知"),
            ("notification.webhook_enabled", "false", "feature", "Webhook通知", "是否启用Webhook通知"),

            # 监控配置
            ("monitoring.metrics_enabled", "true", "feature", "指标监控", "是否启用指标监控"),
            ("monitoring.log_level", "INFO", "feature", "日志级别", "系统日志级别"),
            ("monitoring.retention_days", "30", "feature", "日志保留天数", "日志文件保留天数"),
        ]

        created_count = 0
        for key, value, config_type, name, description in configs:
            # 检查配置是否已存在
            existing_config = await SystemConfig.get_or_none(key=key)
            if not existing_config:
                await SystemConfig.create(
                    key=key,
                    value=value,  # 直接使用字符串值，模型会处理
                    config_type=config_type,
                    name=name,
                    description=description,
                    is_public=key.startswith("system."),  # 系统信息设为公开
                    validation_rules="{}",  # 空的JSON对象
                    status="active"
                )
                created_count += 1

        return SystemResponse(
            data={"created_count": created_count, "total_configs": len(configs)},
            message=f"系统配置初始化完成，共创建 {created_count} 项配置"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化系统配置失败: {str(e)}")


# 插件管理相关接口
@router.get("/plugins")
async def list_plugins(
    status: Optional[PluginStatus] = Query(None, description="插件状态"),
    plugin_type: Optional[PluginType] = Query(None, description="插件类型"),
    current_user: User = Depends(get_current_user)
):
    """列出插件"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        plugins = await plugin_service.list_plugins(status, plugin_type)
        
        return SystemResponse(data=[
            {
                "id": p.manifest.id,
                "name": p.manifest.name,
                "version": p.manifest.version,
                "description": p.manifest.description,
                "author": p.manifest.author,
                "type": p.manifest.plugin_type.value,
                "status": p.status.value,
                "installed_at": p.installed_at.isoformat(),
                "enabled_at": p.enabled_at.isoformat() if p.enabled_at else None,
                "error_message": p.error_message
            }
            for p in plugins
        ])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出插件失败: {str(e)}")


@router.post("/plugins/install")
async def install_plugin(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """安装插件"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        # 保存上传的文件
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            success = await plugin_service.install_plugin(temp_file_path)
            if success:
                return SystemResponse(message="插件安装成功")
            else:
                raise HTTPException(status_code=400, detail="插件安装失败")
        finally:
            # 清理临时文件
            import os
            os.unlink(temp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"安装插件失败: {str(e)}")


@router.post("/plugins/{plugin_id}/enable")
async def enable_plugin(
    plugin_id: str,
    current_user: User = Depends(get_current_user)
):
    """启用插件"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        success = await plugin_service.enable_plugin(plugin_id)
        if success:
            return SystemResponse(message=f"插件 {plugin_id} 已启用")
        else:
            raise HTTPException(status_code=400, detail="插件启用失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启用插件失败: {str(e)}")


@router.post("/plugins/{plugin_id}/disable")
async def disable_plugin(
    plugin_id: str,
    current_user: User = Depends(get_current_user)
):
    """禁用插件"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        success = await plugin_service.disable_plugin(plugin_id)
        if success:
            return SystemResponse(message=f"插件 {plugin_id} 已禁用")
        else:
            raise HTTPException(status_code=400, detail="插件禁用失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"禁用插件失败: {str(e)}")


@router.delete("/plugins/{plugin_id}")
async def uninstall_plugin(
    plugin_id: str,
    current_user: User = Depends(get_current_user)
):
    """卸载插件"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        success = await plugin_service.uninstall_plugin(plugin_id)
        if success:
            return SystemResponse(message=f"插件 {plugin_id} 已卸载")
        else:
            raise HTTPException(status_code=400, detail="插件卸载失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"卸载插件失败: {str(e)}")


@router.get("/system/health")
async def get_system_health():
    """获取系统健康状态"""
    try:
        # 检查各个服务的健康状态
        health_status = {
            "database": "healthy",  # 应该实际检查数据库连接
            "redis": "healthy",     # 应该实际检查Redis连接
            "milvus": "healthy",    # 应该实际检查Milvus连接
            "neo4j": "healthy",     # 应该实际检查Neo4j连接
            "services": {
                "i18n": "healthy",
                "rate_limit": "healthy",
                "notification": "healthy",
                "backup": "healthy",
                "config": "healthy",
                "plugin": "healthy"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return SystemResponse(data=health_status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统健康状态失败: {str(e)}")


@router.get("/system/info")
async def get_system_info():
    """获取系统信息"""
    try:
        import platform
        import psutil
        
        system_info = {
            "version": "1.0.0",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free
            },
            "uptime": datetime.now().isoformat(),  # 应该记录实际启动时间
            "services_status": {
                "total_plugins": len(plugin_service.installed_plugins),
                "enabled_plugins": len(plugin_service.enabled_plugins),
                "cached_configs": len(config_service.config_cache)
            }
        }
        
        return SystemResponse(data=system_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")
