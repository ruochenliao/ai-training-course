"""
AI写作主题和生成API
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import uuid
import asyncio
import json

from app.database.connection import get_db
from app.services.ai_service import ai_service
from app.models.user import User
from app.api.auth import get_current_active_user
from app.schemas.ai import AIRequest

router = APIRouter()

# 导入写作主题服务
from app.services.writing_theme_service import WritingThemeService

# 存储生成会话的临时字典
generation_sessions = {}

# 存储流式输出的队列
import asyncio
from collections import defaultdict
stream_queues = defaultdict(asyncio.Queue)


def get_theme_service(db: Session = Depends(get_db)) -> WritingThemeService:
    """获取写作主题服务实例"""
    return WritingThemeService(db)


@router.get("/themes")
def get_ai_writing_themes(
    db: Session = Depends(get_db),
    service: WritingThemeService = Depends(get_theme_service)
):
    """获取所有AI写作主题"""
    themes = service.get_themes(is_active=True)

    # 转换为前端兼容的格式
    result = []
    for theme in themes:
        theme_data = {
            "id": theme.theme_key,  # 使用theme_key作为前端的id
            "name": theme.name,
            "description": theme.description,
            "category": theme.category,
            "icon": theme.icon,
            "fields": []
        }

        # 转换字段格式
        for field in theme.fields:
            if field.is_visible:
                field_data = {
                    "key": field.field_key,
                    "label": field.field_label,
                    "type": field.field_type,
                    "required": field.is_required,
                    "placeholder": field.placeholder or f"请输入{field.field_label}"
                }
                if field.options:
                    field_data["options"] = field.options
                theme_data["fields"].append(field_data)

        result.append(theme_data)

    return result


@router.get("/themes/{theme_key}")
def get_ai_writing_theme(
    theme_key: str,
    service: WritingThemeService = Depends(get_theme_service)
):
    """获取特定的AI写作主题"""
    theme = service.get_theme_by_key(theme_key)
    if not theme or not theme.is_active:
        raise HTTPException(status_code=404, detail="主题不存在")

    # 转换为前端兼容的格式
    theme_data = {
        "id": theme.theme_key,
        "name": theme.name,
        "description": theme.description,
        "category": theme.category,
        "icon": theme.icon,
        "fields": []
    }

    # 转换字段格式
    for field in theme.fields:
        if field.is_visible:
            field_data = {
                "key": field.field_key,
                "label": field.field_label,
                "type": field.field_type,
                "required": field.is_required,
                "placeholder": field.placeholder or f"请输入{field.field_label}"
            }
            if field.options:
                field_data["options"] = field.options
            theme_data["fields"].append(field_data)

    return theme_data


@router.get("/categories")
def get_ai_writing_categories(
    service: WritingThemeService = Depends(get_theme_service)
):
    """获取所有写作分类"""
    categories = service.get_categories()
    return {"categories": [cat.name for cat in categories]}


@router.post("/generate")
async def generate_ai_content(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """生成AI写作内容"""
    try:
        theme_id = request.get("theme_id")
        fields = request.get("fields", {})
        additional_context = request.get("additional_context", "")

        # 使用写作主题服务查找主题
        theme_service = WritingThemeService(db)
        theme = theme_service.get_theme_by_key(theme_id)

        if not theme or not theme.is_active:
            raise HTTPException(status_code=404, detail="主题不存在")

        # 转换为兼容格式
        theme_data = {
            "id": theme.theme_key,
            "name": theme.name,
            "description": theme.description,
            "fields": []
        }

        # 转换字段格式
        for field in theme.fields:
            if field.is_visible:
                field_data = {
                    "key": field.field_key,
                    "label": field.field_label,
                    "type": field.field_type,
                    "required": field.is_required
                }
                theme_data["fields"].append(field_data)

        # 构建提示词
        prompt = build_writing_prompt(theme_data, fields, additional_context)

        # 创建AI请求
        ai_request = AIRequest(
            ai_type="ai_writer",
            prompt=prompt,
            context=additional_context,
            metadata={
                "theme_id": theme_id,
                "theme_name": theme.name,
                "fields": fields
            }
        )

        # 创建AI会话
        session = ai_service.create_session(db=db, user_id=current_user.id, ai_request=ai_request)

        # 启动异步生成任务
        asyncio.create_task(generate_content_async(session.session_id, ai_request))

        return {
            "session_id": session.session_id,
            "status": "processing"
        }

    except Exception as e:
        print(f"生成AI内容时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{session_id}")
def get_generation_status(session_id: str, db: Session = Depends(get_db)):
    """获取生成状态"""
    try:
        # 从数据库获取会话状态
        from app.models.ai_session import AISession
        session = db.query(AISession).filter(AISession.session_id == session_id).first()

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        return {
            "session_id": session_id,
            "status": session.status,
            "content": session.response if session.status == "completed" else None,
            "error": session.response if session.status == "failed" else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream/{session_id}")
async def stream_generation_content(session_id: str, db: Session = Depends(get_db)):
    """流式获取生成内容"""
    async def generate():
        try:
            print(f"开始流式输出，会话ID: {session_id}")

            # 检查会话是否存在
            from app.models.ai_session import AISession
            session = db.query(AISession).filter(AISession.session_id == session_id).first()

            if not session:
                yield f"data: {json.dumps({'error': '会话不存在'})}\n\n"
                return

            # 如果已经完成，直接返回结果
            if session.status == "completed":
                content = session.response or ""
                print(f"会话已完成，直接返回内容，长度: {len(content)}")
                yield f"data: {json.dumps({'content': content, 'is_complete': True})}\n\n"
                return
            elif session.status == "failed":
                error_msg = session.response or "生成失败"
                print(f"会话已失败: {error_msg}")
                yield f"data: {json.dumps({'error': error_msg, 'is_complete': True})}\n\n"
                return

            # 获取流式队列
            queue = stream_queues[session_id]
            print(f"获取流式队列: {queue}")

            # 等待流式数据或超时
            max_wait_time = 300  # 最大等待5分钟
            start_time = asyncio.get_event_loop().time()

            while True:
                current_time = asyncio.get_event_loop().time()
                if current_time - start_time > max_wait_time:
                    print("流式输出超时")
                    yield f"data: {json.dumps({'error': '生成超时，请重试', 'is_complete': True})}\n\n"
                    break

                try:
                    # 等待队列中的数据，超时时间1秒
                    data = await asyncio.wait_for(queue.get(), timeout=1.0)
                    print(f"从队列获取数据: {data}")

                    if data.get('type') == 'content':
                        # 流式内容片段
                        yield f"data: {json.dumps({'content': data['content'], 'is_complete': False})}\n\n"
                    elif data.get('type') == 'complete':
                        # 生成完成
                        yield f"data: {json.dumps({'content': data['content'], 'is_complete': True})}\n\n"
                        print("流式输出完成")
                        break
                    elif data.get('type') == 'error':
                        # 生成失败
                        yield f"data: {json.dumps({'error': data['error'], 'is_complete': True})}\n\n"
                        print(f"流式输出失败: {data['error']}")
                        break
                    elif data.get('type') == 'progress':
                        # 进度更新
                        yield f"data: {json.dumps({'status': 'processing', 'message': data['message']})}\n\n"

                except asyncio.TimeoutError:
                    # 超时，检查会话状态
                    db.refresh(session)
                    if session.status == "completed":
                        content = session.response or ""
                        print(f"检查到会话完成，内容长度: {len(content)}")
                        yield f"data: {json.dumps({'content': content, 'is_complete': True})}\n\n"
                        break
                    elif session.status == "failed":
                        error_msg = session.response or "生成失败"
                        print(f"检查到会话失败: {error_msg}")
                        yield f"data: {json.dumps({'error': error_msg, 'is_complete': True})}\n\n"
                        break
                    else:
                        # 发送进度更新
                        yield f"data: {json.dumps({'status': 'processing', 'message': 'AI正在生成内容...'})}\n\n"

        except Exception as e:
            print(f"流式输出异常: {str(e)}")
            yield f"data: {json.dumps({'error': str(e), 'is_complete': True})}\n\n"
        finally:
            # 清理队列
            if session_id in stream_queues:
                del stream_queues[session_id]
                print(f"清理流式队列: {session_id}")

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


def build_writing_prompt(theme: Dict[str, Any], fields: Dict[str, Any], additional_context: str = "") -> str:
    """构建写作提示词"""
    prompt = f"请帮我写一份{theme['name']}文档。\n\n"

    # 添加字段信息
    for field_config in theme.get("fields", []):
        field_key = field_config["key"]
        field_label = field_config["label"]
        field_value = fields.get(field_key, "")

        if field_value:
            prompt += f"{field_label}：{field_value}\n"

    # 添加额外上下文
    if additional_context:
        prompt += f"\n补充说明：{additional_context}\n"

    prompt += "\n请根据以上信息，生成一份专业、规范、结构完整的文档。"
    prompt += "文档应该包含适当的格式、标题层次和专业的语言表达。"
    prompt += "请确保内容准确、逻辑清晰、语言流畅。"

    return prompt


def build_enhanced_prompt(ai_request: AIRequest, db: Session) -> str:
    """构建增强的AI提示词（使用数据库中的模板）"""
    theme_key = ai_request.metadata.get("theme_id", "unknown") if ai_request.metadata else "unknown"
    fields = ai_request.metadata.get("fields", {}) if ai_request.metadata else {}

    # 获取主题服务
    theme_service = WritingThemeService(db)

    # 根据theme_key获取主题
    theme = theme_service.get_theme_by_key(theme_key)

    if theme and theme.prompt_templates:
        # 使用数据库中的提示词模板
        # 优先使用主模板，如果没有则使用第一个可用模板
        main_template = None
        for template in theme.prompt_templates:
            if template.is_active:
                if template.template_type == "main":
                    main_template = template
                    break
                elif main_template is None:
                    main_template = template

        if main_template:
            try:
                # 使用模板服务渲染提示词
                return theme_service.render_prompt(main_template.id, fields)
            except Exception as e:
                print(f"模板渲染失败: {e}")
                # 如果模板渲染失败，使用备用方案
                pass

    # 备用方案：使用简化的提示词生成
    return build_fallback_prompt(theme_key, fields, ai_request)


def build_fallback_prompt(theme_key: str, fields: Dict[str, Any], ai_request: AIRequest) -> str:
    """构建备用提示词"""
    if theme_key == "commendation":
        title = fields.get("title", "表彰通报")
        recipient = fields.get("recipient", "先进个人")
        reason = fields.get("reason", "工作表现突出")
        achievement = fields.get("achievement", "取得优异成绩")

        return f"""请你作为一名专业的公文写作专家，帮我撰写一份正式的表彰通报。

