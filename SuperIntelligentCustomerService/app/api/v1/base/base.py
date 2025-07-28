import random
import random
import re
import smtplib
import string
from datetime import timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException

from ....controllers.user import user_controller
from ....core.ctx import CTX_USER_ID
from ....core.dependency import DependAuth
from ....models.admin import Api, Menu, Role, User
from ....schemas.auth import RegisterDTO, EmailCodeDTO
from ....schemas.base import Success
from ....schemas.login import *
from ....schemas.users import UpdatePassword, UserCreate
from ....settings import settings
from ....utils.jwt import create_access_token
from ....utils.password import get_password_hash, verify_password

router = APIRouter()


# 简单的内存缓存服务
class SimpleCache:
    """简单的内存缓存服务"""

    def __init__(self):
        self._cache: Dict[str, Dict] = {}

    def set(self, key: str, value: str, ttl: int = 300) -> None:
        """设置缓存值"""
        expire_time = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = {
            "value": value,
            "expire_time": expire_time
        }

    def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        if key not in self._cache:
            return None

        cache_item = self._cache[key]
        if datetime.now() > cache_item["expire_time"]:
            del self._cache[key]
            return None

        return cache_item["value"]

    def delete(self, key: str) -> None:
        """删除缓存值"""
        if key in self._cache:
            del self._cache[key]

    def clear_expired(self) -> None:
        """清理过期缓存"""
        now = datetime.now()
        expired_keys = [
            key for key, item in self._cache.items()
            if now > item["expire_time"]
        ]
        for key in expired_keys:
            del self._cache[key]


# 邮件发送服务
class EmailService:
    """邮件发送服务"""

    def __init__(self):
        # 邮件配置 - 可以从环境变量或配置文件中读取
        self.smtp_server = "smtp.qq.com"  # QQ邮箱SMTP服务器
        self.smtp_port = 587
        self.sender_email = "your_email@qq.com"  # 发送者邮箱
        self.sender_password = "your_app_password"  # 邮箱授权码
        self.enabled = False  # 默认禁用，需要配置后启用

    def send_verification_code(self, to_email: str, code: str) -> bool:
        """发送验证码邮件"""
        if not self.enabled:
            return False

        try:
            # 创建邮件内容
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = "超级智能客服 - 邮箱验证码"

            # 邮件正文
            body = f"""
            <html>
            <body>
                <h2>超级智能客服系统</h2>
                <p>您好！</p>
                <p>您的邮箱验证码是：<strong style="color: #007bff; font-size: 18px;">{code}</strong></p>
                <p>验证码有效期为5分钟，请及时使用。</p>
                <p>如果这不是您的操作，请忽略此邮件。</p>
                <br>
                <p>此邮件由系统自动发送，请勿回复。</p>
            </body>
            </html>
            """

            msg.attach(MIMEText(body, 'html', 'utf-8'))

            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"发送邮件失败: {e}")
            return False


# 全局实例
cache_service = SimpleCache()
email_service = EmailService()


@router.post("/access_token", summary="获取token")
async def login_access_token(credentials: CredentialsSchema):
    try:
        user: User = await user_controller.authenticate(credentials)
        await user_controller.update_last_login(user.id)
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + access_token_expires

        data = JWTOut(
            access_token=create_access_token(
                data=JWTPayload(
                    user_id=user.id,
                    username=user.username,
                    is_superuser=user.is_superuser,
                    exp=expire,
                )
            ),
            username=user.username,
        )
        return Success(data=data.model_dump())
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"认证失败: {str(e)}")


