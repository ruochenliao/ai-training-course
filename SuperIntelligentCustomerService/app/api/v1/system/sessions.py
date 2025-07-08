from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List, Optional

from app.controllers.session import session_controller
from app.core.dependency import DependAuth
from app.core.ctx import CTX_USER_ID
from app.models.admin import User
from app.schemas import Success, Fail, SuccessExtra
from app.schemas.session import (
    GetSessionListParams, 
    ChatSessionVo, 
    CreateSessionDTO, 
    SessionCreate,
    SessionUpdate
)

router = APIRouter()


@router.get("/list", summary="获取会话列表")
async def get_session_list(
    page_num: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    session_title: Optional[str] = Query(None, description="会话标题"),
    current_user: User = DependAuth
):
    """获取用户的会话列表"""
    try:
        user_id = current_user.id
        total, sessions = await session_controller.get_user_sessions(
            user_id=user_id,
            page=page_num,
            page_size=page_size,
            session_title=session_title
        )
        
        # 转换为前端需要的格式
        session_list = []
        for session in sessions:
            session_dict = await session.to_dict()
            session_dict["id"] = str(session_dict["id"])  # 转换为字符串
            session_list.append(session_dict)
        
        return SuccessExtra(
            data=session_list,
            total=total,
            page=page_num,
            page_size=page_size
        )
        
    except Exception as e:
        return Fail(msg=f"获取会话列表失败: {str(e)}")


@router.post("", summary="创建会话")
async def create_session(
    session_data: CreateSessionDTO,
    current_user: User = DependAuth
):
    """创建新会话"""
    try:
        user_id = current_user.id
        # 使用当前登录用户ID
        session_create = SessionCreate(
            session_title=session_data.session_title,
            session_content=session_data.session_content,
            user_id=user_id,
            remark=session_data.remark
        )
        
        session = await session_controller.create_user_session(session_create)
        session_dict = await session.to_dict()
        session_dict["id"] = str(session_dict["id"])  # 转换为字符串
        
        return Success(data=session_dict, msg="会话创建成功")
        
    except Exception as e:
        return Fail(msg=f"创建会话失败: {str(e)}")


@router.put("", summary="更新会话")
async def update_session(
    session_data: ChatSessionVo,
    current_user: User = DependAuth
):
    """更新会话信息"""
    try:
        user_id = current_user.id
        session_id = int(session_data.id) if session_data.id else None
        if not session_id:
            return Fail(msg="会话ID不能为空")

        session_update = SessionUpdate(
            id=session_id,
            session_title=session_data.session_title,
            session_content=session_data.session_content,
            remark=session_data.remark
        )

        updated_session = await session_controller.update_user_session(
            session_id=session_id,
            user_id=user_id,
            session_data=session_update
        )
        
        if not updated_session:
            return Fail(msg="会话不存在或无权限修改")
        
        session_dict = await updated_session.to_dict()
        session_dict["id"] = str(session_dict["id"])
        
        return Success(data=session_dict, msg="会话更新成功")
        
    except Exception as e:
        return Fail(msg=f"更新会话失败: {str(e)}")


@router.get("/{session_id}", summary="获取单个会话")
async def get_session(
    session_id: str,
    current_user: User = DependAuth
):
    """获取单个会话详情"""
    try:
        user_id = current_user.id
        session_id_int = int(session_id)
        session = await session_controller.get_user_session(session_id_int, user_id)
        
        if not session:
            return Fail(msg="会话不存在或无权限访问")
        
        session_dict = await session.to_dict()
        session_dict["id"] = str(session_dict["id"])
        
        return Success(data=session_dict)
        
    except ValueError:
        return Fail(msg="无效的会话ID")
    except Exception as e:
        return Fail(msg=f"获取会话失败: {str(e)}")


@router.delete("/{session_ids}", summary="删除会话")
async def delete_sessions(
    session_ids: str,
    current_user: User = DependAuth
):
    """删除会话（支持批量删除）"""
    try:
        user_id = current_user.id
        # 解析会话ID列表
        id_list = [int(id.strip()) for id in session_ids.split(",") if id.strip()]

        if not id_list:
            return Fail(msg="请提供要删除的会话ID")

        deleted_count = await session_controller.delete_user_sessions(id_list, user_id)
        
        return Success(msg=f"成功删除 {deleted_count} 个会话")
        
    except ValueError:
        return Fail(msg="无效的会话ID格式")
    except Exception as e:
        return Fail(msg=f"删除会话失败: {str(e)}")
