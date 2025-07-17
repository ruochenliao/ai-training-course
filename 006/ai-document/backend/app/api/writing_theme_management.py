"""
写作主题管理API
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.writing_theme_service import WritingThemeService
from app.schemas.writing_theme import (
    WritingTheme, WritingThemeCreate, WritingThemeUpdate, WritingThemeSimple,
    ThemeField, ThemeFieldCreate, ThemeFieldUpdate,
    PromptTemplate, PromptTemplateCreate, PromptTemplateUpdate,
    ThemeCategory, ThemeCategoryCreate, ThemeCategoryUpdate,
    TemplatePreviewRequest, TemplatePreviewResponse
)
from app.models.user import User
from app.api.auth import get_current_active_user

router = APIRouter()


def get_theme_service(db: Session = Depends(get_db)) -> WritingThemeService:
    """获取写作主题服务实例"""
    return WritingThemeService(db)


# ==================== 主题管理 ====================

@router.get("/themes", response_model=List[WritingTheme])
def get_themes(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    service: WritingThemeService = Depends(get_theme_service)
):
    """获取写作主题列表"""
    return service.get_themes(
        skip=skip,
        limit=limit,
        category=category,
        is_active=is_active,
        search=search
    )


@router.get("/themes/simple", response_model=List[WritingThemeSimple])
def get_themes_simple(
    category: Optional[str] = Query(None, description="分类筛选"),
    is_active: bool = Query(True, description="只获取启用的主题"),
    service: WritingThemeService = Depends(get_theme_service)
):
    """获取简化的主题列表（用于前端选择）"""
    themes = service.get_themes(category=category, is_active=is_active)
    
    # 转换为简化格式
    simple_themes = []
    for theme in themes:
        simple_theme = WritingThemeSimple(
            id=theme.id,
            name=theme.name,
            description=theme.description,
            category=theme.category,
            icon=theme.icon,
            theme_key=theme.theme_key,
            is_active=theme.is_active,
            sort_order=theme.sort_order,
            field_count=len(theme.fields),
            template_count=len(theme.prompt_templates),
            created_at=theme.created_at
        )
        simple_themes.append(simple_theme)
    
    return simple_themes


@router.get("/themes/{theme_id}", response_model=WritingTheme)
def get_theme(
    theme_id: int,
    service: WritingThemeService = Depends(get_theme_service)
):
    """获取单个写作主题详情"""
    theme = service.get_theme_by_id(theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail="主题不存在")
    return theme


@router.post("/themes", response_model=WritingTheme)
def create_theme(
    theme_data: WritingThemeCreate,
    service: WritingThemeService = Depends(get_theme_service),
    current_user: User = Depends(get_current_active_user)
):
    """创建写作主题"""
    return service.create_theme(theme_data)


@router.put("/themes/{theme_id}", response_model=WritingTheme)
def update_theme(
    theme_id: int,
    theme_data: WritingThemeUpdate,
    service: WritingThemeService = Depends(get_theme_service),
    current_user: User = Depends(get_current_active_user)
):
    """更新写作主题"""
    theme = service.update_theme(theme_id, theme_data)
    if not theme:
        raise HTTPException(status_code=404, detail="主题不存在")
    return theme


@router.delete("/themes/{theme_id}")
def delete_theme(
    theme_id: int,
    service: WritingThemeService = Depends(get_theme_service),
    current_user: User = Depends(get_current_active_user)
):
    """删除写作主题"""
    success = service.delete_theme(theme_id)
    if not success:
        raise HTTPException(status_code=404, detail="主题不存在")
    return {"message": "主题删除成功"}


# ==================== 字段管理 ====================

@router.get("/themes/{theme_id}/fields", response_model=List[ThemeField])
def get_theme_fields(
    theme_id: int,
    service: WritingThemeService = Depends(get_theme_service)
):
    """获取主题字段列表"""
    return service.get_theme_fields(theme_id)


@router.post("/themes/{theme_id}/fields", response_model=ThemeField)
def create_theme_field(
    theme_id: int,
    field_data: ThemeFieldCreate,
    service: WritingThemeService = Depends(get_theme_service),
    current_user: User = Depends(get_current_active_user)
):
    """创建主题字段"""
    return service.create_theme_field(theme_id, field_data)


@router.put("/fields/{field_id}", response_model=ThemeField)
def update_theme_field(
    field_id: int,
    field_data: ThemeFieldUpdate,
    service: WritingThemeService = Depends(get_theme_service),
    current_user: User = Depends(get_current_active_user)
):
    """更新主题字段"""
    field = service.update_theme_field(field_id, field_data)
    if not field:
        raise HTTPException(status_code=404, detail="字段不存在")
    return field


@router.delete("/fields/{field_id}")
def delete_theme_field(
    field_id: int,
    service: WritingThemeService = Depends(get_theme_service),
    current_user: User = Depends(get_current_active_user)
):
    """删除主题字段"""
    success = service.delete_theme_field(field_id)
    if not success:
        raise HTTPException(status_code=404, detail="字段不存在")
    return {"message": "字段删除成功"}


# ==================== 提示词模板管理 ====================

@router.get("/themes/{theme_id}/templates", response_model=List[PromptTemplate])
def get_theme_templates(
    theme_id: int,
    service: WritingThemeService = Depends(get_theme_service)
):
    """获取主题提示词模板列表"""
    return service.get_theme_templates(theme_id)


@router.get("/templates/{template_id}", response_model=PromptTemplate)
def get_template(
    template_id: int,
    service: WritingThemeService = Depends(get_theme_service)
):
    """获取单个提示词模板"""
    template = service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.post("/themes/{theme_id}/templates", response_model=PromptTemplate)
def create_template(
    theme_id: int,
    template_data: PromptTemplateCreate,
    service: WritingThemeService = Depends(get_theme_service),
    current_user: User = Depends(get_current_active_user)
):
    """创建提示词模板"""
    return service.create_template(theme_id, template_data)


@router.put("/templates/{template_id}", response_model=PromptTemplate)
def update_template(
    template_id: int,
    template_data: PromptTemplateUpdate,
    service: WritingThemeService = Depends(get_theme_service),
    current_user: User = Depends(get_current_active_user)
):
    """更新提示词模板"""
    template = service.update_template(template_id, template_data)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    service: WritingThemeService = Depends(get_theme_service),
    current_user: User = Depends(get_current_active_user)
):
    """删除提示词模板"""
    success = service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"message": "模板删除成功"}


# ==================== 分类管理 ====================

@router.get("/categories", response_model=List[ThemeCategory])
def get_categories(
    service: WritingThemeService = Depends(get_theme_service)
):
    """获取主题分类列表"""
    return service.get_categories()


@router.post("/categories", response_model=ThemeCategory)
def create_category(
    category_data: ThemeCategoryCreate,
    service: WritingThemeService = Depends(get_theme_service),
    current_user: User = Depends(get_current_active_user)
):
    """创建主题分类"""
    return service.create_category(category_data)


# ==================== 模板预览和测试 ====================

@router.post("/templates/{template_id}/preview", response_model=TemplatePreviewResponse)
def preview_template(
    template_id: int,
    preview_data: TemplatePreviewRequest,
    service: WritingThemeService = Depends(get_theme_service)
):
    """预览提示词模板"""
    try:
        rendered_prompt = service.render_prompt(template_id, preview_data.field_values)
        
        # 提取使用的变量
        template = service.get_template_by_id(template_id)
        variables_used = list(preview_data.field_values.keys())
        
        # 估算令牌数（简单估算：字符数/4）
        estimated_tokens = len(rendered_prompt) // 4
        
        return TemplatePreviewResponse(
            rendered_prompt=rendered_prompt,
            variables_used=variables_used,
            estimated_tokens=estimated_tokens
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 统计信息 ====================

@router.get("/statistics")
def get_theme_statistics(
    service: WritingThemeService = Depends(get_theme_service)
):
    """获取主题统计信息"""
    return service.get_theme_statistics()
