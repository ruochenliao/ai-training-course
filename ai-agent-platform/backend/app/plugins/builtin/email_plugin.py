"""
邮件发送插件

提供邮件发送功能的工具插件。
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List
import logging

from ..base import ToolPlugin, PluginMetadata, PluginType
from ..registry import plugin

logger = logging.getLogger(__name__)


@plugin
class EmailPlugin(ToolPlugin):
    """邮件发送插件"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="email_sender",
            version="1.0.0",
            description="发送邮件的工具插件",
            author="AI Agent Platform",
            plugin_type=PluginType.TOOL,
            config_schema={
                "type": "object",
                "properties": {
                    "smtp_server": {"type": "string", "description": "SMTP服务器地址"},
                    "smtp_port": {"type": "integer", "description": "SMTP端口", "default": 587},
                    "username": {"type": "string", "description": "邮箱用户名"},
                    "password": {"type": "string", "description": "邮箱密码"},
                    "use_tls": {"type": "boolean", "description": "是否使用TLS", "default": True},
                    "from_name": {"type": "string", "description": "发件人名称"}
                },
                "required": ["smtp_server", "username", "password"]
            },
            permissions=["network.smtp"],
            tags=["email", "communication", "notification"]
        )
    
    async def initialize(self) -> bool:
        """初始化插件"""
        try:
            # 验证配置
            required_config = ["smtp_server", "username", "password"]
            for key in required_config:
                if not self.get_config_value(key):
                    self.logger.error(f"缺少必需配置: {key}")
                    return False
            
            # 测试SMTP连接
            if not await self._test_connection():
                self.logger.error("SMTP连接测试失败")
                return False
            
            self.logger.info("邮件插件初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"邮件插件初始化失败: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """清理资源"""
        self.logger.info("邮件插件清理完成")
        return True
    
    async def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行邮件操作"""
        try:
            if action == "send_email":
                return await self._send_email(parameters)
            elif action == "send_bulk_email":
                return await self._send_bulk_email(parameters)
            elif action == "test_connection":
                success = await self._test_connection()
                return {"success": success, "message": "连接测试完成"}
            else:
                return {
                    "success": False,
                    "error": f"不支持的操作: {action}"
                }
                
        except Exception as e:
            self.logger.error(f"执行邮件操作失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_actions(self) -> List[str]:
        """获取可用操作列表"""
        return ["send_email", "send_bulk_email", "test_connection"]
    
    async def _send_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """发送单封邮件"""
        try:
            # 验证参数
            required_params = ["to", "subject", "content"]
            for param in required_params:
                if param not in parameters:
                    return {
                        "success": False,
                        "error": f"缺少必需参数: {param}"
                    }
            
            to_emails = parameters["to"]
            if isinstance(to_emails, str):
                to_emails = [to_emails]
            
            subject = parameters["subject"]
            content = parameters["content"]
            content_type = parameters.get("content_type", "plain")  # plain or html
            cc_emails = parameters.get("cc", [])
            bcc_emails = parameters.get("bcc", [])
            attachments = parameters.get("attachments", [])
            
            # 创建邮件
            msg = MIMEMultipart()
            msg["From"] = self._get_from_address()
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = subject
            
            if cc_emails:
                msg["Cc"] = ", ".join(cc_emails)
            
            # 添加邮件内容
            msg.attach(MIMEText(content, content_type, "utf-8"))
            
            # 添加附件
            for attachment in attachments:
                await self._add_attachment(msg, attachment)
            
            # 发送邮件
            all_recipients = to_emails + cc_emails + bcc_emails
            await self._send_message(msg, all_recipients)
            
            return {
                "success": True,
                "message": f"邮件发送成功，收件人: {len(all_recipients)}",
                "recipients": len(all_recipients)
            }
            
        except Exception as e:
            self.logger.error(f"发送邮件失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_bulk_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """批量发送邮件"""
        try:
            emails = parameters.get("emails", [])
            if not emails:
                return {
                    "success": False,
                    "error": "邮件列表为空"
                }
            
            success_count = 0
            failed_count = 0
            errors = []
            
            for email_data in emails:
                try:
                    result = await self._send_email(email_data)
                    if result["success"]:
                        success_count += 1
                    else:
                        failed_count += 1
                        errors.append({
                            "email": email_data.get("to", "unknown"),
                            "error": result["error"]
                        })
                except Exception as e:
                    failed_count += 1
                    errors.append({
                        "email": email_data.get("to", "unknown"),
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "message": f"批量发送完成，成功: {success_count}，失败: {failed_count}",
                "success_count": success_count,
                "failed_count": failed_count,
                "errors": errors
            }
            
        except Exception as e:
            self.logger.error(f"批量发送邮件失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _test_connection(self) -> bool:
        """测试SMTP连接"""
        try:
            smtp_server = self.get_config_value("smtp_server")
            smtp_port = self.get_config_value("smtp_port", 587)
            username = self.get_config_value("username")
            password = self.get_config_value("password")
            use_tls = self.get_config_value("use_tls", True)
            
            # 创建SMTP连接
            server = smtplib.SMTP(smtp_server, smtp_port)
            
            if use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)
            
            # 登录
            server.login(username, password)
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP连接测试失败: {e}")
            return False
    
    async def _send_message(self, msg: MIMEMultipart, recipients: List[str]):
        """发送邮件消息"""
        smtp_server = self.get_config_value("smtp_server")
        smtp_port = self.get_config_value("smtp_port", 587)
        username = self.get_config_value("username")
        password = self.get_config_value("password")
        use_tls = self.get_config_value("use_tls", True)
        
        # 创建SMTP连接
        server = smtplib.SMTP(smtp_server, smtp_port)
        
        try:
            if use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)
            
            # 登录
            server.login(username, password)
            
            # 发送邮件
            server.send_message(msg, to_addrs=recipients)
            
        finally:
            server.quit()
    
    async def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """添加附件"""
        try:
            filename = attachment.get("filename")
            content = attachment.get("content")
            content_type = attachment.get("content_type", "application/octet-stream")
            
            if not filename or not content:
                return
            
            # 创建附件
            part = MIMEBase(*content_type.split("/"))
            
            if isinstance(content, str):
                part.set_payload(content.encode("utf-8"))
            else:
                part.set_payload(content)
            
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}"
            )
            
            msg.attach(part)
            
        except Exception as e:
            self.logger.error(f"添加附件失败: {e}")
    
    def _get_from_address(self) -> str:
        """获取发件人地址"""
        username = self.get_config_value("username")
        from_name = self.get_config_value("from_name")
        
        if from_name:
            return f"{from_name} <{username}>"
        else:
            return username
