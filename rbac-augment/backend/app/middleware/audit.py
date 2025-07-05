"""
审计日志中间件
自动记录API操作和重要事件
"""

import time
import json
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from ..models.audit_log import AuditLog, AuditAction, AuditLevel, AuditStatus
from ..models.user import User


class AuditMiddleware(BaseHTTPMiddleware):
    """审计日志中间件"""
    
    def __init__(self, app, skip_paths: Optional[list] = None):
        super().__init__(app)
        # 跳过记录的路径
        self.skip_paths = skip_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/favicon.ico",
            "/health",
            "/metrics"
        ]
        
        # 需要记录的HTTP方法
        self.audit_methods = {"POST", "PUT", "DELETE", "PATCH"}
        
        # 敏感操作路径模式
        self.sensitive_patterns = [
            "/auth/login",
            "/auth/logout", 
            "/users",
            "/roles",
            "/permissions",
            "/data-permissions"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """处理请求并记录审计日志"""
        start_time = time.time()
        
        # 检查是否需要跳过
        if self._should_skip_audit(request):
            return await call_next(request)
        
        # 获取请求信息
        request_info = await self._extract_request_info(request)
        
        # 处理请求
        response = await call_next(request)
        
        # 计算响应时间
        response_time = int((time.time() - start_time) * 1000)
        
        # 记录审计日志
        await self._log_request(request, response, request_info, response_time)
        
        return response

    def _should_skip_audit(self, request: Request) -> bool:
        """判断是否应该跳过审计"""
        path = request.url.path
        
        # 跳过指定路径
        for skip_path in self.skip_paths:
            if path.startswith(skip_path):
                return True
        
        # 只记录API请求
        if not path.startswith("/api/"):
            return True
            
        # GET请求只记录敏感操作
        if request.method == "GET":
            return not any(pattern in path for pattern in self.sensitive_patterns)
        
        return False

    async def _extract_request_info(self, request: Request) -> Dict[str, Any]:
        """提取请求信息"""
        # 获取用户信息
        user = getattr(request.state, "user", None)
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 获取User-Agent
        user_agent = request.headers.get("user-agent", "")
        
        # 获取请求参数
        request_params = {}
        
        # 查询参数
        if request.query_params:
            request_params["query"] = dict(request.query_params)
        
        # 路径参数
        if hasattr(request, "path_params") and request.path_params:
            request_params["path"] = request.path_params
        
        # 请求体（对于POST/PUT请求）
        if request.method in {"POST", "PUT", "PATCH"}:
            try:
                # 注意：这里需要小心处理，因为request.body()只能读取一次
                # 在实际应用中，可能需要使用其他方式获取请求体
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    # 这里简化处理，实际应用中需要更复杂的逻辑
                    request_params["body"] = "JSON body (not captured for security)"
            except Exception:
                pass
        
        return {
            "user": user,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "request_params": request_params
        }

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # 直接连接
        if request.client:
            return request.client.host
        
        return "unknown"

    async def _log_request(
        self,
        request: Request,
        response: Response,
        request_info: Dict[str, Any],
        response_time: int
    ):
        """记录请求审计日志"""
        try:
            # 确定操作类型
            action = self._determine_action(request)
            
            # 确定资源类型
            resource_type = self._determine_resource_type(request.url.path)
            
            # 确定审计级别
            level = self._determine_audit_level(request, response)
            
            # 确定操作状态
            status = AuditStatus.SUCCESS if response.status_code < 400 else AuditStatus.FAILED
            
            # 生成描述
            description = self._generate_description(request, response, action, resource_type)
            
            # 提取资源信息
            resource_id, resource_name = self._extract_resource_info(request)
            
            # 记录日志
            await AuditLog.log_action(
                action=action,
                resource_type=resource_type,
                description=description,
                user_id=request_info["user"].id if request_info["user"] else None,
                username=request_info["user"].username if request_info["user"] else None,
                resource_id=resource_id,
                resource_name=resource_name,
                level=level,
                status=status,
                user_ip=request_info["client_ip"],
                user_agent=request_info["user_agent"],
                request_method=request.method,
                request_url=str(request.url),
                request_params=request_info["request_params"],
                response_status=response.status_code,
                response_time=response_time
            )
            
        except Exception as e:
            # 审计日志记录失败不应该影响正常请求
            print(f"Failed to log audit: {e}")

    def _determine_action(self, request: Request) -> AuditAction:
        """确定操作类型"""
        method = request.method
        path = request.url.path
        
        if "login" in path:
            return AuditAction.LOGIN
        elif "logout" in path:
            return AuditAction.LOGOUT
        elif method == "POST":
            if "assign" in path:
                return AuditAction.ASSIGN
            elif "revoke" in path:
                return AuditAction.REVOKE
            elif "export" in path:
                return AuditAction.EXPORT
            elif "import" in path:
                return AuditAction.IMPORT
            else:
                return AuditAction.CREATE
        elif method == "PUT" or method == "PATCH":
            return AuditAction.UPDATE
        elif method == "DELETE":
            return AuditAction.DELETE
        elif method == "GET":
            if "export" in path or "download" in path:
                return AuditAction.DOWNLOAD
            else:
                return AuditAction.VIEW
        else:
            return AuditAction.VIEW

    def _determine_resource_type(self, path: str) -> str:
        """确定资源类型"""
        if "/users" in path:
            return "user"
        elif "/roles" in path:
            return "role"
        elif "/permissions" in path:
            return "permission"
        elif "/menus" in path:
            return "menu"
        elif "/departments" in path:
            return "department"
        elif "/data-permissions" in path:
            return "data_permission"
        elif "/auth" in path:
            return "auth"
        else:
            return "system"

    def _determine_audit_level(self, request: Request, response: Response) -> AuditLevel:
        """确定审计级别"""
        path = request.url.path
        method = request.method
        
        # 失败操作提升级别
        if response.status_code >= 400:
            return AuditLevel.HIGH
        
        # 删除操作
        if method == "DELETE":
            return AuditLevel.HIGH
        
        # 权限相关操作
        if any(keyword in path for keyword in ["assign", "revoke", "permissions"]):
            return AuditLevel.HIGH
        
        # 用户管理操作
        if "/users" in path and method in {"POST", "PUT", "DELETE"}:
            return AuditLevel.MEDIUM
        
        # 登录登出
        if any(keyword in path for keyword in ["login", "logout"]):
            return AuditLevel.MEDIUM
        
        # 其他操作
        return AuditLevel.LOW

    def _generate_description(
        self,
        request: Request,
        response: Response,
        action: AuditAction,
        resource_type: str
    ) -> str:
        """生成操作描述"""
        method = request.method
        path = request.url.path
        status = "成功" if response.status_code < 400 else "失败"
        
        action_map = {
            AuditAction.CREATE: "创建",
            AuditAction.UPDATE: "更新", 
            AuditAction.DELETE: "删除",
            AuditAction.LOGIN: "登录",
            AuditAction.LOGOUT: "登出",
            AuditAction.ASSIGN: "分配",
            AuditAction.REVOKE: "撤销",
            AuditAction.VIEW: "查看",
            AuditAction.EXPORT: "导出",
            AuditAction.IMPORT: "导入",
            AuditAction.DOWNLOAD: "下载"
        }
        
        resource_map = {
            "user": "用户",
            "role": "角色",
            "permission": "权限",
            "menu": "菜单",
            "department": "部门",
            "data_permission": "数据权限",
            "auth": "认证",
            "system": "系统"
        }
        
        action_text = action_map.get(action, action.value)
        resource_text = resource_map.get(resource_type, resource_type)
        
        return f"{status}{action_text}{resource_text} - {method} {path}"

    def _extract_resource_info(self, request: Request) -> tuple[Optional[str], Optional[str]]:
        """提取资源信息"""
        # 从路径参数中提取资源ID
        path_params = getattr(request, "path_params", {})
        
        resource_id = None
        resource_name = None
        
        # 常见的ID参数名
        id_params = ["user_id", "role_id", "permission_id", "menu_id", "department_id", "id"]
        
        for param in id_params:
            if param in path_params:
                resource_id = str(path_params[param])
                break
        
        # 资源名称通常需要从请求体或数据库查询获取
        # 这里简化处理
        if resource_id:
            resource_name = f"Resource {resource_id}"
        
        return resource_id, resource_name
