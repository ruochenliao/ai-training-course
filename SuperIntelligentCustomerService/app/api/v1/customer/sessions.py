"""
客户端会话管理接口
提供完整的会话增删改查功能
"""
from typing import Optional, List

from fastapi import APIRouter, Query, HTTPException, Body
from pydantic import BaseModel, Field

from app.controllers.session_service import session_service
from ....core.dependency import DependAuth
from ....models.admin import User, ChatMessage as ChatMessageModel
from ....schemas import Success, SuccessExtra
from ....schemas.session import CreateSessionDTO

router = APIRouter(tags=['会话管理'])


@router.post("/create", summary="创建新会话")
async def create_session(
        request: CreateSessionDTO,
        current_user: User = DependAuth
):
    """创建新的聊天会话"""
    try:
        # 使用当前用户ID
        user_id = str(current_user.id)
        session_data = session_service.create_session(user_id)

        # 添加会话标题和内容
        if request.session_title:
            session_data["session_title"] = request.session_title
        if request.session_content:
            session_data["session_content"] = request.session_content
        if request.remark:
            session_data["remark"] = request.remark

        # 保存更新后的会话数据
        session_service._save_session(session_data)

        data = {
            "session_id": session_data["session_id"],
            "user_id": session_data["user_id"],
            "created_at": session_data["created_at"],
            "last_active": session_data["last_active"],
            "messages": session_data["messages"],
            "session_title": session_data.get("session_title", "新对话"),
            "session_content": session_data.get("session_content", ""),
            "remark": session_data.get("remark", "")
        }
        return Success(data=data, msg="会话创建成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("/list", summary="获取会话列表")
async def get_session_list(
        page: int = Query(1, description="页码"),
        page_size: int = Query(20, description="每页数量"),
        session_title: Optional[str] = Query(None, description="会话标题搜索"),
        current_user: User = DependAuth
):
    """获取用户的会话列表"""
    try:
        user_id = str(current_user.id)
        sessions_data = session_service.get_user_sessions(user_id)

        # 过滤会话标题
        if session_title:
            sessions_data = [
                session for session in sessions_data
                if session_title.lower() in session.get("session_title", "").lower()
            ]

        # 手动实现分页
        total = len(sessions_data)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_sessions = sessions_data[start_index:end_index]

        # 格式化返回数据
        data = []
        for session in paginated_sessions:
            session_info = {
                "session_id": session["session_id"],
                "user_id": session["user_id"],
                "created_at": session["created_at"],
                "last_active": session["last_active"],
                "message_count": len(session.get("messages", [])),
                "session_title": session.get("session_title", "新对话"),
                "session_content": session.get("session_content", ""),
                "remark": session.get("remark", "")
            }
            data.append(session_info)

        return SuccessExtra(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            msg="获取会话列表成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.get("/{session_id}", summary="获取单个会话")
async def get_session(
        session_id: str,
        current_user: User = DependAuth
):
    """获取会话详情和历史消息"""
    try:
        session_data = session_service.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 检查权限
        if session_data.get("user_id") != str(current_user.id):
            raise HTTPException(status_code=403, detail="无权限访问此会话")

        data = {
            "session_id": session_data["session_id"],
            "user_id": session_data["user_id"],
            "created_at": session_data["created_at"],
            "last_active": session_data["last_active"],
            "messages": session_data["messages"],
            "session_title": session_data.get("session_title", "新对话"),
            "session_content": session_data.get("session_content", ""),
            "remark": session_data.get("remark", "")
        }
        return Success(data=data, msg="获取会话成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话失败: {str(e)}")


class UpdateSessionRequest(BaseModel):
    session_title: Optional[str] = Field(None, description="会话标题")
    session_content: Optional[str] = Field(None, description="会话内容")
    remark: Optional[str] = Field(None, description="备注")


@router.put("/{session_id}", summary="更新会话")
async def update_session(
        session_id: str,
        request: UpdateSessionRequest,
        current_user: User = DependAuth
):
    """更新会话信息"""
    try:
        # 获取会话数据
        session_data = session_service.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 检查权限
        if session_data.get("user_id") != str(current_user.id):
            raise HTTPException(status_code=403, detail="无权限修改此会话")

        # 准备更新数据
        updates = {}
        if request.session_title is not None:
            updates["session_title"] = request.session_title
        if request.session_content is not None:
            updates["session_content"] = request.session_content
        if request.remark is not None:
            updates["remark"] = request.remark

        # 更新会话
        success = session_service.update_session(session_id, updates)
        if not success:
            raise HTTPException(status_code=500, detail="更新会话失败")

        # 获取更新后的会话数据
        updated_session = session_service.get_session(session_id)

        data = {
            "session_id": updated_session["session_id"],
            "user_id": updated_session["user_id"],
            "created_at": updated_session["created_at"],
            "last_active": updated_session["last_active"],
            "session_title": updated_session.get("session_title", "新对话"),
            "session_content": updated_session.get("session_content", ""),
            "remark": updated_session.get("remark", "")
        }

        return Success(data=data, msg="会话更新成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新会话失败: {str(e)}")


@router.delete("/{session_id}", summary="删除会话")
async def delete_session(
        session_id: str,
        current_user: User = DependAuth
):
    """删除单个会话"""
    try:
        # 获取会话数据检查是否存在和权限
        session_data = session_service.get_session(session_id)

        # 检查会话是否存在
        if not session_data:
            # 会话不存在，但仍然尝试删除数据库中的消息（防止数据不一致）
            db_deleted = await ChatMessageModel.filter(
                session_id=session_id,
                user_id=current_user.id
            ).delete()

            if db_deleted > 0:
                return Success(msg=f"会话删除成功，清理了 {db_deleted} 条孤立消息")
            else:
                raise HTTPException(status_code=404, detail="会话不存在")

        # 检查权限
        if session_data.get("user_id") != str(current_user.id):
            raise HTTPException(status_code=403, detail="无权限删除此会话")

        # 从文件系统中删除
        file_deleted = session_service.delete_session(session_id)

        # 从数据库中删除相关消息
        db_deleted = await ChatMessageModel.filter(
            session_id=session_id,
            user_id=current_user.id
        ).delete()

        return Success(msg=f"会话删除成功，删除了 {db_deleted} 条消息")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.delete("/batch", summary="批量删除会话")
async def batch_delete_sessions(
        session_ids: List[str] = Body(..., description="会话ID列表"),
        current_user: User = DependAuth
):
    """批量删除会话"""
    try:
        deleted_count = 0
        failed_count = 0

        for session_id in session_ids:
            try:
                # 检查权限
                session_data = session_service.get_session(session_id)
                if session_data and session_data.get("user_id") != str(current_user.id):
                    failed_count += 1
                    continue

                # 删除文件和数据库记录
                file_deleted = session_service.delete_session(session_id)
                db_deleted = await ChatMessageModel.filter(
                    session_id=session_id,
                    user_id=current_user.id
                ).delete()

                if file_deleted or db_deleted > 0:
                    deleted_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1
                continue

        return Success(
            data={
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "total_count": len(session_ids)
            },
            msg=f"批量删除完成，成功删除 {deleted_count} 个会话，失败 {failed_count} 个"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量删除会话失败: {str(e)}")
