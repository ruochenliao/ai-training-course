"""
写作主题管理服务
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException

from app.models.writing_theme import WritingTheme, ThemeField, PromptTemplate, ThemeCategory
from app.schemas.writing_theme import (
    WritingThemeCreate, WritingThemeUpdate, WritingTheme as WritingThemeSchema,
    ThemeFieldCreate, ThemeFieldUpdate, PromptTemplateCreate, PromptTemplateUpdate,
    ThemeCategoryCreate, ThemeCategoryUpdate
)


class WritingThemeService:
    """写作主题服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 主题管理 ====================
    
    def get_themes(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[WritingTheme]:
        """获取主题列表"""
        query = self.db.query(WritingTheme)
        
        # 筛选条件
        if category:
            query = query.filter(WritingTheme.category == category)
        if is_active is not None:
            query = query.filter(WritingTheme.is_active == is_active)
        if search:
            query = query.filter(
                or_(
                    WritingTheme.name.contains(search),
                    WritingTheme.description.contains(search)
                )
            )
        
        return query.order_by(WritingTheme.sort_order, WritingTheme.created_at.desc()).offset(skip).limit(limit).all()

    def get_theme_by_id(self, theme_id: int) -> Optional[WritingTheme]:
        """根据ID获取主题"""
        return self.db.query(WritingTheme).filter(WritingTheme.id == theme_id).first()

    def get_theme_by_key(self, theme_key: str) -> Optional[WritingTheme]:
        """根据key获取主题"""
        return self.db.query(WritingTheme).filter(WritingTheme.theme_key == theme_key).first()

    def create_theme(self, theme_data: WritingThemeCreate) -> WritingTheme:
        """创建主题"""
        # 检查theme_key是否已存在
        if self.get_theme_by_key(theme_data.theme_key):
            raise HTTPException(status_code=400, detail="主题标识已存在")

        # 创建主题
        db_theme = WritingTheme(
            name=theme_data.name,
            description=theme_data.description,
            category=theme_data.category,
            icon=theme_data.icon,
            theme_key=theme_data.theme_key,
            is_active=theme_data.is_active,
            sort_order=theme_data.sort_order
        )
        
        self.db.add(db_theme)
        self.db.flush()  # 获取ID

        # 创建字段
        for field_data in theme_data.fields:
            db_field = ThemeField(
                theme_id=db_theme.id,
                **field_data.dict()
            )
            self.db.add(db_field)

        # 创建提示词模板
        for template_data in theme_data.prompt_templates:
            db_template = PromptTemplate(
                theme_id=db_theme.id,
                **template_data.dict()
            )
            self.db.add(db_template)

        self.db.commit()
        self.db.refresh(db_theme)
        return db_theme

    def update_theme(self, theme_id: int, theme_data: WritingThemeUpdate) -> Optional[WritingTheme]:
        """更新主题"""
        db_theme = self.get_theme_by_id(theme_id)
        if not db_theme:
            return None

        # 更新字段
        update_data = theme_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_theme, field, value)

        self.db.commit()
        self.db.refresh(db_theme)
        return db_theme

    def delete_theme(self, theme_id: int) -> bool:
        """删除主题"""
        db_theme = self.get_theme_by_id(theme_id)
        if not db_theme:
            return False

        self.db.delete(db_theme)
        self.db.commit()
        return True

    # ==================== 字段管理 ====================

    def get_theme_fields(self, theme_id: int) -> List[ThemeField]:
        """获取主题字段"""
        return self.db.query(ThemeField).filter(
            ThemeField.theme_id == theme_id
        ).order_by(ThemeField.sort_order).all()

    def create_theme_field(self, theme_id: int, field_data: ThemeFieldCreate) -> ThemeField:
        """创建主题字段"""
        # 检查主题是否存在
        if not self.get_theme_by_id(theme_id):
            raise HTTPException(status_code=404, detail="主题不存在")

        # 检查字段key是否在该主题下已存在
        existing_field = self.db.query(ThemeField).filter(
            and_(
                ThemeField.theme_id == theme_id,
                ThemeField.field_key == field_data.field_key
            )
        ).first()
        
        if existing_field:
            raise HTTPException(status_code=400, detail="字段键名在该主题下已存在")

        db_field = ThemeField(
            theme_id=theme_id,
            **field_data.dict()
        )
        
        self.db.add(db_field)
        self.db.commit()
        self.db.refresh(db_field)
        return db_field

    def update_theme_field(self, field_id: int, field_data: ThemeFieldUpdate) -> Optional[ThemeField]:
        """更新主题字段"""
        db_field = self.db.query(ThemeField).filter(ThemeField.id == field_id).first()
        if not db_field:
            return None

        update_data = field_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_field, field, value)

        self.db.commit()
        self.db.refresh(db_field)
        return db_field

    def delete_theme_field(self, field_id: int) -> bool:
        """删除主题字段"""
        db_field = self.db.query(ThemeField).filter(ThemeField.id == field_id).first()
        if not db_field:
            return False

        self.db.delete(db_field)
        self.db.commit()
        return True

    # ==================== 提示词模板管理 ====================

    def get_theme_templates(self, theme_id: int) -> List[PromptTemplate]:
        """获取主题提示词模板"""
        return self.db.query(PromptTemplate).filter(
            PromptTemplate.theme_id == theme_id
        ).order_by(PromptTemplate.created_at.desc()).all()

    def get_template_by_id(self, template_id: int) -> Optional[PromptTemplate]:
        """根据ID获取模板"""
        return self.db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()

    def create_template(self, theme_id: int, template_data: PromptTemplateCreate) -> PromptTemplate:
        """创建提示词模板"""
        # 检查主题是否存在
        if not self.get_theme_by_id(theme_id):
            raise HTTPException(status_code=404, detail="主题不存在")

        db_template = PromptTemplate(
            theme_id=theme_id,
            **template_data.dict()
        )
        
        self.db.add(db_template)
        self.db.commit()
        self.db.refresh(db_template)
        return db_template

    def update_template(self, template_id: int, template_data: PromptTemplateUpdate) -> Optional[PromptTemplate]:
        """更新提示词模板"""
        db_template = self.get_template_by_id(template_id)
        if not db_template:
            return None

        update_data = template_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_template, field, value)

        self.db.commit()
        self.db.refresh(db_template)
        return db_template

    def delete_template(self, template_id: int) -> bool:
        """删除提示词模板"""
        db_template = self.get_template_by_id(template_id)
        if not db_template:
            return False

        self.db.delete(db_template)
        self.db.commit()
        return True

    # ==================== 分类管理 ====================

    def get_categories(self) -> List[ThemeCategory]:
        """获取所有分类"""
        return self.db.query(ThemeCategory).filter(
            ThemeCategory.is_active == True
        ).order_by(ThemeCategory.sort_order).all()

    def create_category(self, category_data: ThemeCategoryCreate) -> ThemeCategory:
        """创建分类"""
        # 检查名称是否已存在
        existing = self.db.query(ThemeCategory).filter(ThemeCategory.name == category_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="分类名称已存在")

        db_category = ThemeCategory(**category_data.dict())
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category

    # ==================== 提示词渲染 ====================

    def render_prompt(self, template_id: int, field_values: Dict[str, Any]) -> str:
        """渲染提示词模板"""
        template = self.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")

        # 获取主题和字段信息
        theme = template.theme
        fields = {field.field_key: field for field in theme.fields}

        # 构建模板变量
        template_vars = {
            'theme_name': theme.name,
            'theme_description': theme.description,
            **field_values
        }

        # 渲染用户提示词
        try:
            rendered_prompt = template.user_prompt_template.format(**template_vars)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"模板变量缺失: {e}")

        # 如果有系统提示词，组合起来
        if template.system_prompt:
            full_prompt = f"{template.system_prompt}\n\n{rendered_prompt}"
        else:
            full_prompt = rendered_prompt

        return full_prompt

    def get_theme_statistics(self) -> Dict[str, Any]:
        """获取主题统计信息"""
        total_themes = self.db.query(WritingTheme).count()
        active_themes = self.db.query(WritingTheme).filter(WritingTheme.is_active == True).count()
        total_categories = self.db.query(ThemeCategory).count()
        
        # 按分类统计主题数量
        category_stats = self.db.query(
            WritingTheme.category,
            func.count(WritingTheme.id).label('count')
        ).group_by(WritingTheme.category).all()

        return {
            'total_themes': total_themes,
            'active_themes': active_themes,
            'total_categories': total_categories,
            'category_distribution': [
                {'category': stat.category, 'count': stat.count}
                for stat in category_stats
            ]
        }