@router.get("/userinfo", summary="查看用户信息", dependencies=[DependAuth])
async def get_userinfo():
    try:
        user_id = CTX_USER_ID.get()
        user_obj = await user_controller.get(id=user_id)
        data = await user_obj.to_dict(exclude_fields=["password"])
        data["avatar"] = "https://avatars.githubusercontent.com/u/54677442?v=4"
        return Success(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")


@router.get("/usermenu", summary="查看用户菜单", dependencies=[DependAuth])
async def get_user_menu():
    try:
        user_id = CTX_USER_ID.get()
        user_obj = await User.filter(id=user_id).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="用户不存在")

        menus: list[Menu] = []
        if user_obj.is_superuser:
            menus = await Menu.all()
        else:
            role_objs: list[Role] = await user_obj.roles
            for role_obj in role_objs:
                menu = await role_obj.menus
                menus.extend(menu)
            menus = list(set(menus))
        parent_menus: list[Menu] = []
        for menu in menus:
            if menu.parent_id == 0:
                parent_menus.append(menu)
        res = []
        for parent_menu in parent_menus:
            parent_menu_dict = await parent_menu.to_dict()
            parent_menu_dict["children"] = []
            for menu in menus:
                if menu.parent_id == parent_menu.id:
                    parent_menu_dict["children"].append(await menu.to_dict())
            res.append(parent_menu_dict)
        return Success(data=res)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户菜单失败: {str(e)}")


@router.get("/userapi", summary="查看用户API", dependencies=[DependAuth])
async def get_user_api():
    try:
        user_id = CTX_USER_ID.get()
        user_obj = await User.filter(id=user_id).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="用户不存在")

        if user_obj.is_superuser:
            api_objs: list[Api] = await Api.all()
            apis = [api.method.lower() + api.path for api in api_objs]
            return Success(data=apis)
        role_objs: list[Role] = await user_obj.roles
        apis = []
        for role_obj in role_objs:
            api_objs: list[Api] = await role_obj.apis
            apis.extend([api.method.lower() + api.path for api in api_objs])
        apis = list(set(apis))
        return Success(data=apis)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户API失败: {str(e)}")


@router.post("/update_password", summary="修改密码", dependencies=[DependAuth])
async def update_user_password(req_in: UpdatePassword):
    try:
        user_id = CTX_USER_ID.get()
        user = await user_controller.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        verified = verify_password(req_in.old_password, user.password)
        if not verified:
            raise HTTPException(status_code=400, detail="旧密码验证错误")

        user.password = get_password_hash(req_in.new_password)
        await user.save()
        return Success(msg="修改成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修改密码失败: {str(e)}")


