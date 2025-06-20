"""
文件工具集
基于MCP协议的文件操作和管理工具实现
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import mimetypes
import base64
from datetime import datetime
import json

from loguru import logger
from app.services.mcp_service import MCPTool, MCPContext
from app.services.enhanced_document_service import enhanced_document_service
from app.core.config import settings


class FileTools:
    """文件工具集"""
    
    def __init__(self):
        """初始化文件工具"""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
    async def get_tools(self) -> List[MCPTool]:
        """获取所有文件工具"""
        return [
            MCPTool(
                name="upload_file",
                description="上传文件到系统中",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_content": {
                            "type": "string",
                            "description": "文件内容（base64编码）"
                        },
                        "file_name": {
                            "type": "string",
                            "description": "文件名"
                        },
                        "conversation_id": {
                            "type": "string",
                            "description": "对话ID"
                        },
                        "extract_images": {
                            "type": "boolean",
                            "description": "是否提取图片",
                            "default": True
                        },
                        "extract_tables": {
                            "type": "boolean",
                            "description": "是否提取表格",
                            "default": True
                        }
                    },
                    "required": ["file_content", "file_name"]
                },
                handler=self.upload_file,
                category="file"
            ),
            
            MCPTool(
                name="list_files",
                description="列出用户上传的文件",
                parameters={
                    "type": "object",
                    "properties": {
                        "conversation_id": {
                            "type": "string",
                            "description": "对话ID，用于过滤文件"
                        },
                        "file_type": {
                            "type": "string",
                            "description": "文件类型过滤"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回结果数量限制",
                            "default": 20
                        }
                    },
                    "required": []
                },
                handler=self.list_files,
                category="file"
            ),
            
            MCPTool(
                name="get_file_info",
                description="获取文件详细信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "文档ID"
                        }
                    },
                    "required": ["document_id"]
                },
                handler=self.get_file_info,
                category="file"
            ),
            
            MCPTool(
                name="delete_file",
                description="删除文件",
                parameters={
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "文档ID"
                        }
                    },
                    "required": ["document_id"]
                },
                handler=self.delete_file,
                category="file"
            ),
            
            MCPTool(
                name="read_file_content",
                description="读取文件内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "文档ID"
                        },
                        "max_length": {
                            "type": "integer",
                            "description": "最大返回长度",
                            "default": 5000
                        }
                    },
                    "required": ["document_id"]
                },
                handler=self.read_file_content,
                category="file"
            ),
            
            MCPTool(
                name="analyze_file",
                description="分析文件内容，提取关键信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "文档ID"
                        },
                        "analysis_type": {
                            "type": "string",
                            "description": "分析类型",
                            "enum": ["summary", "keywords", "entities", "structure"],
                            "default": "summary"
                        }
                    },
                    "required": ["document_id"]
                },
                handler=self.analyze_file,
                category="file"
            ),
            
            MCPTool(
                name="create_text_file",
                description="创建文本文件",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_name": {
                            "type": "string",
                            "description": "文件名"
                        },
                        "content": {
                            "type": "string",
                            "description": "文件内容"
                        },
                        "conversation_id": {
                            "type": "string",
                            "description": "对话ID"
                        }
                    },
                    "required": ["file_name", "content"]
                },
                handler=self.create_text_file,
                category="file"
            ),
            
            MCPTool(
                name="get_file_statistics",
                description="获取文件统计信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "conversation_id": {
                            "type": "string",
                            "description": "对话ID，用于过滤统计范围"
                        }
                    },
                    "required": []
                },
                handler=self.get_file_statistics,
                category="file"
            )
        ]
    
    async def upload_file(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """上传文件"""
        try:
            file_content_b64 = params["file_content"]
            file_name = params["file_name"]
            conversation_id = params.get("conversation_id")
            extract_images = params.get("extract_images", True)
            extract_tables = params.get("extract_tables", True)
            
            # 获取用户ID
            user_id = context.user_id if context else None
            if not user_id:
                return {"error": "需要用户ID进行文件上传"}
            
            # 解码文件内容
            try:
                file_content = base64.b64decode(file_content_b64)
            except Exception as e:
                return {"error": f"文件内容解码失败: {e}"}
            
            # 保存文件
            file_path = self.upload_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # 处理文档
            result = await enhanced_document_service.process_document(
                file_path=str(file_path),
                file_name=file_name,
                user_id=int(user_id),
                conversation_id=conversation_id,
                extract_images=extract_images,
                extract_tables=extract_tables
            )
            
            return {
                "success": True,
                "document_id": result["document_id"],
                "file_name": file_name,
                "file_size": len(file_content),
                "processing_status": result["status"],
                "message": "文件上传成功，正在后台处理"
            }
            
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            return {"error": str(e), "success": False}
    
    async def list_files(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """列出文件"""
        try:
            conversation_id = params.get("conversation_id")
            file_type = params.get("file_type")
            limit = params.get("limit", 20)
            
            # 获取用户ID
            user_id = context.user_id if context else None
            if not user_id:
                return {"error": "需要用户ID进行文件列表查询"}
            
            # 这里应该调用数据库查询，暂时返回模拟数据
            mock_files = [
                {
                    "document_id": "doc_001",
                    "file_name": "产品手册.pdf",
                    "file_type": ".pdf",
                    "file_size": 1024000,
                    "status": "completed",
                    "created_at": "2024-01-27T10:00:00Z",
                    "conversation_id": conversation_id
                },
                {
                    "document_id": "doc_002",
                    "file_name": "技术文档.docx",
                    "file_type": ".docx",
                    "file_size": 512000,
                    "status": "completed",
                    "created_at": "2024-01-27T11:00:00Z",
                    "conversation_id": conversation_id
                }
            ]
            
            # 应用过滤器
            filtered_files = mock_files
            if file_type:
                filtered_files = [f for f in filtered_files if f["file_type"] == file_type]
            if conversation_id:
                filtered_files = [f for f in filtered_files if f["conversation_id"] == conversation_id]
            
            return {
                "files": filtered_files[:limit],
                "total": len(filtered_files),
                "filters": {
                    "conversation_id": conversation_id,
                    "file_type": file_type,
                    "limit": limit
                }
            }
            
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            return {"error": str(e), "files": []}
    
    async def get_file_info(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            document_id = params["document_id"]
            
            # 获取用户ID
            user_id = context.user_id if context else None
            if not user_id:
                return {"error": "需要用户ID进行文件信息查询"}
            
            # 调用文档服务获取信息
            document_info = await enhanced_document_service.get_document_info(
                document_id=document_id,
                user_id=int(user_id)
            )
            
            if not document_info:
                return {"error": "文档不存在或无权访问"}
            
            return document_info
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return {"error": str(e)}
    
    async def delete_file(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """删除文件"""
        try:
            document_id = params["document_id"]
            
            # 获取用户ID
            user_id = context.user_id if context else None
            if not user_id:
                return {"error": "需要用户ID进行文件删除"}
            
            # 调用文档服务删除文件
            success = await enhanced_document_service.delete_document(
                document_id=document_id,
                user_id=int(user_id)
            )
            
            if success:
                return {"success": True, "message": "文件删除成功"}
            else:
                return {"success": False, "error": "文件删除失败或无权删除"}
            
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return {"error": str(e), "success": False}
    
    async def read_file_content(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """读取文件内容"""
        try:
            document_id = params["document_id"]
            max_length = params.get("max_length", 5000)
            
            # 获取用户ID
            user_id = context.user_id if context else None
            if not user_id:
                return {"error": "需要用户ID进行文件内容读取"}
            
            # 获取文档信息
            document_info = await enhanced_document_service.get_document_info(
                document_id=document_id,
                user_id=int(user_id)
            )
            
            if not document_info:
                return {"error": "文档不存在或无权访问"}
            
            # 这里应该从数据库获取文档内容，暂时返回模拟内容
            content = "这是文档的内容示例。在实际实现中，这里会返回文档的实际解析内容。"
            
            # 限制内容长度
            if len(content) > max_length:
                content = content[:max_length] + "..."
                truncated = True
            else:
                truncated = False
            
            return {
                "document_id": document_id,
                "content": content,
                "content_length": len(content),
                "truncated": truncated,
                "max_length": max_length
            }
            
        except Exception as e:
            logger.error(f"读取文件内容失败: {e}")
            return {"error": str(e)}
    
    async def analyze_file(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """分析文件"""
        try:
            document_id = params["document_id"]
            analysis_type = params.get("analysis_type", "summary")
            
            # 获取用户ID
            user_id = context.user_id if context else None
            if not user_id:
                return {"error": "需要用户ID进行文件分析"}
            
            # 获取文档信息
            document_info = await enhanced_document_service.get_document_info(
                document_id=document_id,
                user_id=int(user_id)
            )
            
            if not document_info:
                return {"error": "文档不存在或无权访问"}
            
            # 根据分析类型返回不同的分析结果
            analysis_result = {}
            
            if analysis_type == "summary":
                analysis_result = {
                    "summary": "这是文档的摘要信息，包含了主要内容和关键点。",
                    "key_points": ["关键点1", "关键点2", "关键点3"],
                    "word_count": document_info.get("metadata", {}).get("parse_result", {}).get("word_count", 0)
                }
            elif analysis_type == "keywords":
                analysis_result = {
                    "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
                    "keyword_frequency": {
                        "关键词1": 10,
                        "关键词2": 8,
                        "关键词3": 6
                    }
                }
            elif analysis_type == "entities":
                analysis_result = {
                    "entities": {
                        "人名": ["张三", "李四"],
                        "地名": ["北京", "上海"],
                        "组织": ["公司A", "公司B"],
                        "时间": ["2024年", "1月27日"]
                    }
                }
            elif analysis_type == "structure":
                analysis_result = {
                    "structure": {
                        "chapters": 5,
                        "sections": 15,
                        "paragraphs": 120,
                        "tables": document_info.get("metadata", {}).get("parse_result", {}).get("tables_count", 0),
                        "images": document_info.get("metadata", {}).get("parse_result", {}).get("images_count", 0)
                    }
                }
            
            return {
                "document_id": document_id,
                "analysis_type": analysis_type,
                "result": analysis_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"文件分析失败: {e}")
            return {"error": str(e)}
    
    async def create_text_file(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """创建文本文件"""
        try:
            file_name = params["file_name"]
            content = params["content"]
            conversation_id = params.get("conversation_id")
            
            # 获取用户ID
            user_id = context.user_id if context else None
            if not user_id:
                return {"error": "需要用户ID进行文件创建"}
            
            # 确保文件名有正确的扩展名
            if not file_name.endswith('.txt'):
                file_name += '.txt'
            
            # 保存文件
            file_path = self.upload_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # 处理文档
            result = await enhanced_document_service.process_document(
                file_path=str(file_path),
                file_name=file_name,
                user_id=int(user_id),
                conversation_id=conversation_id,
                extract_images=False,
                extract_tables=False
            )
            
            return {
                "success": True,
                "document_id": result["document_id"],
                "file_name": file_name,
                "file_size": len(content.encode('utf-8')),
                "message": "文本文件创建成功"
            }
            
        except Exception as e:
            logger.error(f"创建文本文件失败: {e}")
            return {"error": str(e), "success": False}
    
    async def get_file_statistics(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """获取文件统计信息"""
        try:
            conversation_id = params.get("conversation_id")
            
            # 获取用户ID
            user_id = context.user_id if context else None
            if not user_id:
                return {"error": "需要用户ID进行统计查询"}
            
            # 这里应该从数据库查询真实统计数据，暂时返回模拟数据
            statistics = {
                "total_files": 15,
                "total_size": 50 * 1024 * 1024,  # 50MB
                "file_types": {
                    ".pdf": 8,
                    ".docx": 4,
                    ".txt": 2,
                    ".xlsx": 1
                },
                "status_distribution": {
                    "completed": 12,
                    "processing": 2,
                    "failed": 1
                },
                "recent_uploads": 5,
                "conversation_id": conversation_id
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"获取文件统计失败: {e}")
            return {"error": str(e)}


# 全局文件工具实例
file_tools = FileTools()
