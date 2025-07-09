"""
序列化工具函数
"""
from decimal import Decimal
from typing import Any, Dict, List, Union


def serialize_decimal(value: Any) -> Union[float, Any]:
    """
    将Decimal类型转换为float，其他类型保持不变
    """
    if isinstance(value, Decimal):
        return float(value)
    return value


def serialize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    递归序列化字典中的所有Decimal类型
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, dict):
            result[key] = serialize_dict(value)
        elif isinstance(value, list):
            result[key] = serialize_list(value)
        else:
            result[key] = value
    return result


def serialize_list(data: List[Any]) -> List[Any]:
    """
    递归序列化列表中的所有Decimal类型
    """
    result = []
    for item in data:
        if isinstance(item, Decimal):
            result.append(float(item))
        elif isinstance(item, dict):
            result.append(serialize_dict(item))
        elif isinstance(item, list):
            result.append(serialize_list(item))
        else:
            result.append(item)
    return result


def safe_serialize(data: Any) -> Any:
    """
    安全序列化任意数据类型，处理Decimal等不可JSON序列化的类型
    """
    if isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, dict):
        return serialize_dict(data)
    elif isinstance(data, list):
        return serialize_list(data)
    else:
        return data
