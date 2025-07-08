from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class GetSessionListVO(BaseModel):
    """模型列表返回对象"""
    model_config = ConfigDict(protected_namespaces=())

    id: Optional[int] = Field(None, description="模型ID")
    category: Optional[str] = Field(None, description="模型分类")
    model_name: Optional[str] = Field(None, description="模型名称")
    model_describe: Optional[str] = Field(None, description="模型描述")
    model_price: Optional[float] = Field(None, description="模型价格")
    model_type: Optional[str] = Field(None, description="模型类型")
    model_show: Optional[str] = Field(None, description="显示名称")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    api_host: Optional[str] = Field(None, description="API主机地址")
    api_key: Optional[str] = Field(None, description="API密钥")
    remark: Optional[str] = Field(None, description="备注")


class ModelCreate(BaseModel):
    """创建模型请求对象"""
    model_config = ConfigDict(protected_namespaces=())

    category: str = Field(..., description="模型分类")
    model_name: str = Field(..., description="模型名称")
    model_describe: Optional[str] = Field(None, description="模型描述")
    model_price: Optional[float] = Field(0, description="模型价格")
    model_type: str = Field(..., description="模型类型")
    model_show: str = Field(..., description="显示名称")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    api_host: Optional[str] = Field(None, description="API主机地址")
    api_key: Optional[str] = Field(None, description="API密钥")
    is_active: Optional[bool] = Field(True, description="是否启用")
    remark: Optional[str] = Field(None, description="备注")


class ModelUpdate(BaseModel):
    """更新模型请求对象"""
    model_config = ConfigDict(protected_namespaces=())

    id: int = Field(..., description="模型ID")
    category: Optional[str] = Field(None, description="模型分类")
    model_name: Optional[str] = Field(None, description="模型名称")
    model_describe: Optional[str] = Field(None, description="模型描述")
    model_price: Optional[float] = Field(None, description="模型价格")
    model_type: Optional[str] = Field(None, description="模型类型")
    model_show: Optional[str] = Field(None, description="显示名称")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    api_host: Optional[str] = Field(None, description="API主机地址")
    api_key: Optional[str] = Field(None, description="API密钥")
    is_active: Optional[bool] = Field(None, description="是否启用")
    remark: Optional[str] = Field(None, description="备注")
