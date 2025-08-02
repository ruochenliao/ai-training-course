"""
安全相关功能：JWT认证、密码加密等
"""

from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer认证
security = HTTPBearer(auto_error=True)


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any]) -> str:
    """
    创建刷新令牌
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """
    验证令牌并返回用户ID
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None


def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    """
    return pwd_context.verify(plain_password, hashed_password)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    获取当前用户ID（依赖注入）
    """
    token = credentials.credentials
    user_id = verify_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


class RateLimiter:
    """
    简单的内存限流器
    """
    def __init__(self):
        self.requests = {}
    
    def is_allowed(
        self, 
        key: str, 
        limit: int = 60, 
        window: int = 60
    ) -> bool:
        """
        检查是否允许请求
        """
        now = datetime.utcnow()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # 清理过期请求
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if (now - req_time).seconds < window
        ]
        
        # 检查是否超过限制
        if len(self.requests[key]) >= limit:
            return False
        
        # 记录当前请求
        self.requests[key].append(now)
        return True


# 全局限流器实例
rate_limiter = RateLimiter()


def check_rate_limit(request: Request) -> bool:
    """
    检查请求限流
    """
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    key = f"{client_ip}:{user_agent}"

    return rate_limiter.is_allowed(
        key,
        limit=settings.RATE_LIMIT_REQUESTS,
        window=settings.RATE_LIMIT_WINDOW
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> "User":
    """
    获取当前用户（依赖注入）
    """
    from app.models.user import User

    try:
        # 验证token并获取用户ID
        user_id = verify_token(credentials.credentials)

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 从数据库获取用户信息
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已被禁用",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