@router.post("/email/code", summary="发送邮箱验证码")
async def send_email_code(email_data: EmailCodeDTO):
    """发送邮箱验证码"""
    try:
        if not email_data.username:
            raise HTTPException(status_code=400, detail="邮箱地址不能为空")

        # 验证邮箱格式
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email_data.username):
            raise HTTPException(status_code=400, detail="邮箱格式不正确")

        # 检查发送频率限制（同一邮箱60秒内只能发送一次）
        rate_limit_key = f"email_rate_limit:{email_data.username}"
        if cache_service.get(rate_limit_key):
            raise HTTPException(status_code=429, detail="发送过于频繁，请60秒后再试")

        # 生成6位数字验证码
        code = ''.join(random.choices(string.digits, k=6))

        # 将验证码存储到缓存中，设置过期时间为5分钟
        cache_key = f"email_code:{email_data.username}"
        cache_service.set(cache_key, code, ttl=300)  # 5分钟过期

        # 设置发送频率限制
        cache_service.set(rate_limit_key, "1", ttl=60)  # 60秒限制

        # 尝试发送邮件
        email_sent = False
        if email_service.enabled:
            email_sent = email_service.send_verification_code(email_data.username, code)

        # 清理过期缓存
        cache_service.clear_expired()

        # 根据邮件发送状态返回不同的响应
        if email_sent:
            return Success(msg="验证码已发送到您的邮箱，请查收")
        else:
            # 开发环境下返回验证码用于测试
            return Success(
                msg="验证码已生成（开发模式）",
                data={"code": code, "note": "生产环境中需要配置邮件服务"}
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送验证码失败: {str(e)}")


@router.post("/register", summary="用户注册")
async def register(register_data: RegisterDTO):
    """用户注册接口"""
    try:
        # 验证邮箱格式
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, register_data.username):
            raise HTTPException(status_code=400, detail="邮箱格式不正确")

        # 检查用户是否已存在
        existing_user = await user_controller.get_by_email(register_data.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="该邮箱已被注册")

        # 验证密码确认
        if register_data.confirm_password and register_data.password != register_data.confirm_password:
            raise HTTPException(status_code=400, detail="两次输入的密码不一致")

        # 验证密码强度
        if len(register_data.password) < 6:
            raise HTTPException(status_code=400, detail="密码长度至少6位")

        # 验证邮箱验证码
        if not register_data.code:
            raise HTTPException(status_code=400, detail="验证码不能为空")

        # 从缓存中获取验证码
        cache_key = f"email_code:{register_data.username}"
        cached_code = cache_service.get(cache_key)

        if not cached_code:
            raise HTTPException(status_code=400, detail="验证码已过期或不存在，请重新获取")

        if cached_code != register_data.code:
            raise HTTPException(status_code=400, detail="验证码错误")

        # 验证成功，删除验证码缓存
        cache_service.delete(cache_key)

        # 生成唯一的用户名（如果邮箱前缀已存在，则添加随机数字）
        base_username = register_data.username.split("@")[0]
        username = base_username
        counter = 1
        while await user_controller.get_by_username(username):
            username = f"{base_username}{counter}"
            counter += 1

        # 创建新用户
        user_create = UserCreate(
            username=username,
            email=register_data.username,
            password=register_data.password,
            is_active=True,
            is_superuser=False
        )

        user = await user_controller.create_user(user_create)

        # 清理过期缓存
        cache_service.clear_expired()

        return Success(
            msg="注册成功",
            data={
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@router.post("/email/verify", summary="验证邮箱验证码")
async def verify_email_code(email: str, code: str):
    """验证邮箱验证码（不删除验证码）"""
    try:
        if not email:
            raise HTTPException(status_code=400, detail="邮箱地址不能为空")

        if not code:
            raise HTTPException(status_code=400, detail="验证码不能为空")

        # 验证邮箱格式
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise HTTPException(status_code=400, detail="邮箱格式不正确")

        # 从缓存中获取验证码
        cache_key = f"email_code:{email}"
        cached_code = cache_service.get(cache_key)

        if not cached_code:
            raise HTTPException(status_code=400, detail="验证码已过期或不存在")

        if cached_code != code:
            raise HTTPException(status_code=400, detail="验证码错误")

        # 清理过期缓存
        cache_service.clear_expired()

        return Success(msg="验证码验证成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证码验证失败: {str(e)}")


@router.get("/cache/stats", summary="缓存统计信息")
async def get_cache_stats():
    """获取缓存统计信息（仅用于调试）"""
    try:
        # 清理过期缓存
        cache_service.clear_expired()

        stats = {
            "total_keys": len(cache_service._cache),
            "keys": list(cache_service._cache.keys()),
            "current_time": datetime.now().isoformat()
        }

        return Success(data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")


@router.post("/email/config", summary="配置邮件服务", dependencies=[DependAuth])
async def configure_email_service(
    smtp_server: str,
    smtp_port: int,
    sender_email: str,
    sender_password: str
):
    """配置邮件服务（需要管理员权限）"""
    try:
        user_id = CTX_USER_ID.get()
        user = await user_controller.get(user_id)

        # 检查是否为超级管理员
        if not user.is_superuser:
            raise HTTPException(status_code=403, detail="只有超级管理员可以配置邮件服务")

        # 更新邮件服务配置
        email_service.smtp_server = smtp_server
        email_service.smtp_port = smtp_port
        email_service.sender_email = sender_email
        email_service.sender_password = sender_password
        email_service.enabled = True

        # 测试邮件配置
        try:
            test_sent = email_service.send_verification_code(
                sender_email,
                "123456"  # 测试验证码
            )
            if test_sent:
                return Success(msg="邮件服务配置成功并测试通过")
            else:
                email_service.enabled = False
                return Success(msg="邮件服务配置已保存，但测试发送失败，请检查配置")
        except Exception as e:
            email_service.enabled = False
            return Success(msg=f"邮件服务配置已保存，但测试失败: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置邮件服务失败: {str(e)}")


@router.get("/email/status", summary="获取邮件服务状态")
async def get_email_service_status():
    """获取邮件服务状态"""
    try:
        status = {
            "enabled": email_service.enabled,
            "smtp_server": email_service.smtp_server if email_service.enabled else "未配置",
            "smtp_port": email_service.smtp_port if email_service.enabled else 0,
            "sender_email": email_service.sender_email if email_service.enabled else "未配置"
        }

        return Success(data=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取邮件服务状态失败: {str(e)}")
