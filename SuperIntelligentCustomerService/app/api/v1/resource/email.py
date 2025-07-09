import random
import string

from fastapi import APIRouter

from ....schemas import Success, Fail
from ....schemas.auth import EmailCodeDTO

router = APIRouter()


@router.post("/code", summary="发送邮箱验证码")
async def send_email_code(email_data: EmailCodeDTO):
    """发送邮箱验证码"""
    try:
        if not email_data.username:
            return Fail(msg="邮箱地址不能为空")
        
        # 生成6位数字验证码
        code = ''.join(random.choices(string.digits, k=6))
        
        # TODO: 实现真实的邮件发送逻辑
        # 这里应该：
        # 1. 验证邮箱格式
        # 2. 将验证码存储到Redis或数据库中，设置过期时间（如5分钟）
        # 3. 发送邮件
        # 4. 记录发送日志
        
        # 模拟发送成功（开发环境下可以返回验证码用于测试）
        return Success(
            msg="验证码已发送到您的邮箱，请查收",
            data={"code": code}  # 生产环境中应该移除这个字段
        )
        
    except Exception as e:
        return Fail(msg=f"发送验证码失败: {str(e)}")


@router.post("/verify", summary="验证邮箱验证码")
async def verify_email_code(
    email: str,
    code: str
):
    """验证邮箱验证码"""
    try:
        # TODO: 实现验证码验证逻辑
        # 这里应该：
        # 1. 从Redis或数据库中获取存储的验证码
        # 2. 比较验证码是否正确
        # 3. 检查是否过期
        # 4. 验证成功后删除验证码
        
        # 模拟验证成功
        return Success(msg="验证码验证成功")
        
    except Exception as e:
        return Fail(msg=f"验证码验证失败: {str(e)}")
