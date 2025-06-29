"""
增强的请求验证中间件
"""

import re
import json
import time
import ipaddress
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from app.core.config import settings
from app.core.error_codes import ErrorCode, create_error_response
from app.core.error_monitoring import get_error_monitor


class SecurityLevel(str, Enum):
    """安全级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationRule:
    """验证规则"""
    name: str
    pattern: str
    message: str
    enabled: bool = True
    security_level: SecurityLevel = SecurityLevel.MEDIUM


@dataclass
class IPRule:
    """IP规则"""
    ip_range: str
    rule_type: str  # "allow" or "deny"
    description: str
    enabled: bool = True


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """增强的请求验证中间件"""
    
    def __init__(
        self,
        app,
        enable_ip_filtering: bool = True,
        enable_input_validation: bool = True,
        enable_security_headers: bool = True,
        enable_content_validation: bool = True,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        max_json_depth: int = 10,
        rate_limit_per_ip: int = 100,  # 每分钟请求数
    ):
        super().__init__(app)
        self.enable_ip_filtering = enable_ip_filtering
        self.enable_input_validation = enable_input_validation
        self.enable_security_headers = enable_security_headers
        self.enable_content_validation = enable_content_validation
        self.max_request_size = max_request_size
        self.max_json_depth = max_json_depth
        self.rate_limit_per_ip = rate_limit_per_ip
        
        # IP白名单和黑名单
        self.ip_whitelist: Set[str] = set()
        self.ip_blacklist: Set[str] = set()
        self.ip_rules: List[IPRule] = []
        
        # 验证规则
        self.validation_rules: List[ValidationRule] = []
        self._init_default_validation_rules()
        
        # 限流记录
        self.rate_limit_records: Dict[str, List[float]] = {}
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "validation_failures": 0,
            "ip_blocks": 0,
            "rate_limit_blocks": 0,
            "security_violations": 0,
        }
    
    def _init_default_validation_rules(self):
        """初始化默认验证规则"""
        self.validation_rules = [
            # SQL注入检测
            ValidationRule(
                name="sql_injection",
                pattern=r"(?i)(union|select|insert|update|delete|drop|create|alter|exec|execute|script|javascript|vbscript)",
                message="检测到潜在的SQL注入攻击",
                security_level=SecurityLevel.HIGH
            ),
            
            # XSS攻击检测
            ValidationRule(
                name="xss_attack",
                pattern=r"(?i)(<script|javascript:|vbscript:|onload=|onerror=|onclick=|onmouseover=)",
                message="检测到潜在的XSS攻击",
                security_level=SecurityLevel.HIGH
            ),
            
            # 路径遍历攻击
            ValidationRule(
                name="path_traversal",
                pattern=r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)",
                message="检测到潜在的路径遍历攻击",
                security_level=SecurityLevel.HIGH
            ),
            
            # 命令注入检测
            ValidationRule(
                name="command_injection",
                pattern=r"(?i)(;|\||&|`|\$\(|wget|curl|nc|netcat|bash|sh|cmd|powershell)",
                message="检测到潜在的命令注入攻击",
                security_level=SecurityLevel.CRITICAL
            ),
            
            # LDAP注入检测
            ValidationRule(
                name="ldap_injection",
                pattern=r"(\*|\(|\)|\\|/|null|nil)",
                message="检测到潜在的LDAP注入攻击",
                security_level=SecurityLevel.MEDIUM
            ),
            
            # 恶意文件上传检测
            ValidationRule(
                name="malicious_file",
                pattern=r"(?i)\.(exe|bat|cmd|com|pif|scr|vbs|js|jar|php|asp|jsp|sh)$",
                message="检测到潜在的恶意文件类型",
                security_level=SecurityLevel.HIGH
            ),
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """中间件主要处理逻辑"""
        self.stats["total_requests"] += 1
        start_time = time.time()
        
        try:
            # 1. IP过滤检查
            if self.enable_ip_filtering:
                ip_check_result = await self._check_ip_filtering(request)
                if not ip_check_result["allowed"]:
                    self.stats["blocked_requests"] += 1
                    self.stats["ip_blocks"] += 1
                    return self._create_blocked_response(ip_check_result["reason"])
            
            # 2. 限流检查
            rate_limit_result = await self._check_rate_limit(request)
            if not rate_limit_result["allowed"]:
                self.stats["blocked_requests"] += 1
                self.stats["rate_limit_blocks"] += 1
                return self._create_rate_limit_response(rate_limit_result)
            
            # 3. 请求大小检查
            if await self._check_request_size(request):
                self.stats["blocked_requests"] += 1
                return self._create_blocked_response("请求体过大")
            
            # 4. 内容验证
            if self.enable_content_validation:
                content_validation_result = await self._validate_request_content(request)
                if not content_validation_result["valid"]:
                    self.stats["blocked_requests"] += 1
                    self.stats["validation_failures"] += 1
                    return self._create_blocked_response(content_validation_result["reason"])
            
            # 5. 输入验证
            if self.enable_input_validation:
                input_validation_result = await self._validate_input_security(request)
                if not input_validation_result["valid"]:
                    self.stats["blocked_requests"] += 1
                    self.stats["security_violations"] += 1
                    return self._create_security_violation_response(input_validation_result)
            
            # 处理请求
            response = await call_next(request)
            
            # 6. 添加安全响应头
            if self.enable_security_headers:
                self._add_security_headers(response)
            
            # 记录处理时间
            process_time = time.time() - start_time
            response.headers["X-Validation-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            logger.error(f"请求验证中间件异常: {e}")
            # 记录到错误监控
            error_monitor = get_error_monitor()
            error_monitor.record_error(
                error_code="VAL_9001",
                path=request.url.path,
                method=request.method,
                response_time=time.time() - start_time,
                details={"middleware_error": str(e)}
            )
            raise
    
    async def _check_ip_filtering(self, request: Request) -> Dict[str, Any]:
        """检查IP过滤"""
        client_ip = self._get_client_ip(request)
        
        # 检查黑名单
        if self._is_ip_in_blacklist(client_ip):
            logger.warning(f"IP黑名单拦截: {client_ip}")
            return {"allowed": False, "reason": f"IP {client_ip} 在黑名单中"}
        
        # 检查白名单（如果启用）
        if self.ip_whitelist and not self._is_ip_in_whitelist(client_ip):
            logger.warning(f"IP白名单拦截: {client_ip}")
            return {"allowed": False, "reason": f"IP {client_ip} 不在白名单中"}
        
        # 检查IP规则
        for rule in self.ip_rules:
            if not rule.enabled:
                continue
                
            if self._ip_matches_rule(client_ip, rule):
                if rule.rule_type == "deny":
                    logger.warning(f"IP规则拦截: {client_ip} - {rule.description}")
                    return {"allowed": False, "reason": f"IP被规则拦截: {rule.description}"}
                elif rule.rule_type == "allow":
                    return {"allowed": True, "reason": "IP规则允许"}
        
        return {"allowed": True, "reason": "IP检查通过"}
    
    async def _check_rate_limit(self, request: Request) -> Dict[str, Any]:
        """检查限流"""
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # 清理过期记录
        self._cleanup_rate_limit_records(current_time)
        
        # 获取当前IP的请求记录
        if client_ip not in self.rate_limit_records:
            self.rate_limit_records[client_ip] = []
        
        ip_requests = self.rate_limit_records[client_ip]
        
        # 统计最近一分钟的请求数
        recent_requests = [
            req_time for req_time in ip_requests
            if current_time - req_time <= 60
        ]
        
        if len(recent_requests) >= self.rate_limit_per_ip:
            logger.warning(f"限流拦截: IP {client_ip} 请求频率过高")
            return {
                "allowed": False,
                "reason": "请求频率过高",
                "current_requests": len(recent_requests),
                "limit": self.rate_limit_per_ip,
                "reset_time": int(current_time + 60)
            }
        
        # 记录当前请求
        self.rate_limit_records[client_ip].append(current_time)
        
        return {
            "allowed": True,
            "current_requests": len(recent_requests) + 1,
            "limit": self.rate_limit_per_ip,
            "remaining": self.rate_limit_per_ip - len(recent_requests) - 1
        }
    
    async def _check_request_size(self, request: Request) -> bool:
        """检查请求大小"""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_request_size:
                    logger.warning(f"请求体过大: {size} > {self.max_request_size}")
                    return True
            except ValueError:
                pass
        
        return False
    
    async def _validate_request_content(self, request: Request) -> Dict[str, Any]:
        """验证请求内容"""
        try:
            # 检查Content-Type
            content_type = request.headers.get("content-type", "")
            
            # 如果是JSON请求，验证JSON格式和深度
            if "application/json" in content_type:
                try:
                    # 获取请求体（注意：这会消耗请求体，需要重新设置）
                    body = await request.body()
                    if body:
                        json_data = json.loads(body)
                        
                        # 检查JSON深度
                        if self._get_json_depth(json_data) > self.max_json_depth:
                            return {
                                "valid": False,
                                "reason": f"JSON嵌套深度超过限制 {self.max_json_depth}"
                            }
                        
                        # 重新设置请求体
                        request._body = body
                        
                except json.JSONDecodeError:
                    return {"valid": False, "reason": "无效的JSON格式"}
                except Exception as e:
                    return {"valid": False, "reason": f"JSON验证失败: {str(e)}"}
            
            return {"valid": True, "reason": "内容验证通过"}
            
        except Exception as e:
            logger.error(f"内容验证异常: {e}")
            return {"valid": False, "reason": f"内容验证异常: {str(e)}"}
    
    async def _validate_input_security(self, request: Request) -> Dict[str, Any]:
        """验证输入安全性"""
        try:
            # 检查URL路径
            path = str(request.url.path)
            for rule in self.validation_rules:
                if not rule.enabled:
                    continue
                    
                if re.search(rule.pattern, path):
                    logger.warning(f"安全规则触发: {rule.name} - {path}")
                    return {
                        "valid": False,
                        "reason": rule.message,
                        "rule": rule.name,
                        "security_level": rule.security_level.value
                    }
            
            # 检查查询参数
            for key, value in request.query_params.items():
                combined_input = f"{key}={value}"
                for rule in self.validation_rules:
                    if not rule.enabled:
                        continue
                        
                    if re.search(rule.pattern, combined_input):
                        logger.warning(f"安全规则触发: {rule.name} - 查询参数: {combined_input}")
                        return {
                            "valid": False,
                            "reason": rule.message,
                            "rule": rule.name,
                            "security_level": rule.security_level.value,
                            "location": "query_params"
                        }
            
            # 检查请求头
            for header_name, header_value in request.headers.items():
                if header_name.lower() in ["user-agent", "referer", "x-forwarded-for"]:
                    for rule in self.validation_rules:
                        if not rule.enabled:
                            continue
                            
                        if re.search(rule.pattern, header_value):
                            logger.warning(f"安全规则触发: {rule.name} - 请求头: {header_name}")
                            return {
                                "valid": False,
                                "reason": rule.message,
                                "rule": rule.name,
                                "security_level": rule.security_level.value,
                                "location": "headers"
                            }
            
            return {"valid": True, "reason": "输入安全验证通过"}
            
        except Exception as e:
            logger.error(f"输入安全验证异常: {e}")
            return {"valid": False, "reason": f"安全验证异常: {str(e)}"}
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 检查代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # 使用直接连接IP
        return request.client.host if request.client else "unknown"
    
    def _is_ip_in_whitelist(self, ip: str) -> bool:
        """检查IP是否在白名单中"""
        return ip in self.ip_whitelist or self._check_ip_ranges(ip, self.ip_whitelist)
    
    def _is_ip_in_blacklist(self, ip: str) -> bool:
        """检查IP是否在黑名单中"""
        return ip in self.ip_blacklist or self._check_ip_ranges(ip, self.ip_blacklist)
    
    def _check_ip_ranges(self, ip: str, ip_set: Set[str]) -> bool:
        """检查IP是否在IP范围内"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for ip_range in ip_set:
                try:
                    if "/" in ip_range:
                        network = ipaddress.ip_network(ip_range, strict=False)
                        if ip_obj in network:
                            return True
                    elif ip == ip_range:
                        return True
                except ValueError:
                    continue
        except ValueError:
            pass
        
        return False
    
    def _ip_matches_rule(self, ip: str, rule: IPRule) -> bool:
        """检查IP是否匹配规则"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            if "/" in rule.ip_range:
                network = ipaddress.ip_network(rule.ip_range, strict=False)
                return ip_obj in network
            else:
                return ip == rule.ip_range
        except ValueError:
            return False
    
    def _get_json_depth(self, obj: Any, depth: int = 0) -> int:
        """获取JSON嵌套深度"""
        if isinstance(obj, dict):
            if not obj:
                return depth
            return max(self._get_json_depth(value, depth + 1) for value in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return depth
            return max(self._get_json_depth(item, depth + 1) for item in obj)
        else:
            return depth
    
    def _cleanup_rate_limit_records(self, current_time: float):
        """清理过期的限流记录"""
        for ip in list(self.rate_limit_records.keys()):
            # 保留最近5分钟的记录
            self.rate_limit_records[ip] = [
                req_time for req_time in self.rate_limit_records[ip]
                if current_time - req_time <= 300
            ]
            
            # 如果没有记录，删除该IP
            if not self.rate_limit_records[ip]:
                del self.rate_limit_records[ip]
    
    def _add_security_headers(self, response: Response):
        """添加安全响应头"""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
    
    def _create_blocked_response(self, reason: str) -> Response:
        """创建被阻止的响应"""
        return create_error_response(
            error_code=ErrorCode.REQUEST_BLOCKED,
            message=reason,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    def _create_rate_limit_response(self, rate_limit_info: Dict[str, Any]) -> Response:
        """创建限流响应"""
        response = create_error_response(
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="请求频率过高，请稍后再试",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )
        
        # 添加限流相关头部
        response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = "0"
        response.headers["X-RateLimit-Reset"] = str(rate_limit_info.get("reset_time", 0))
        response.headers["Retry-After"] = "60"
        
        return response
    
    def _create_security_violation_response(self, violation_info: Dict[str, Any]) -> Response:
        """创建安全违规响应"""
        return create_error_response(
            error_code=ErrorCode.SECURITY_VIOLATION,
            message=violation_info["reason"],
            status_code=status.HTTP_400_BAD_REQUEST,
            details={
                "rule": violation_info.get("rule"),
                "security_level": violation_info.get("security_level"),
                "location": violation_info.get("location")
            }
        )
    
    # 管理方法
    def add_ip_to_whitelist(self, ip: str):
        """添加IP到白名单"""
        self.ip_whitelist.add(ip)
        logger.info(f"IP添加到白名单: {ip}")
    
    def add_ip_to_blacklist(self, ip: str):
        """添加IP到黑名单"""
        self.ip_blacklist.add(ip)
        logger.info(f"IP添加到黑名单: {ip}")
    
    def remove_ip_from_whitelist(self, ip: str):
        """从白名单移除IP"""
        self.ip_whitelist.discard(ip)
        logger.info(f"IP从白名单移除: {ip}")
    
    def remove_ip_from_blacklist(self, ip: str):
        """从黑名单移除IP"""
        self.ip_blacklist.discard(ip)
        logger.info(f"IP从黑名单移除: {ip}")
    
    def add_validation_rule(self, rule: ValidationRule):
        """添加验证规则"""
        self.validation_rules.append(rule)
        logger.info(f"添加验证规则: {rule.name}")
    
    def remove_validation_rule(self, rule_name: str):
        """移除验证规则"""
        self.validation_rules = [
            rule for rule in self.validation_rules
            if rule.name != rule_name
        ]
        logger.info(f"移除验证规则: {rule_name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "whitelist_size": len(self.ip_whitelist),
            "blacklist_size": len(self.ip_blacklist),
            "validation_rules": len(self.validation_rules),
            "active_rate_limits": len(self.rate_limit_records),
        }
