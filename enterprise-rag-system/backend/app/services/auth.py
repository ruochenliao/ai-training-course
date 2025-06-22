"""
认证服务
"""

from datetime import datetime
from typing import Optional

from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.schemas.auth import UserRegister
from app.schemas.user import UserCreate


class AuthService:
    """认证服务类"""
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        验证用户身份
        """
        # 支持用户名或邮箱登录
        user = await User.get_or_none(username=username)
        if not user:
            user = await User.get_or_none(email=username)
        
        if not user:
            return None
        
        # 验证密码
        if not user.verify_password(password):
            # 记录失败登录
            await user.record_failed_login()
            await user.save()
            return None
        
        return user
    
    async def create_user(self, user_data: UserRegister) -> User:
        """
        创建用户
        """
        # 创建用户实例
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            phone=user_data.phone,
        )
        
        # 设置密码
        user.set_password(user_data.password)
        
        # 保存用户
        await user.save()
        
        return user
    
    async def create_user_from_schema(self, user_data: UserCreate) -> User:
        """
        从Schema创建用户
        """
        # 创建用户实例
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            phone=user_data.phone,
            bio=user_data.bio,
            language=user_data.language,
            timezone=user_data.timezone,
            theme=user_data.theme,
        )
        
        # 设置密码
        user.set_password(user_data.password)
        
        # 保存用户
        await user.save()
        
        return user
    
    async def verify_email(self, user_id: int) -> bool:
        """
        验证邮箱
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            return False
        
        user.is_email_verified = True
        await user.save()
        
        return True
    
    async def verify_phone(self, user_id: int) -> bool:
        """
        验证手机号
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            return False
        
        user.is_phone_verified = True
        await user.save()
        
        return True
    
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        修改密码
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            return False
        
        # 验证旧密码
        if not user.verify_password(old_password):
            return False
        
        # 设置新密码
        user.set_password(new_password)
        await user.save()
        
        return True
    
    async def reset_password(self, user_id: int, new_password: str) -> bool:
        """
        重置密码
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            return False
        
        # 设置新密码
        user.set_password(new_password)
        
        # 解锁账户
        user.unlock_account()
        
        await user.save()
        
        return True
    
    async def lock_user(self, user_id: int, duration_minutes: int = 30) -> bool:
        """
        锁定用户
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            return False
        
        user.lock_account(duration_minutes)
        await user.save()
        
        return True
    
    async def unlock_user(self, user_id: int) -> bool:
        """
        解锁用户
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            return False
        
        user.unlock_account()
        await user.save()
        
        return True
    
    async def activate_user(self, user_id: int) -> bool:
        """
        激活用户
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            return False
        
        user.status = "active"
        await user.save()
        
        return True
    
    async def deactivate_user(self, user_id: int) -> bool:
        """
        停用用户
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            return False
        
        user.status = "inactive"
        await user.save()
        
        return True
    
    async def record_login(self, user_id: int, ip_address: str = None) -> bool:
        """
        记录登录
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            return False
        
        user.record_login(ip_address)
        await user.save()
        
        return True
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        通过邮箱获取用户
        """
        return await User.get_or_none(email=email)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        通过用户名获取用户
        """
        return await User.get_or_none(username=username)
    
    async def check_username_exists(self, username: str) -> bool:
        """
        检查用户名是否存在
        """
        user = await User.get_or_none(username=username)
        return user is not None
    
    async def check_email_exists(self, email: str) -> bool:
        """
        检查邮箱是否存在
        """
        user = await User.get_or_none(email=email)
        return user is not None
    
    async def get_user_stats(self) -> dict:
        """
        获取用户统计信息
        """
        from datetime import date, timedelta
        
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        total_users = await User.all().count()
        active_users = await User.filter(status="active").count()
        
        new_users_today = await User.filter(
            created_at__gte=datetime.combine(today, datetime.min.time())
        ).count()
        
        new_users_this_week = await User.filter(
            created_at__gte=datetime.combine(week_ago, datetime.min.time())
        ).count()
        
        new_users_this_month = await User.filter(
            created_at__gte=datetime.combine(month_ago, datetime.min.time())
        ).count()
        
        login_count_today = await User.filter(
            last_login_at__gte=datetime.combine(today, datetime.min.time())
        ).count()
        
        login_count_this_week = await User.filter(
            last_login_at__gte=datetime.combine(week_ago, datetime.min.time())
        ).count()
        
        login_count_this_month = await User.filter(
            last_login_at__gte=datetime.combine(month_ago, datetime.min.time())
        ).count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "new_users_today": new_users_today,
            "new_users_this_week": new_users_this_week,
            "new_users_this_month": new_users_this_month,
            "login_count_today": login_count_today,
            "login_count_this_week": login_count_this_week,
            "login_count_this_month": login_count_this_month,
        }
