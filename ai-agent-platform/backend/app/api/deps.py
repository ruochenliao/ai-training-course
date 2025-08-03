"""
API依赖项
"""
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.db.session import get_db as get_database_session
# 暂时注释掉可能导致循环导入的模块
# from app import crud
from app.models.user import User

# HTTP Bearer token认证
security_scheme = HTTPBearer()


def get_db() -> Generator:
    """
    获取数据库会话

    Yields:
        数据库会话对象
    """
    yield from get_database_session()


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> User:
    """
    获取当前用户
    
    Args:
        db: 数据库会话
        credentials: 认证凭据
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解析JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[security.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # 暂时返回一个模拟用户，避免循环导入
    # 实际应用中应该从数据库查询用户
    user = User(
        id=1,
        email="admin@example.com",
        username=username,
        full_name="Administrator",
        is_active=True,
        is_superuser=True
    )
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前激活用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        当前激活用户对象
        
    Raises:
        HTTPException: 用户未激活时抛出异常
    """
    # 暂时简化用户激活检查
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前超级用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        当前超级用户对象
        
    Raises:
        HTTPException: 用户不是超级用户时抛出异常
    """
    # 暂时简化超级用户检查
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user doesn't have enough privileges"
        )
    return current_user


def get_optional_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Optional[User]:
    """
    获取可选的当前用户（用于可选认证的接口）
    
    Args:
        db: 数据库会话
        credentials: 认证凭据（可选）
        
    Returns:
        当前用户对象或None
    """
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[security.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    # 暂时返回模拟用户
    user = User(
        id=1,
        email="admin@example.com",
        username=username,
        full_name="Administrator",
        is_active=True,
        is_superuser=True
    )
    return user


def get_current_user_websocket(
    db: Session = Depends(get_db)
) -> User:
    """
    WebSocket专用的用户认证（简化版）
    在实际应用中，应该通过token验证用户身份

    Args:
        db: 数据库会话

    Returns:
        当前用户对象
    """
    # 这里简化处理，实际应该从WebSocket连接中获取token并验证
    # 暂时返回一个默认的超级用户用于测试
    user = User(
        id=1,
        email="admin@example.com",
        username="admin",
        full_name="Administrator",
        is_active=True,
        is_superuser=True
    )
    return user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前激活的超级用户

    Args:
        current_user: 当前用户

    Returns:
        当前激活的超级用户对象

    Raises:
        HTTPException: 用户未激活或不是超级用户时抛出异常
    """
    # 暂时简化检查
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user doesn't have enough privileges"
        )
    return current_user
