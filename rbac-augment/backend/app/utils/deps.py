"""
依赖注入模块
定义FastAPI依赖注入函数
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..core.security import verify_token
from ..crud.user import crud_user
from ..models.user import User
from ..schemas.common import PaginationParams


# HTTP Bearer Token认证
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """获取当前用户"""
    token = credentials.credentials
    user_id = verify_token(token, "access")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await crud_user.get(int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前激活用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要超级用户权限"
        )
    return current_user


def get_pagination_params(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=1000, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_field: Optional[str] = Query(None, description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向")
) -> PaginationParams:
    """获取分页参数"""
    return PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort_field=sort_field,
        sort_order=sort_order
    )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """获取可选的当前用户（用于可选认证的接口）"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_id = verify_token(token, "access")
        
        if user_id is None:
            return None
        
        user = await crud_user.get(int(user_id))
        if user is None or not user.is_active:
            return None
        
        return user
    except Exception:
        return None


class CurrentUserPermissions:
    """当前用户权限依赖"""
    
    def __init__(self, required_permissions: list[str]):
        self.required_permissions = required_permissions
    
    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """检查用户权限"""
        if current_user.is_superuser:
            return current_user
        
        user_permissions = await current_user.get_permissions()
        
        # 检查是否拥有所有必需权限
        missing_permissions = []
        for permission in self.required_permissions:
            if permission not in user_permissions:
                missing_permissions.append(permission)
        
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，缺少权限: {', '.join(missing_permissions)}"
            )
        
        return current_user


class CurrentUserAnyPermissions:
    """当前用户任意权限依赖"""
    
    def __init__(self, required_permissions: list[str]):
        self.required_permissions = required_permissions
    
    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """检查用户是否拥有任意一个权限"""
        if current_user.is_superuser:
            return current_user
        
        user_permissions = await current_user.get_permissions()
        
        # 检查是否拥有任意一个权限
        has_permission = any(
            permission in user_permissions 
            for permission in self.required_permissions
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下任意一个权限: {', '.join(self.required_permissions)}"
            )
        
        return current_user


class CurrentUserRole:
    """当前用户角色依赖"""
    
    def __init__(self, required_roles: list[str]):
        self.required_roles = required_roles
    
    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """检查用户角色"""
        if current_user.is_superuser:
            return current_user
        
        user_roles = await current_user.get_role_codes()
        
        # 检查是否拥有任意一个角色
        has_role = any(role in user_roles for role in self.required_roles)
        
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下任意一个角色: {', '.join(self.required_roles)}"
            )
        
        return current_user


# 常用权限依赖
require_user_read = CurrentUserPermissions(["user:read"])
require_user_write = CurrentUserPermissions(["user:create", "user:update"])
require_user_delete = CurrentUserPermissions(["user:delete"])

require_role_read = CurrentUserPermissions(["role:read"])
require_role_write = CurrentUserPermissions(["role:create", "role:update"])
require_role_delete = CurrentUserPermissions(["role:delete"])

require_permission_read = CurrentUserPermissions(["permission:read"])
require_permission_write = CurrentUserPermissions(["permission:create", "permission:update"])
require_permission_delete = CurrentUserPermissions(["permission:delete"])

require_menu_read = CurrentUserPermissions(["menu:read"])
require_menu_write = CurrentUserPermissions(["menu:create", "menu:update"])
require_menu_delete = CurrentUserPermissions(["menu:delete"])

require_system_read = CurrentUserPermissions(["system:read"])
require_system_write = CurrentUserPermissions(["system:update"])

# 常用角色依赖
require_admin_role = CurrentUserRole(["super_admin", "system_admin"])
require_manager_role = CurrentUserRole(["super_admin", "system_admin", "manager"])
