"""
插件管理API

提供插件的安装、卸载、激活、停用等管理功能。
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_current_active_superuser
from app.models.user import User
# 暂时注释掉插件系统导入，避免循环依赖
# from app.plugins.manager import plugin_manager
# from app.plugins.base import PluginType, PluginStatus

router = APIRouter()


class PluginInfo(BaseModel):
    """插件信息"""
    name: str
    version: str
    description: str
    author: str
    type: str
    status: str
    dependencies: List[str]
    permissions: List[str]
    config: Dict[str, Any]
    tags: List[str]


class PluginConfig(BaseModel):
    """插件配置"""
    config: Dict[str, Any]


class PluginAction(BaseModel):
    """插件操作"""
    action: str
    parameters: Dict[str, Any] = {}


@router.get("/", response_model=List[PluginInfo])
async def get_plugins(
    plugin_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    获取插件列表
    
    Args:
        plugin_type: 插件类型过滤
        status: 状态过滤
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        List[PluginInfo]: 插件信息列表
    """
    # 暂时返回模拟数据，避免插件系统导入问题
    mock_plugins = [
        PluginInfo(
            name="email_sender",
            version="1.0.0",
            description="邮件发送插件",
            author="AI Agent Platform",
            type="tool",
            status="active",
            dependencies=[],
            permissions=["network.smtp"],
            config={"smtp_server": "smtp.gmail.com", "smtp_port": 587},
            tags=["email", "communication"]
        ),
        PluginInfo(
            name="slack_integration",
            version="1.2.0",
            description="Slack集成插件",
            author="AI Agent Platform",
            type="integration",
            status="inactive",
            dependencies=[],
            permissions=["network.http"],
            config={"webhook_url": "", "token": ""},
            tags=["slack", "integration"]
        )
    ]

    # 应用过滤器
    filtered_plugins = []
    for plugin in mock_plugins:
        if plugin_type and plugin.type != plugin_type:
            continue
        if status and plugin.status != status:
            continue
        filtered_plugins.append(plugin)

    return filtered_plugins


@router.get("/{plugin_name}", response_model=PluginInfo)
async def get_plugin(
    plugin_name: str,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    获取插件详细信息
    
    Args:
        plugin_name: 插件名称
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        PluginInfo: 插件信息
    """
    try:
        plugin_info = await plugin_manager.get_plugin_info(plugin_name)
        if not plugin_info:
            raise HTTPException(status_code=404, detail="插件不存在")
        
        return PluginInfo(**plugin_info)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取插件信息失败: {str(e)}")


@router.post("/{plugin_name}/activate")
async def activate_plugin(
    plugin_name: str,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    激活插件
    
    Args:
        plugin_name: 插件名称
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        Dict: 操作结果
    """
    # 暂时返回成功消息
    return {"message": f"插件 {plugin_name} 激活成功"}


@router.post("/{plugin_name}/deactivate")
async def deactivate_plugin(
    plugin_name: str,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    停用插件
    
    Args:
        plugin_name: 插件名称
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        Dict: 操作结果
    """
    try:
        success = await plugin_manager.deactivate_plugin(plugin_name)
        if not success:
            raise HTTPException(status_code=400, detail="插件停用失败")
        
        return {"message": f"插件 {plugin_name} 停用成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停用插件失败: {str(e)}")


@router.put("/{plugin_name}/config")
async def update_plugin_config(
    plugin_name: str,
    config_data: PluginConfig,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    更新插件配置
    
    Args:
        plugin_name: 插件名称
        config_data: 配置数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        Dict: 操作结果
    """
    try:
        success = await plugin_manager.update_plugin_config(
            plugin_name, 
            config_data.config
        )
        if not success:
            raise HTTPException(status_code=400, detail="更新插件配置失败")
        
        return {"message": f"插件 {plugin_name} 配置更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新插件配置失败: {str(e)}")


@router.post("/{plugin_name}/reload")
async def reload_plugin(
    plugin_name: str,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    重新加载插件
    
    Args:
        plugin_name: 插件名称
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        Dict: 操作结果
    """
    try:
        success = await plugin_manager.reload_plugin(plugin_name)
        if not success:
            raise HTTPException(status_code=400, detail="重新加载插件失败")
        
        return {"message": f"插件 {plugin_name} 重新加载成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载插件失败: {str(e)}")


@router.post("/{plugin_name}/execute")
async def execute_plugin_action(
    plugin_name: str,
    action_data: PluginAction,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    执行插件操作
    
    Args:
        plugin_name: 插件名称
        action_data: 操作数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        Dict: 执行结果
    """
    try:
        plugin = plugin_manager.get_plugin(plugin_name)
        if not plugin:
            raise HTTPException(status_code=404, detail="插件不存在或未加载")
        
        if plugin.status != PluginStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="插件未激活")
        
        # 根据插件类型执行不同的操作
        if hasattr(plugin, 'execute'):
            # 工具插件
            result = await plugin.execute(action_data.action, action_data.parameters)
        elif hasattr(plugin, 'process'):
            # 智能体插件
            result = await plugin.process(action_data.parameters)
        else:
            raise HTTPException(status_code=400, detail="插件不支持此操作")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行插件操作失败: {str(e)}")


@router.post("/install")
async def install_plugin(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    安装插件
    
    Args:
        file: 插件文件
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        Dict: 安装结果
    """
    try:
        # 保存上传的文件
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 安装插件
            success = await plugin_manager.install_plugin(temp_file_path)
            if not success:
                raise HTTPException(status_code=400, detail="插件安装失败")
            
            return {"message": "插件安装成功"}
            
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"安装插件失败: {str(e)}")


@router.delete("/{plugin_name}")
async def uninstall_plugin(
    plugin_name: str,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    卸载插件
    
    Args:
        plugin_name: 插件名称
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        Dict: 卸载结果
    """
    try:
        success = await plugin_manager.uninstall_plugin(plugin_name)
        if not success:
            raise HTTPException(status_code=400, detail="插件卸载失败")
        
        return {"message": f"插件 {plugin_name} 卸载成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"卸载插件失败: {str(e)}")


@router.get("/types/available")
async def get_plugin_types(
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    获取可用的插件类型
    
    Args:
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        List[str]: 插件类型列表
    """
    return [plugin_type.value for plugin_type in PluginType]


@router.get("/status/available")
async def get_plugin_statuses(
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    获取可用的插件状态
    
    Args:
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        List[str]: 插件状态列表
    """
    return [status.value for status in PluginStatus]
