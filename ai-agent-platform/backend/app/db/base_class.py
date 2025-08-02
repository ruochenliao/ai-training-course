"""
SQLAlchemy模型基类定义
"""
from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    """
    SQLAlchemy模型基类
    所有模型都应该继承这个基类
    """
    id: Any
    __name__: str

    # 自动生成表名（类名的小写形式）
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
