from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.schemas.template import (
    TemplateCategory, TemplateCategoryCreate, TemplateCategoryUpdate,
    TemplateType, TemplateTypeCreate, TemplateTypeUpdate,
    TemplateFile, TemplateFileCreate, TemplateFileUpdate,
    TemplateTreeNode, TemplateCategoryWithTypes,
    WritingScenarioConfig, WritingScenarioConfigCreate, WritingScenarioConfigUpdate
)
from app.schemas.user import User
from app.services.template_service import template_service
from app.services.template_init_service import template_init_service
from app.api.deps import get_current_active_user
import os
import uuid
from app.config.base import settings

router = APIRouter()


# 模板分类相关API
@router.get("/categories", response_model=List[TemplateCategory])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取模板分类列表"""
    return template_service.get_categories(db, skip=skip, limit=limit)


@router.get("/categories/{category_id}", response_model=TemplateCategory)
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """获取单个模板分类"""
    category = template_service.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="模板分类不存在")
    return category


@router.post("/categories", response_model=TemplateCategory)
def create_category(
    category: TemplateCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建模板分类"""
    return template_service.create_category(db, category)


@router.put("/categories/{category_id}", response_model=TemplateCategory)
def update_category(
    category_id: int,
    category: TemplateCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新模板分类"""
    updated_category = template_service.update_category(db, category_id, category)
    if not updated_category:
        raise HTTPException(status_code=404, detail="模板分类不存在")
    return updated_category


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除模板分类"""
    success = template_service.delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="模板分类不存在")
    return {"message": "删除成功"}


# 模板类型相关API
@router.get("/categories/{category_id}/types", response_model=List[TemplateType])
def get_types_by_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """获取指定分类下的模板类型"""
    return template_service.get_types_by_category(db, category_id)


@router.get("/types/{type_id}", response_model=TemplateType)
def get_type(
    type_id: int,
    db: Session = Depends(get_db)
):
    """获取单个模板类型"""
    template_type = template_service.get_type_by_id(db, type_id)
    if not template_type:
        raise HTTPException(status_code=404, detail="模板类型不存在")
    return template_type


