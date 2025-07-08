from fastapi import APIRouter, Query, Depends
from typing import Optional

from app.controllers.chat import chat_controller
from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas import Success, Fail, SuccessExtra
from app.schemas.chat import (
    GetChatListParams,
    ChatMessageVo,
    ChatMessageCreate
)
from app.utils.serializer import safe_serialize

router = APIRouter()


@router.get("/list", summary="获取聊天记录列表")
async def get_chat_list(
    sessionId: Optional[str] = Query(None, description="会话ID"),
    page_num: int = Query(1, description="页码"),
    page_size: int = Query(50, description="每页数量"),
    role: Optional[str] = Query(None, description="对话角色"),
    current_user: User = DependAuth
):
    """获取聊天记录列表"""
    user_id = current_user.id
    try:
        # 验证会话ID
        if not sessionId or sessionId.strip() == "":
            return Fail(msg="会话ID不能为空")

        # 检查特殊值
        if sessionId.strip() in ["not_login", "undefined", "null"]:
            return Fail(msg="无效的会话ID")

        try:
            session_id_int = int(sessionId.strip())
            if session_id_int <= 0:
                return Fail(msg="会话ID必须为正整数")
        except (ValueError, TypeError):
            return Fail(msg="会话ID格式错误")



        total, messages = await chat_controller.get_session_messages(
            session_id=session_id_int,
            user_id=user_id,
            page=page_num,
            page_size=page_size,
            role=role
        )
        
        # 转换为前端需要的格式
        message_list = []
        for message in messages:
            message_dict = await message.to_dict()
            # 转换字段名为驼峰命名格式
            formatted_message = {
                "id": message_dict["id"],
                "content": message_dict["content"],
                "role": message_dict["role"],
                "sessionId": message_dict["session_id"],
                "userId": message_dict["user_id"],
                "modelName": message_dict.get("model_name", ""),
                "totalTokens": message_dict.get("total_tokens", 0),
                "deductCost": safe_serialize(message_dict.get("deduct_cost", 0)),
                "remark": message_dict.get("remark"),
                "created_at": message_dict["created_at"],
                "updated_at": message_dict["updated_at"]
            }
            message_list.append(formatted_message)
        
        return SuccessExtra(
            data=message_list,
            total=total,
            page=page_num,
            page_size=page_size
        )
        
    except ValueError:
        return Fail(msg="无效的会话ID")
    except Exception as e:
        return Fail(msg=f"获取聊天记录失败: {str(e)}")


@router.post("", summary="新增聊天记录")
async def add_chat_message(
    message_data: ChatMessageVo,
    current_user: User = DependAuth
):
    """新增聊天记录"""
    try:
        user_id = current_user.id
        # 验证必要字段
        if not message_data.session_id:
            return Fail(msg="会话ID不能为空")
        if not message_data.content:
            return Fail(msg="消息内容不能为空")
        if not message_data.role:
            return Fail(msg="对话角色不能为空")

        # 创建消息记录
        message_create = ChatMessageCreate(
            session_id=int(message_data.session_id),
            user_id=user_id,
            role=message_data.role,
            content=message_data.content,
            model_name=message_data.model_name,
            total_tokens=message_data.total_tokens or 0,
            deduct_cost=message_data.deduct_cost or 0,
            remark=message_data.remark
        )
        
        message = await chat_controller.create_message(message_create)
        message_dict = await message.to_dict()
        
        return Success(data=message_dict, msg="聊天记录添加成功")
        
    except ValueError:
        return Fail(msg="无效的会话ID")
    except Exception as e:
        return Fail(msg=f"添加聊天记录失败: {str(e)}")


@router.get("/latest/{session_id}", summary="获取最新聊天记录")
async def get_latest_messages(
    session_id: str,
    limit: int = Query(10, description="获取消息数量"),
    current_user: User = DependAuth
):
    """获取会话的最新聊天记录"""
    try:
        user_id = current_user.id
        session_id_int = int(session_id)
        messages = await chat_controller.get_latest_messages(
            session_id=session_id_int,
            user_id=user_id,
            limit=limit
        )
        
        message_list = []
        for message in messages:
            message_dict = await message.to_dict()
            message_list.append(message_dict)
        
        return Success(data=message_list)
        
    except ValueError:
        return Fail(msg="无效的会话ID")
    except Exception as e:
        return Fail(msg=f"获取最新聊天记录失败: {str(e)}")


@router.delete("/{session_id}", summary="删除会话的所有聊天记录")
async def delete_session_messages(
    session_id: str,
    current_user: User = DependAuth
):
    """删除会话的所有聊天记录"""
    try:
        user_id = current_user.id
        session_id_int = int(session_id)
        deleted_count = await chat_controller.delete_session_messages(session_id_int, user_id)
        
        return Success(msg=f"成功删除 {deleted_count} 条聊天记录")
        
    except ValueError:
        return Fail(msg="无效的会话ID")
    except Exception as e:
        return Fail(msg=f"删除聊天记录失败: {str(e)}")


@router.get("/stats", summary="获取用户聊天统计")
async def get_user_chat_stats(
    current_user: User = DependAuth
):
    """获取用户聊天统计信息"""
    try:
        user_id = current_user.id
        stats = await chat_controller.get_user_message_stats(user_id)
        return Success(data=stats)
        
    except Exception as e:
        return Fail(msg=f"获取统计信息失败: {str(e)}")
