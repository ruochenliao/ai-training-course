"""
资源级别权限控制模块
"""

from typing import Type, Union, Optional, Callable, Any
from functools import wraps

from fastapi import Depends, HTTPException, status
from tortoise.models import Model

from app.core.security import get_current_user
from app.core.error_codes import ErrorCode
from app.core.exceptions import AuthorizationException
from app.models import User


class ResourcePermissionChecker:
    """资源权限检查器"""
    
    def __init__(
        self,
        model_class: Type[Model],
        resource_id_param: str = "resource_id",
        owner_field: str = "user_id",
        permission_code: Optional[str] = None,
        allow_superuser: bool = True,
        allow_owner: bool = True,
        department_field: Optional[str] = None,
    ):
        """
        初始化资源权限检查器
        
        Args:
            model_class: 资源模型类
            resource_id_param: 资源ID参数名
            owner_field: 所有者字段名
            permission_code: 需要的权限代码
            allow_superuser: 是否允许超级用户访问
            allow_owner: 是否允许所有者访问
            department_field: 部门字段名（用于部门级权限）
        """
        self.model_class = model_class
        self.resource_id_param = resource_id_param
        self.owner_field = owner_field
        self.permission_code = permission_code
        self.allow_superuser = allow_superuser
        self.allow_owner = allow_owner
        self.department_field = department_field
    
    async def __call__(self, **kwargs) -> User:
        """执行权限检查"""
        # 获取当前用户
        current_user = kwargs.get("current_user")
        if not current_user:
            raise AuthorizationException(error_code=ErrorCode.TOKEN_INVALID)
        
        # 超级用户检查
        if self.allow_superuser and current_user.is_superuser:
            return current_user
        
        # 获取资源ID
        resource_id = kwargs.get(self.resource_id_param)
        if not resource_id:
            raise AuthorizationException(
                error_code=ErrorCode.INVALID_OPERATION,
                details={"missing_param": self.resource_id_param}
            )
        
        # 获取资源
        try:
            resource = await self.model_class.get(id=resource_id)
        except Exception:
            raise AuthorizationException(error_code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 所有者检查
        if self.allow_owner and hasattr(resource, self.owner_field):
            owner_id = getattr(resource, self.owner_field)
            if owner_id == current_user.id:
                return current_user
        
        # 权限代码检查
        if self.permission_code:
            has_permission = await current_user.has_permission(self.permission_code)
            if has_permission:
                return current_user
        
        # 部门级权限检查
        if self.department_field and hasattr(resource, self.department_field):
            resource_dept_id = getattr(resource, self.department_field)
            user_dept_scope = await current_user.get_data_scope_departments()
            user_dept_ids = [dept.id for dept in user_dept_scope]
            
            if resource_dept_id in user_dept_ids:
                return current_user
        
        # 权限不足
        raise AuthorizationException(
            error_code=ErrorCode.RESOURCE_NOT_OWNED,
            details={
                "resource_type": self.model_class.__name__,
                "resource_id": resource_id,
                "required_permission": self.permission_code
            }
        )


def require_resource_access(
    model_class: Type[Model],
    resource_id_param: str = "resource_id",
    owner_field: str = "user_id",
    permission_code: Optional[str] = None,
    allow_superuser: bool = True,
    allow_owner: bool = True,
    department_field: Optional[str] = None,
):
    """
    资源访问权限装饰器
    
    使用示例:
    @require_resource_access(KnowledgeBase, "kb_id", "user_id", "knowledge_base:read")
    async def get_knowledge_base(kb_id: int, current_user: User = Depends(get_current_user)):
        pass
    """
    checker = ResourcePermissionChecker(
        model_class=model_class,
        resource_id_param=resource_id_param,
        owner_field=owner_field,
        permission_code=permission_code,
        allow_superuser=allow_superuser,
        allow_owner=allow_owner,
        department_field=department_field,
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 确保有current_user参数
            if "current_user" not in kwargs:
                # 从依赖注入中获取
                for arg in args:
                    if isinstance(arg, User):
                        kwargs["current_user"] = arg
                        break
            
            # 执行权限检查
            await checker(**kwargs)
            
            # 调用原函数
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


class BatchResourcePermissionChecker:
    """批量资源权限检查器"""
    
    def __init__(
        self,
        model_class: Type[Model],
        owner_field: str = "user_id",
        permission_code: Optional[str] = None,
        department_field: Optional[str] = None,
    ):
        self.model_class = model_class
        self.owner_field = owner_field
        self.permission_code = permission_code
        self.department_field = department_field
    
    async def filter_accessible_resources(
        self,
        user: User,
        resource_ids: list,
    ) -> list:
        """
        过滤用户可访问的资源ID列表
        
        Args:
            user: 当前用户
            resource_ids: 资源ID列表
            
        Returns:
            用户可访问的资源ID列表
        """
        if user.is_superuser:
            return resource_ids
        
        accessible_ids = []
        
        # 获取所有资源
        resources = await self.model_class.filter(id__in=resource_ids)
        
        # 获取用户权限和部门范围
        has_permission = False
        if self.permission_code:
            has_permission = await user.has_permission(self.permission_code)
        
        user_dept_ids = []
        if self.department_field:
            user_dept_scope = await user.get_data_scope_departments()
            user_dept_ids = [dept.id for dept in user_dept_scope]
        
        # 检查每个资源
        for resource in resources:
            # 所有者检查
            if hasattr(resource, self.owner_field):
                owner_id = getattr(resource, self.owner_field)
                if owner_id == user.id:
                    accessible_ids.append(resource.id)
                    continue
            
            # 权限检查
            if has_permission:
                accessible_ids.append(resource.id)
                continue
            
            # 部门权限检查
            if self.department_field and hasattr(resource, self.department_field):
                resource_dept_id = getattr(resource, self.department_field)
                if resource_dept_id in user_dept_ids:
                    accessible_ids.append(resource.id)
                    continue
        
        return accessible_ids
    
    async def get_accessible_query(self, user: User, base_query):
        """
        获取用户可访问资源的查询对象
        
        Args:
            user: 当前用户
            base_query: 基础查询对象
            
        Returns:
            过滤后的查询对象
        """
        if user.is_superuser:
            return base_query
        
        # 构建权限过滤条件
        filters = []
        
        # 所有者过滤
        if self.owner_field:
            filters.append({self.owner_field: user.id})
        
        # 部门权限过滤
        if self.department_field:
            user_dept_scope = await user.get_data_scope_departments()
            user_dept_ids = [dept.id for dept in user_dept_scope]
            if user_dept_ids:
                filters.append({f"{self.department_field}__in": user_dept_ids})
        
        # 如果有权限代码，检查是否有全局权限
        if self.permission_code:
            has_permission = await user.has_permission(self.permission_code)
            if has_permission:
                return base_query
        
        # 应用过滤条件
        if filters:
            from tortoise.expressions import Q
            filter_q = Q()
            for filter_dict in filters:
                filter_q |= Q(**filter_dict)
            return base_query.filter(filter_q)
        else:
            # 如果没有任何权限，返回空查询
            return base_query.filter(id__in=[])


# 常用资源权限检查器实例
def require_knowledge_base_access(kb_id_param: str = "kb_id", permission: str = "knowledge_base:read"):
    """知识库访问权限检查"""
    from app.models import KnowledgeBase
    return require_resource_access(
        model_class=KnowledgeBase,
        resource_id_param=kb_id_param,
        owner_field="user_id",
        permission_code=permission,
        department_field="department_id"
    )


def require_document_access(doc_id_param: str = "document_id", permission: str = "document:read"):
    """文档访问权限检查"""
    from app.models import Document
    return require_resource_access(
        model_class=Document,
        resource_id_param=doc_id_param,
        owner_field="user_id",
        permission_code=permission,
        department_field="department_id"
    )


def require_conversation_access(conv_id_param: str = "conversation_id", permission: str = "chat:access"):
    """对话访问权限检查"""
    from app.models import Conversation
    return require_resource_access(
        model_class=Conversation,
        resource_id_param=conv_id_param,
        owner_field="user_id",
        permission_code=permission
    )


# 批量权限检查器实例
def get_knowledge_base_filter():
    """获取知识库批量权限过滤器"""
    from app.models import KnowledgeBase
    return BatchResourcePermissionChecker(
        model_class=KnowledgeBase,
        owner_field="user_id",
        permission_code="knowledge_base:read",
        department_field="department_id"
    )


def get_document_filter():
    """获取文档批量权限过滤器"""
    from app.models import Document
    return BatchResourcePermissionChecker(
        model_class=Document,
        owner_field="user_id",
        permission_code="document:read",
        department_field="department_id"
    )
