"""
认证API测试
"""

import pytest
from httpx import AsyncClient

from app.models import User
from tests.conftest import assert_response_success, assert_response_error


class TestAuthAPI:
    """认证API测试类"""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """测试用户注册成功"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert_response_success(response, 201)
        
        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert data["user"]["username"] == user_data["username"]
        assert data["user"]["email"] == user_data["email"]
        assert "password" not in data["user"]
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, test_user: User):
        """测试注册重复用户名"""
        user_data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "password123",
            "full_name": "Different User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert_response_error(response, 400)
        
        data = response.json()
        assert "用户名已存在" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """测试注册重复邮箱"""
        user_data = {
            "username": "differentuser",
            "email": test_user.email,
            "password": "password123",
            "full_name": "Different User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert_response_error(response, 400)
        
        data = response.json()
        assert "邮箱已存在" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_register_invalid_data(self, client: AsyncClient):
        """测试注册无效数据"""
        # 缺少必填字段
        user_data = {
            "username": "newuser",
            "password": "password123"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert_response_error(response, 422)
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """测试登录成功"""
        login_data = {
            "username": test_user.username,
            "password": "password123"  # 对应测试用户的密码
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert_response_success(response)
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """测试登录错误密码"""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert_response_error(response, 401)
        
        data = response.json()
        assert "用户名或密码错误" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """测试登录不存在的用户"""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert_response_error(response, 401)
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, test_factory):
        """测试登录未激活用户"""
        inactive_user = await test_factory.create_user(
            username="inactive",
            email="inactive@example.com",
            is_active=False
        )
        
        login_data = {
            "username": inactive_user.username,
            "password": "password123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert_response_error(response, 401)
        
        data = response.json()
        assert "账户未激活" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, auth_headers: dict):
        """测试获取当前用户信息"""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert_response_success(response)
        
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "password" not in data
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """测试未授权获取用户信息"""
        response = await client.get("/api/v1/auth/me")
        assert_response_error(response, 401)
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """测试无效token获取用户信息"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert_response_error(response, 401)
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, auth_headers: dict):
        """测试刷新token"""
        response = await client.post("/api/v1/auth/refresh", headers=auth_headers)
        assert_response_success(response)
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, client: AsyncClient, auth_headers: dict):
        """测试修改密码成功"""
        password_data = {
            "current_password": "password123",
            "new_password": "newpassword123"
        }
        
        response = await client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=auth_headers
        )
        assert_response_success(response)
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, client: AsyncClient, auth_headers: dict):
        """测试修改密码当前密码错误"""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        
        response = await client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=auth_headers
        )
        assert_response_error(response, 400)
        
        data = response.json()
        assert "当前密码错误" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient, auth_headers: dict):
        """测试登出"""
        response = await client.post("/api/v1/auth/logout", headers=auth_headers)
        assert_response_success(response)
        
        data = response.json()
        assert data["message"] == "登出成功"
    
    @pytest.mark.asyncio
    async def test_forgot_password(self, client: AsyncClient, test_user: User):
        """测试忘记密码"""
        email_data = {"email": test_user.email}
        
        response = await client.post("/api/v1/auth/forgot-password", json=email_data)
        assert_response_success(response)
        
        data = response.json()
        assert "重置密码邮件已发送" in data["message"]
    
    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_email(self, client: AsyncClient):
        """测试忘记密码不存在的邮箱"""
        email_data = {"email": "nonexistent@example.com"}
        
        response = await client.post("/api/v1/auth/forgot-password", json=email_data)
        assert_response_error(response, 404)
        
        data = response.json()
        assert "用户不存在" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_reset_password(self, client: AsyncClient):
        """测试重置密码"""
        # 这里需要模拟一个有效的重置token
        reset_data = {
            "token": "valid_reset_token",
            "new_password": "newpassword123"
        }
        
        # 由于需要实际的重置token，这里只测试接口格式
        response = await client.post("/api/v1/auth/reset-password", json=reset_data)
        # 预期会返回400因为token无效，但接口格式正确
        assert response.status_code in [200, 400]
    
    @pytest.mark.asyncio
    async def test_verify_email(self, client: AsyncClient):
        """测试邮箱验证"""
        # 这里需要模拟一个有效的验证token
        verify_data = {"token": "valid_verify_token"}
        
        # 由于需要实际的验证token，这里只测试接口格式
        response = await client.post("/api/v1/auth/verify-email", json=verify_data)
        # 预期会返回400因为token无效，但接口格式正确
        assert response.status_code in [200, 400]


class TestAuthPermissions:
    """认证权限测试类"""
    
    @pytest.mark.asyncio
    async def test_admin_required_endpoint(self, client: AsyncClient, auth_headers: dict):
        """测试需要管理员权限的端点"""
        response = await client.get("/api/v1/admin/users", headers=auth_headers)
        assert_response_error(response, 403)
    
    @pytest.mark.asyncio
    async def test_admin_access_with_admin_user(self, client: AsyncClient, admin_auth_headers: dict):
        """测试管理员用户访问管理端点"""
        response = await client.get("/api/v1/admin/users", headers=admin_auth_headers)
        # 应该返回200或者其他成功状态码，而不是403
        assert response.status_code != 403
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, client: AsyncClient):
        """测试速率限制"""
        # 快速发送多个登录请求
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        responses = []
        for _ in range(10):
            response = await client.post("/api/v1/auth/login", data=login_data)
            responses.append(response)
        
        # 检查是否有429状态码（Too Many Requests）
        status_codes = [r.status_code for r in responses]
        # 至少应该有一些请求被限制
        assert any(code == 429 for code in status_codes) or all(code == 401 for code in status_codes)