**文档信息：**
- 标题：{title}
- 表彰对象：{recipient}
- 表彰原因：{reason}
- 主要成就：{achievement}

**写作要求：**
1. 使用正式的公文格式和语言
2. 结构清晰，包含表彰决定、表彰原因、主要成就、决定等部分
3. 语言庄重、准确、简洁
4. 体现表彰的正面意义和激励作用
5. 符合党政机关公文写作规范

请生成一份完整、专业的表彰通报文档。"""

    elif theme_key == "meeting_notice":
        title = fields.get("title", "会议通知")
        time = fields.get("time", "待定")
        location = fields.get("location", "待定")
        agenda = fields.get("agenda", "讨论重要事项")
        participants = fields.get("participants", "相关人员")

        return f"""请你作为一名专业的行政文秘，帮我撰写一份正式的会议通知。

**会议信息：**
- 会议主题：{title}
- 会议时间：{time}
- 会议地点：{location}
- 会议议程：{agenda}
- 参会人员：{participants}

**写作要求：**
1. 使用标准的会议通知格式
2. 信息完整、准确、清晰
3. 语言正式、简洁明了
4. 包含会议安排、议程、参会人员、注意事项等
5. 体现会议的重要性和必要性

请生成一份完整、规范的会议通知文档。"""

    else:
        # 通用提示词
        return f"""请你作为一名专业的文档写作专家，根据以下信息帮我撰写文档：

