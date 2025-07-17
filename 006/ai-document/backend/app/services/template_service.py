from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.template import TemplateCategory, TemplateType, TemplateFile, WritingScenarioConfig
from app.schemas.template import (
    TemplateCategoryCreate, TemplateCategoryUpdate,
    TemplateTypeCreate, TemplateTypeUpdate,
    TemplateFileCreate, TemplateFileUpdate,
    TemplateTreeNode, WritingScenarioConfigCreate, WritingScenarioConfigUpdate
)


class TemplateService:
    """模板服务"""

    @staticmethod
    def get_categories(db: Session, skip: int = 0, limit: int = 100) -> List[TemplateCategory]:
        """获取模板分类列表"""
        return db.query(TemplateCategory).filter(
            TemplateCategory.is_active == True
        ).order_by(TemplateCategory.sort_order, TemplateCategory.id).offset(skip).limit(limit).all()

    @staticmethod
    def get_category_by_id(db: Session, category_id: int) -> Optional[TemplateCategory]:
        """根据ID获取模板分类"""
        return db.query(TemplateCategory).filter(TemplateCategory.id == category_id).first()

    @staticmethod
    def create_category(db: Session, category: TemplateCategoryCreate) -> TemplateCategory:
        """创建模板分类"""
        db_category = TemplateCategory(**category.dict())
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category

    @staticmethod
    def update_category(db: Session, category_id: int, category: TemplateCategoryUpdate) -> Optional[TemplateCategory]:
        """更新模板分类"""
        db_category = db.query(TemplateCategory).filter(TemplateCategory.id == category_id).first()
        if db_category:
            update_data = category.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_category, field, value)
            db.commit()
            db.refresh(db_category)
        return db_category

    @staticmethod
    def delete_category(db: Session, category_id: int) -> bool:
        """删除模板分类"""
        db_category = db.query(TemplateCategory).filter(TemplateCategory.id == category_id).first()
        if db_category:
            db.delete(db_category)
            db.commit()
            return True
        return False

    @staticmethod
    def get_types_by_category(db: Session, category_id: int) -> List[TemplateType]:
        """获取指定分类下的模板类型"""
        return db.query(TemplateType).filter(
            and_(TemplateType.category_id == category_id, TemplateType.is_active == True)
        ).order_by(TemplateType.sort_order, TemplateType.id).all()

    @staticmethod
    def get_type_by_id(db: Session, type_id: int) -> Optional[TemplateType]:
        """根据ID获取模板类型"""
        return db.query(TemplateType).filter(TemplateType.id == type_id).first()

    @staticmethod
    def create_type(db: Session, template_type: TemplateTypeCreate) -> TemplateType:
        """创建模板类型"""
        db_type = TemplateType(**template_type.dict())
        db.add(db_type)
        db.commit()
        db.refresh(db_type)
        return db_type

    @staticmethod
    def update_type(db: Session, type_id: int, template_type: TemplateTypeUpdate) -> Optional[TemplateType]:
        """更新模板类型"""
        db_type = db.query(TemplateType).filter(TemplateType.id == type_id).first()
        if db_type:
            update_data = template_type.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_type, field, value)
            db.commit()
            db.refresh(db_type)
        return db_type

    @staticmethod
    def delete_type(db: Session, type_id: int) -> bool:
        """删除模板类型"""
        db_type = db.query(TemplateType).filter(TemplateType.id == type_id).first()
        if db_type:
            db.delete(db_type)
            db.commit()
            return True
        return False

    @staticmethod
    def get_files_by_type(db: Session, type_id: int) -> List[TemplateFile]:
        """获取指定类型下的模板文件"""
        return db.query(TemplateFile).filter(
            and_(TemplateFile.template_type_id == type_id, TemplateFile.is_active == True)
        ).order_by(TemplateFile.is_default.desc(), TemplateFile.usage_count.desc(), TemplateFile.id).all()

    @staticmethod
    def get_file_by_id(db: Session, file_id: int) -> Optional[TemplateFile]:
        """根据ID获取模板文件"""
        return db.query(TemplateFile).filter(TemplateFile.id == file_id).first()

    @staticmethod
    def create_file(db: Session, template_file: TemplateFileCreate, user_id: int) -> TemplateFile:
        """创建模板文件"""
        file_data = template_file.dict()
        file_data['created_by'] = user_id
        db_file = TemplateFile(**file_data)
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return db_file

    @staticmethod
    def update_file(db: Session, file_id: int, template_file: TemplateFileUpdate) -> Optional[TemplateFile]:
        """更新模板文件"""
        db_file = db.query(TemplateFile).filter(TemplateFile.id == file_id).first()
        if db_file:
            update_data = template_file.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_file, field, value)
            db.commit()
            db.refresh(db_file)
        return db_file

    @staticmethod
    def delete_file(db: Session, file_id: int) -> bool:
        """删除模板文件"""
        db_file = db.query(TemplateFile).filter(TemplateFile.id == file_id).first()
        if db_file:
            db.delete(db_file)
            db.commit()
            return True
        return False

    @staticmethod
    def increment_usage_count(db: Session, file_id: int):
        """增加模板使用次数"""
        db_file = db.query(TemplateFile).filter(TemplateFile.id == file_id).first()
        if db_file:
            db_file.usage_count += 1
            db.commit()

    @staticmethod
    def get_template_tree(db: Session) -> List[TemplateTreeNode]:
        """获取模板树结构"""
        categories = db.query(TemplateCategory).filter(
            TemplateCategory.is_active == True
        ).order_by(TemplateCategory.sort_order, TemplateCategory.id).all()

        tree = []
        for category in categories:
            category_node = TemplateTreeNode(
                id=category.id,
                name=category.name,
                type="category",
                description=category.description,
                is_active=category.is_active,
                sort_order=category.sort_order,
                children=[]
            )

            # 获取该分类下的类型
            types = db.query(TemplateType).filter(
                and_(TemplateType.category_id == category.id, TemplateType.is_active == True)
            ).order_by(TemplateType.sort_order, TemplateType.id).all()

            for template_type in types:
                type_node = TemplateTreeNode(
                    id=template_type.id,
                    name=template_type.name or f"类型{template_type.id}",
                    type="type",
                    description=template_type.description or "",
                    is_active=template_type.is_active,
                    sort_order=template_type.sort_order,
                    children=[]
                )

                # 获取该类型下的文件
                files = db.query(TemplateFile).filter(
                    and_(TemplateFile.template_type_id == template_type.id, TemplateFile.is_active == True)
                ).order_by(TemplateFile.is_default.desc(), TemplateFile.usage_count.desc(), TemplateFile.id).all()

                for template_file in files:
                    file_node = TemplateTreeNode(
                        id=template_file.id,
                        name=template_file.name,
                        type="file",
                        description=template_file.description,
                        is_active=template_file.is_active,
                        sort_order=0,
                        children=[]
                    )
                    type_node.children.append(file_node)

                category_node.children.append(type_node)

            tree.append(category_node)

        return tree

    @staticmethod
    def search_templates(db: Session, keyword: str) -> Dict[str, Any]:
        """搜索模板"""
        results = {
            "categories": [],
            "types": [],
            "files": []
        }

        if keyword:
            # 搜索分类
            categories = db.query(TemplateCategory).filter(
                and_(
                    TemplateCategory.is_active == True,
                    TemplateCategory.name.contains(keyword)
                )
            ).all()
            results["categories"] = categories

            # 搜索类型
            types = db.query(TemplateType).filter(
                and_(
                    TemplateType.is_active == True,
                    TemplateType.name.contains(keyword)
                )
            ).all()
            results["types"] = types

            # 搜索文件
            files = db.query(TemplateFile).filter(
                and_(
                    TemplateFile.is_active == True,
                    TemplateFile.name.contains(keyword)
                )
            ).all()
            results["files"] = files

        return results

    # 写作场景配置相关方法
    @staticmethod
    def get_writing_scenario_config_by_type_id(db: Session, type_id: int) -> Optional[WritingScenarioConfig]:
        """根据模板类型ID获取写作场景配置"""
        return db.query(WritingScenarioConfig).filter(WritingScenarioConfig.template_type_id == type_id).first()

    @staticmethod
    def create_writing_scenario_config(db: Session, config: WritingScenarioConfigCreate) -> WritingScenarioConfig:
        """创建写作场景配置"""
        # 将field_configs转换为字典格式存储
        config_data = config.dict()
        if config_data.get('field_configs'):
            config_data['field_configs'] = [field.dict() if hasattr(field, 'dict') else field for field in config_data['field_configs']]

        db_config = WritingScenarioConfig(**config_data)
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return db_config

    @staticmethod
    def update_writing_scenario_config(db: Session, config_id: int, config: WritingScenarioConfigUpdate) -> Optional[WritingScenarioConfig]:
        """更新写作场景配置"""
        db_config = db.query(WritingScenarioConfig).filter(WritingScenarioConfig.id == config_id).first()
        if db_config:
            update_data = config.dict(exclude_unset=True)
            if update_data.get('field_configs'):
                update_data['field_configs'] = [field.dict() if hasattr(field, 'dict') else field for field in update_data['field_configs']]

            for field, value in update_data.items():
                setattr(db_config, field, value)
            db.commit()
            db.refresh(db_config)
        return db_config

    @staticmethod
    def delete_writing_scenario_config(db: Session, config_id: int) -> bool:
        """删除写作场景配置"""
        db_config = db.query(WritingScenarioConfig).filter(WritingScenarioConfig.id == config_id).first()
        if db_config:
            db.delete(db_config)
            db.commit()
            return True
        return False


template_service = TemplateService()
