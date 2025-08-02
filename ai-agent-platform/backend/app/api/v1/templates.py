"""
智能体模板API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.core.security import get_current_user_id
from app.models.agent import Agent
from app.schemas.templates import (
    AgentTemplateResponse,
    CreateAgentFromTemplateRequest,
    TemplateCategory
)

router = APIRouter()

# 预定义的智能体模板
PREDEFINED_TEMPLATES = [
    {
        "id": "assistant",
        "name": "通用助手",
        "description": "一个友好、有帮助的AI助手，可以回答各种问题并提供建议",
        "category": "general",
        "avatar_url": "/static/templates/assistant.png",
        "prompt_template": """你是一个友好、有帮助的AI助手。请遵循以下原则：

1. 始终保持礼貌和专业
2. 提供准确、有用的信息
3. 如果不确定答案，请诚实说明
4. 根据用户的需求调整回答的详细程度
5. 鼓励用户提出后续问题

用户问题：{input}

请提供有帮助的回答：""",
        "model_name": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 2000,
        "tags": ["通用", "助手", "问答"]
    },
    {
        "id": "code_assistant",
        "name": "编程助手",
        "description": "专业的编程助手，帮助解决代码问题、代码审查和技术咨询",
        "category": "programming",
        "avatar_url": "/static/templates/code_assistant.png",
        "prompt_template": """你是一个专业的编程助手，具有丰富的软件开发经验。请遵循以下原则：

1. 提供清晰、可执行的代码示例
2. 解释代码的工作原理
3. 指出潜在的问题和改进建议
4. 推荐最佳实践
5. 支持多种编程语言

用户的编程问题：{input}

请提供专业的技术回答：""",
        "model_name": "gpt-4",
        "temperature": 0.3,
        "max_tokens": 3000,
        "tags": ["编程", "代码", "技术", "开发"]
    },
    {
        "id": "writer",
        "name": "写作助手",
        "description": "创意写作助手，帮助创作文章、故事、诗歌等各类文本内容",
        "category": "creative",
        "avatar_url": "/static/templates/writer.png",
        "prompt_template": """你是一个富有创意的写作助手，擅长各种文体的创作。请遵循以下原则：

1. 根据用户需求调整写作风格
2. 保持内容的原创性和创意性
3. 注意语言的流畅性和表达力
4. 提供多样化的表达方式
5. 鼓励创意思维

用户的写作需求：{input}

请提供创意的写作内容：""",
        "model_name": "gpt-3.5-turbo",
        "temperature": 0.9,
        "max_tokens": 2500,
        "tags": ["写作", "创意", "文案", "内容"]
    },
    {
        "id": "analyst",
        "name": "数据分析师",
        "description": "专业的数据分析助手，帮助分析数据、制作图表和提供商业洞察",
        "category": "business",
        "avatar_url": "/static/templates/analyst.png",
        "prompt_template": """你是一个专业的数据分析师，具有丰富的数据分析和商业洞察经验。请遵循以下原则：

1. 提供基于数据的客观分析
2. 使用适当的统计方法
3. 提供可视化建议
4. 解释分析结果的商业意义
5. 建议后续行动方案

用户的分析需求：{input}

请提供专业的数据分析建议：""",
        "model_name": "gpt-4",
        "temperature": 0.4,
        "max_tokens": 2500,
        "tags": ["数据分析", "商业", "统计", "洞察"]
    },
    {
        "id": "teacher",
        "name": "教学助手",
        "description": "耐心的教学助手，帮助学习各种知识，提供个性化的学习指导",
        "category": "education",
        "avatar_url": "/static/templates/teacher.png",
        "prompt_template": """你是一个耐心、专业的教学助手，擅长因材施教。请遵循以下原则：

1. 根据学习者水平调整解释深度
2. 使用生动的例子和类比
3. 鼓励主动思考和提问
4. 提供练习建议
5. 保持积极正面的态度

学习者的问题：{input}

请提供清晰易懂的教学回答：""",
        "model_name": "gpt-3.5-turbo",
        "temperature": 0.6,
        "max_tokens": 2000,
        "tags": ["教育", "学习", "教学", "知识"]
    },
    {
        "id": "translator",
        "name": "翻译助手",
        "description": "专业的多语言翻译助手，提供准确、自然的翻译服务",
        "category": "language",
        "avatar_url": "/static/templates/translator.png",
        "prompt_template": """你是一个专业的翻译助手，精通多种语言。请遵循以下原则：

1. 提供准确、自然的翻译
2. 保持原文的语调和风格
3. 解释文化背景差异
4. 提供多种翻译选项
5. 标注翻译的语言对

用户的翻译需求：{input}

请提供专业的翻译服务：""",
        "model_name": "gpt-3.5-turbo",
        "temperature": 0.3,
        "max_tokens": 2000,
        "tags": ["翻译", "语言", "多语言", "国际化"]
    }
]


@router.get("/", response_model=List[AgentTemplateResponse])
async def get_templates(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取智能体模板列表
    """
    templates = PREDEFINED_TEMPLATES.copy()
    
    # 按类别筛选
    if category:
        templates = [t for t in templates if t["category"] == category]
    
    # 按搜索关键词筛选
    if search:
        search_lower = search.lower()
        templates = [
            t for t in templates 
            if search_lower in t["name"].lower() 
            or search_lower in t["description"].lower()
            or any(search_lower in tag.lower() for tag in t["tags"])
        ]
    
    return templates


@router.get("/categories")
async def get_template_categories():
    """
    获取模板分类
    """
    categories = [
        {"id": "general", "name": "通用", "description": "通用助手模板"},
        {"id": "programming", "name": "编程", "description": "编程和技术相关模板"},
        {"id": "creative", "name": "创意", "description": "创意写作和内容创作模板"},
        {"id": "business", "name": "商业", "description": "商业分析和咨询模板"},
        {"id": "education", "name": "教育", "description": "教学和学习辅助模板"},
        {"id": "language", "name": "语言", "description": "翻译和语言学习模板"}
    ]
    return categories


@router.get("/{template_id}", response_model=AgentTemplateResponse)
async def get_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """
    获取指定模板详情
    """
    template = next((t for t in PREDEFINED_TEMPLATES if t["id"] == template_id), None)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    return template


@router.post("/{template_id}/create-agent")
async def create_agent_from_template(
    template_id: str,
    request: CreateAgentFromTemplateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    从模板创建智能体
    """
    template = next((t for t in PREDEFINED_TEMPLATES if t["id"] == template_id), None)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    # 创建智能体
    agent = Agent(
        name=request.name or template["name"],
        description=request.description or template["description"],
        avatar_url=template["avatar_url"],
        type="custom",
        prompt_template=template["prompt_template"],
        model_name=template["model_name"],
        temperature=str(template["temperature"]),
        max_tokens=str(template["max_tokens"]),
        owner_id=int(current_user_id),
        is_public=request.is_public or False,
        is_active=True
    )
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    return {
        "message": "智能体创建成功",
        "agent_id": agent.id,
        "agent_name": agent.name,
        "template_id": template_id
    }


@router.get("/popular/trending")
async def get_trending_templates(
    limit: int = 6,
    db: Session = Depends(get_db)
):
    """
    获取热门模板（基于使用次数）
    """
    # 这里可以根据实际使用统计来排序
    # 目前返回前几个模板作为热门模板
    trending = PREDEFINED_TEMPLATES[:limit]
    
    # 添加模拟的使用统计
    for i, template in enumerate(trending):
        template["usage_count"] = 100 - i * 10  # 模拟使用次数
        template["rating"] = 4.5 + (i * 0.1)   # 模拟评分
    
    return trending