**用户需求：**
{ai_request.prompt}

**字段信息：**
{chr(10).join([f"- {k}: {v}" for k, v in fields.items() if v])}

**补充信息：**
{ai_request.context or '无'}

**写作要求：**
1. 内容准确、逻辑清晰
2. 结构完整、层次分明
3. 语言规范、表达流畅
4. 格式正确、排版美观
5. 符合相关写作规范

请生成一份高质量的专业文档。"""


def generate_backup_content(ai_request: AIRequest) -> str:
    """生成备用内容（当AI服务不可用时）"""
    theme_key = ai_request.metadata.get("theme_id", "unknown") if ai_request.metadata else "unknown"
    fields = ai_request.metadata.get("fields", {}) if ai_request.metadata else {}

    # 使用备用提示词生成简单内容
    return build_fallback_prompt(theme_key, fields, ai_request)


async def generate_content_async(session_id: str, ai_request: AIRequest):
    """异步生成内容并发送流式数据"""
    from app.database.connection import get_db_session

    try:
        print(f"开始异步生成内容，会话ID: {session_id}")
        # 获取数据库会话
        db = next(get_db_session())

        # 获取流式队列
        queue = stream_queues[session_id]

        # 发送开始信号
        await queue.put({
            'type': 'progress',
            'message': 'AI开始生成内容...'
        })

        # 使用真实的AI智能体生成内容
        try:
            # 发送进度更新
            await queue.put({
                'type': 'progress',
                'message': '正在启动AI智能体...'
            })

            # 构建专业的提示词（使用数据库模板）
            enhanced_prompt = build_enhanced_prompt(ai_request, db)
            print(f"构建的提示词: {enhanced_prompt[:200]}...")  # 只打印前200字符

            await queue.put({
                'type': 'progress',
                'message': '正在分析您的需求...'
            })

            # 使用AI服务生成内容
            full_content = ""
            async for response in ai_service.generate_single_agent_response(
                db=db,
                session_id=session_id,
                ai_type=ai_request.ai_type,
                prompt=enhanced_prompt,
                context=ai_request.context
            ):
                if response.content and not response.is_complete:
                    # 流式内容片段
                    full_content += response.content
                    print(f"收到AI内容片段: {response.content[:100]}...")

                    # 发送流式内容
                    await queue.put({
                        'type': 'content',
                        'content': full_content  # 发送累积的完整内容
                    })

                elif response.is_complete:
                    # 生成完成
                    if response.content:
                        full_content = response.content

                    print(f"AI生成完成，最终内容长度: {len(full_content)}")

                    # 发送完成信号
                    await queue.put({
                        'type': 'complete',
                        'content': full_content
                    })

                    ai_service.update_session_status(db, session_id, "completed", full_content)
                    break

                elif response.error:
                    # 生成失败
                    print(f"AI生成失败: {response.error}")

                    # 发送错误信号
                    await queue.put({
                        'type': 'error',
                        'error': response.error
                    })

                    ai_service.update_session_status(db, session_id, "failed", response.error)
                    break

            # 如果没有收到任何内容，使用备用方案
            if not full_content:
                print("警告：AI服务没有返回内容，使用备用生成")
                backup_content = generate_backup_content(ai_request)

                await queue.put({
                    'type': 'complete',
                    'content': backup_content
                })

                ai_service.update_session_status(db, session_id, "completed", backup_content)

        except Exception as e:
            print(f"AI生成过程中出现异常: {str(e)}")

            # 尝试备用生成方案
            try:
                backup_content = generate_backup_content(ai_request)

                await queue.put({
                    'type': 'complete',
                    'content': backup_content
                })

                ai_service.update_session_status(db, session_id, "completed", backup_content)

            except Exception as backup_error:
                print(f"备用生成也失败: {str(backup_error)}")

                # 发送错误信号
                await queue.put({
                    'type': 'error',
                    'error': f"AI生成失败: {str(e)}"
                })

                ai_service.update_session_status(db, session_id, "failed", str(e))

        db.close()
        print(f"异步生成任务完成，会话ID: {session_id}")

    except Exception as e:
        print(f"异步生成出错: {str(e)}")

        # 发送错误信号
        try:
            queue = stream_queues[session_id]
            await queue.put({
                'type': 'error',
                'error': str(e)
            })
        except:
            pass

        # 更新会话状态为失败
        try:
            db = next(get_db_session())
            ai_service.update_session_status(db, session_id, "failed", str(e))
            db.close()
        except:
            pass