@router.post("/types", response_model=TemplateType)
def create_type(
    template_type: TemplateTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建模板类型"""
    return template_service.create_type(db, template_type)


@router.put("/types/{type_id}", response_model=TemplateType)
def update_type(
    type_id: int,
    template_type: TemplateTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新模板类型"""
    updated_type = template_service.update_type(db, type_id, template_type)
    if not updated_type:
        raise HTTPException(status_code=404, detail="模板类型不存在")
    return updated_type


@router.delete("/types/{type_id}")
def delete_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除模板类型"""
    success = template_service.delete_type(db, type_id)
    if not success:
        raise HTTPException(status_code=404, detail="模板类型不存在")
    return {"message": "删除成功"}


# 模板文件相关API
@router.get("/types/{type_id}/files", response_model=List[TemplateFile])
def get_files_by_type(
    type_id: int,
    db: Session = Depends(get_db)
):
    """获取指定类型下的模板文件"""
    return template_service.get_files_by_type(db, type_id)


@router.get("/files/{file_id}", response_model=TemplateFile)
def get_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """获取单个模板文件"""
    template_file = template_service.get_file_by_id(db, file_id)
    if not template_file:
        raise HTTPException(status_code=404, detail="模板文件不存在")
    return template_file


@router.post("/files", response_model=TemplateFile)
def create_file(
    template_file: TemplateFileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建模板文件"""
    return template_service.create_file(db, template_file, current_user.id)


@router.put("/files/{file_id}", response_model=TemplateFile)
def update_file(
    file_id: int,
    template_file: TemplateFileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新模板文件"""
    updated_file = template_service.update_file(db, file_id, template_file)
    if not updated_file:
        raise HTTPException(status_code=404, detail="模板文件不存在")
    return updated_file


@router.delete("/files/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除模板文件"""
    success = template_service.delete_file(db, file_id)
    if not success:
        raise HTTPException(status_code=404, detail="模板文件不存在")
    return {"message": "删除成功"}


@router.post("/files/{file_id}/use")
def use_template_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """使用模板文件（增加使用次数）"""
    template_service.increment_usage_count(db, file_id)
    return {"message": "使用记录已更新"}


# 文件上传API
@router.post("/files/upload")
async def upload_template_file(
    file: UploadFile = File(...),
    type_id: int = None,
    name: str = None,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """上传模板文件"""
    if not type_id:
        raise HTTPException(status_code=400, detail="必须指定模板类型")
    
    # 验证模板类型是否存在
    template_type = template_service.get_type_by_id(db, type_id)
    if not template_type:
        raise HTTPException(status_code=404, detail="模板类型不存在")
    
    # 生成唯一文件名
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.upload_dir, "templates", unique_filename)
    
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # 读取文件内容（如果是文本文件）
    file_content = None
    if file.content_type and file.content_type.startswith('text/'):
        try:
            file_content = content.decode('utf-8')
        except:
            pass
    
    # 创建模板文件记录
    template_file = TemplateFileCreate(
        template_type_id=type_id,
        name=name or file.filename,
        description=description,
        file_path=file_path,
        file_size=len(content),
        file_type=file.content_type,
        content=file_content
    )
    
    return template_service.create_file(db, template_file, current_user.id)


# 综合API
@router.get("/tree")
def get_template_tree(db: Session = Depends(get_db)):
    """获取模板树结构"""
    from fastapi.responses import JSONResponse
    import json

    tree = template_service.get_template_tree(db)

    # 转换为字典格式，确保数据正确序列化
    def convert_to_dict(node):
        return {
            "id": node.id,
            "name": node.name,
            "type": node.type,
            "description": node.description,
            "is_active": node.is_active,
            "sort_order": node.sort_order,
            "children": [convert_to_dict(child) for child in node.children] if node.children else []
        }

    result = [convert_to_dict(node) for node in tree]

    # 确保UTF-8编码
    return JSONResponse(
        content=result,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )


@router.get("/search")
def search_templates(
    keyword: str,
    db: Session = Depends(get_db)
):
    """搜索模板"""
    return template_service.search_templates(db, keyword)


@router.get("/categories-with-types", response_model=List[TemplateCategoryWithTypes])
def get_categories_with_types(db: Session = Depends(get_db)):
    """获取包含类型的分类列表"""
    categories = template_service.get_categories(db)
    result = []

    for category in categories:
        types = template_service.get_types_by_category(db, category.id)
        category_dict = category.__dict__.copy()
        category_dict['template_types'] = types
        result.append(TemplateCategoryWithTypes(**category_dict))

    return result


# 数据初始化API
@router.post("/init")
def init_template_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """初始化模板数据"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有超级用户可以执行此操作")

    return template_init_service.init_template_data(db)


@router.post("/reset")
def reset_template_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """重置模板数据"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有超级用户可以执行此操作")

    return template_init_service.reset_template_data(db)


@router.get("/statistics")
def get_template_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取模板统计信息"""
    return template_init_service.get_template_statistics(db)


# 写作场景配置相关API
@router.get("/types/{type_id}/writing-scenario", response_model=WritingScenarioConfig)
def get_writing_scenario_config(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取模板类型的写作场景配置"""
    config = template_service.get_writing_scenario_config_by_type_id(db, type_id)
    if not config:
        raise HTTPException(status_code=404, detail="写作场景配置不存在")
    return config


@router.post("/types/{type_id}/writing-scenario", response_model=WritingScenarioConfig)
def create_writing_scenario_config(
    type_id: int,
    config: WritingScenarioConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建写作场景配置"""
    # 检查模板类型是否存在
    template_type = template_service.get_type_by_id(db, type_id)
    if not template_type:
        raise HTTPException(status_code=404, detail="模板类型不存在")

    # 检查是否已存在配置
    existing_config = template_service.get_writing_scenario_config_by_type_id(db, type_id)
    if existing_config:
        raise HTTPException(status_code=400, detail="该模板类型已存在写作场景配置")

    config.template_type_id = type_id
    return template_service.create_writing_scenario_config(db, config)


@router.put("/writing-scenario/{config_id}", response_model=WritingScenarioConfig)
def update_writing_scenario_config(
    config_id: int,
    config: WritingScenarioConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新写作场景配置"""
    updated_config = template_service.update_writing_scenario_config(db, config_id, config)
    if not updated_config:
        raise HTTPException(status_code=404, detail="写作场景配置不存在")
    return updated_config


@router.delete("/writing-scenario/{config_id}")
def delete_writing_scenario_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除写作场景配置"""
    success = template_service.delete_writing_scenario_config(db, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="写作场景配置不存在")
    return {"message": "写作场景配置删除成功"}
