"""
智能体配置服务
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.agent_config import AgentConfig, AgentTool, AgentModel
from app.models.template import WritingFieldConfig
from app.schemas.agent_config import (
    AgentConfigCreate, AgentConfigUpdate,
    AgentToolCreate, AgentToolUpdate,
    AgentModelCreate, AgentModelUpdate,
    WritingFieldConfigUpdate
)


class AgentService:
    """智能体配置服务"""

    def get_agent_configs(self, db: Session, skip: int = 0, limit: int = 100) -> List[AgentConfig]:
        """获取智能体配置列表"""
        return db.query(AgentConfig).filter(AgentConfig.is_active == True).offset(skip).limit(limit).all()

    def get_agent_config(self, db: Session, agent_id: int) -> Optional[AgentConfig]:
        """获取单个智能体配置"""
        return db.query(AgentConfig).filter(
            and_(AgentConfig.id == agent_id, AgentConfig.is_active == True)
        ).first()

    def create_agent_config(self, db: Session, agent_data: AgentConfigCreate) -> AgentConfig:
        """创建智能体配置"""
        agent = AgentConfig(**agent_data.model_dump())
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    def update_agent_config(self, db: Session, agent_id: int, agent_data: AgentConfigUpdate) -> Optional[AgentConfig]:
        """更新智能体配置"""
        agent = self.get_agent_config(db, agent_id)
        if not agent:
            return None

        update_data = agent_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)

        db.commit()
        db.refresh(agent)
        return agent

    def delete_agent_config(self, db: Session, agent_id: int) -> bool:
        """删除智能体配置（软删除）"""
        agent = self.get_agent_config(db, agent_id)
        if not agent:
            return False

        agent.is_active = False
        db.commit()
        return True

    # 工具管理
    def get_agent_tools(self, db: Session, skip: int = 0, limit: int = 100) -> List[AgentTool]:
        """获取智能体工具列表"""
        return db.query(AgentTool).filter(AgentTool.is_active == True).offset(skip).limit(limit).all()

    def get_agent_tool(self, db: Session, tool_id: int) -> Optional[AgentTool]:
        """获取单个智能体工具"""
        return db.query(AgentTool).filter(
            and_(AgentTool.id == tool_id, AgentTool.is_active == True)
        ).first()

    def create_agent_tool(self, db: Session, tool_data: AgentToolCreate) -> AgentTool:
        """创建智能体工具"""
        tool = AgentTool(**tool_data.model_dump())
        db.add(tool)
        db.commit()
        db.refresh(tool)
        return tool

    def update_agent_tool(self, db: Session, tool_id: int, tool_data: AgentToolUpdate) -> Optional[AgentTool]:
        """更新智能体工具"""
        tool = self.get_agent_tool(db, tool_id)
        if not tool:
            return None

        update_data = tool_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tool, field, value)

        db.commit()
        db.refresh(tool)
        return tool

    def delete_agent_tool(self, db: Session, tool_id: int) -> bool:
        """删除智能体工具（软删除）"""
        tool = self.get_agent_tool(db, tool_id)
        if not tool:
            return False

        tool.is_active = False
        db.commit()
        return True

    # 模型管理
    def get_agent_models(self, db: Session, skip: int = 0, limit: int = 100) -> List[AgentModel]:
        """获取智能体模型列表"""
        return db.query(AgentModel).filter(AgentModel.is_active == True).offset(skip).limit(limit).all()

    def get_agent_model(self, db: Session, model_id: int) -> Optional[AgentModel]:
        """获取单个智能体模型"""
        return db.query(AgentModel).filter(
            and_(AgentModel.id == model_id, AgentModel.is_active == True)
        ).first()

    def create_agent_model(self, db: Session, model_data: AgentModelCreate) -> AgentModel:
        """创建智能体模型"""
        model = AgentModel(**model_data.model_dump())
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    def update_agent_model(self, db: Session, model_id: int, model_data: AgentModelUpdate) -> Optional[AgentModel]:
        """更新智能体模型"""
        model = self.get_agent_model(db, model_id)
        if not model:
            return None

        update_data = model_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(model, field, value)

        db.commit()
        db.refresh(model)
        return model

    def delete_agent_model(self, db: Session, model_id: int) -> bool:
        """删除智能体模型（软删除）"""
        model = self.get_agent_model(db, model_id)
        if not model:
            return False

        model.is_active = False
        db.commit()
        return True

    # 字段配置管理
    def get_field_configs_by_scenario(self, db: Session, scenario_config_id: int) -> List[WritingFieldConfig]:
        """获取写作场景的字段配置"""
        return db.query(WritingFieldConfig).filter(
            and_(
                WritingFieldConfig.scenario_config_id == scenario_config_id,
                WritingFieldConfig.is_active == True
            )
        ).order_by(WritingFieldConfig.sort_order).all()

    def update_field_config(self, db: Session, field_id: int, field_data: WritingFieldConfigUpdate) -> Optional[WritingFieldConfig]:
        """更新字段配置"""
        field = db.query(WritingFieldConfig).filter(WritingFieldConfig.id == field_id).first()
        if not field:
            return None

        update_data = field_data.model_dump(exclude_unset=True)
        for field_name, value in update_data.items():
            setattr(field, field_name, value)

        db.commit()
        db.refresh(field)
        return field

    def get_field_agent_config(self, db: Session, field_id: int) -> Optional[AgentConfig]:
        """获取字段关联的智能体配置"""
        field = db.query(WritingFieldConfig).filter(WritingFieldConfig.id == field_id).first()
        if not field or not field.agent_config_id:
            return None

        return self.get_agent_config(db, field.agent_config_id)

    def assign_agent_to_field(self, db: Session, field_id: int, agent_id: int) -> bool:
        """为字段分配智能体"""
        field = db.query(WritingFieldConfig).filter(WritingFieldConfig.id == field_id).first()
        agent = self.get_agent_config(db, agent_id)
        
        if not field or not agent:
            return False

        field.agent_config_id = agent_id
        db.commit()
        return True

    def remove_agent_from_field(self, db: Session, field_id: int) -> bool:
        """移除字段的智能体分配"""
        field = db.query(WritingFieldConfig).filter(WritingFieldConfig.id == field_id).first()
        if not field:
            return False

        field.agent_config_id = None
        db.commit()
        return True


# 创建服务实例
agent_service = AgentService()
