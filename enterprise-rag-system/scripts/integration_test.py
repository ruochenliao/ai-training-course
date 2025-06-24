#!/usr/bin/env python3
"""
企业RAG系统集成测试脚本
测试系统各个组件的集成情况和功能完整性
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

import aiohttp
import requests
from colorama import Fore, Style, init

# 初始化colorama
init(autoreset=True)

class IntegrationTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.test_results = []
        self.session = None
        
    async def setup(self):
        """设置测试环境"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """清理测试环境"""
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, message: str = "", details: Any = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        # 控制台输出
        color = Fore.GREEN if status == "PASS" else Fore.RED if status == "FAIL" else Fore.YELLOW
        print(f"{color}[{status}] {test_name}: {message}")
        if details and isinstance(details, dict):
            for key, value in details.items():
                print(f"  {key}: {value}")
    
    async def test_health_check(self):
        """测试系统健康检查"""
        try:
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Health Check", "PASS", "系统健康检查通过", data)
                    return True
                else:
                    self.log_test("Health Check", "FAIL", f"健康检查失败，状态码: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Health Check", "FAIL", f"健康检查异常: {str(e)}")
            return False
    
    async def test_knowledge_base_crud(self):
        """测试知识库CRUD操作"""
        try:
            # 创建知识库
            kb_data = {
                "name": "测试知识库",
                "description": "集成测试用知识库",
                "embedding_model": "text-embedding-ada-002"
            }
            
            async with self.session.post(f"{self.api_base}/knowledge-bases/", json=kb_data) as response:
                if response.status == 200:
                    kb = await response.json()
                    kb_id = kb["id"]
                    self.log_test("Knowledge Base Create", "PASS", f"知识库创建成功，ID: {kb_id}")
                    
                    # 获取知识库列表
                    async with self.session.get(f"{self.api_base}/knowledge-bases/") as list_response:
                        if list_response.status == 200:
                            kb_list = await list_response.json()
                            self.log_test("Knowledge Base List", "PASS", f"获取知识库列表成功，共 {len(kb_list)} 个")
                        else:
                            self.log_test("Knowledge Base List", "FAIL", f"获取知识库列表失败")
                    
                    # 更新知识库
                    update_data = {"description": "更新后的描述"}
                    async with self.session.put(f"{self.api_base}/knowledge-bases/{kb_id}", json=update_data) as update_response:
                        if update_response.status == 200:
                            self.log_test("Knowledge Base Update", "PASS", "知识库更新成功")
                        else:
                            self.log_test("Knowledge Base Update", "FAIL", "知识库更新失败")
                    
                    # 删除知识库
                    async with self.session.delete(f"{self.api_base}/knowledge-bases/{kb_id}") as delete_response:
                        if delete_response.status == 200:
                            self.log_test("Knowledge Base Delete", "PASS", "知识库删除成功")
                        else:
                            self.log_test("Knowledge Base Delete", "FAIL", "知识库删除失败")
                    
                    return True
                else:
                    self.log_test("Knowledge Base Create", "FAIL", f"知识库创建失败，状态码: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Knowledge Base CRUD", "FAIL", f"知识库CRUD测试异常: {str(e)}")
            return False
    
    async def test_document_upload_and_processing(self):
        """测试文档上传和处理"""
        try:
            # 首先创建一个测试知识库
            kb_data = {
                "name": "文档测试知识库",
                "description": "用于测试文档上传的知识库",
                "embedding_model": "text-embedding-ada-002"
            }
            
            async with self.session.post(f"{self.api_base}/knowledge-bases/", json=kb_data) as response:
                if response.status != 200:
                    self.log_test("Document Test Setup", "FAIL", "创建测试知识库失败")
                    return False
                
                kb = await response.json()
                kb_id = kb["id"]
                
                # 创建测试文档内容
                test_content = """
                这是一个测试文档。
                
                ## 产品介绍
                我们的产品是一个企业级RAG系统，具有以下特点：
                1. 支持多种文档格式
                2. 智能文档分块
                3. 向量化存储
                4. 语义搜索
                
                ## 技术架构
                系统采用微服务架构，包含以下组件：
                - 文档处理服务
                - 向量数据库
                - 图数据库
                - AI模型服务
                """
                
                # 模拟文件上传
                files = {
                    'file': ('test_document.txt', test_content, 'text/plain')
                }
                data = {
                    'knowledge_base_id': kb_id,
                    'title': '测试文档'
                }
                
                # 使用requests进行文件上传（aiohttp的文件上传比较复杂）
                upload_response = requests.post(
                    f"{self.api_base}/documents/upload",
                    files=files,
                    data=data
                )
                
                if upload_response.status_code == 200:
                    doc_data = upload_response.json()
                    doc_id = doc_data["id"]
                    self.log_test("Document Upload", "PASS", f"文档上传成功，ID: {doc_id}")
                    
                    # 等待文档处理完成
                    max_wait = 30  # 最多等待30秒
                    wait_time = 0
                    processing_complete = False
                    
                    while wait_time < max_wait:
                        async with self.session.get(f"{self.api_base}/documents/{doc_id}") as status_response:
                            if status_response.status == 200:
                                doc_status = await status_response.json()
                                if doc_status["status"] == "processed":
                                    processing_complete = True
                                    self.log_test("Document Processing", "PASS", "文档处理完成")
                                    break
                                elif doc_status["status"] == "failed":
                                    self.log_test("Document Processing", "FAIL", "文档处理失败")
                                    break
                        
                        await asyncio.sleep(2)
                        wait_time += 2
                    
                    if not processing_complete and wait_time >= max_wait:
                        self.log_test("Document Processing", "FAIL", "文档处理超时")
                    
                    # 清理：删除测试文档和知识库
                    async with self.session.delete(f"{self.api_base}/documents/{doc_id}"):
                        pass
                    async with self.session.delete(f"{self.api_base}/knowledge-bases/{kb_id}"):
                        pass
                    
                    return processing_complete
                else:
                    self.log_test("Document Upload", "FAIL", f"文档上传失败，状态码: {upload_response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_test("Document Upload and Processing", "FAIL", f"文档上传处理测试异常: {str(e)}")
            return False
    
    async def test_chat_functionality(self):
        """测试聊天功能"""
        try:
            # 创建测试知识库和文档（简化版）
            kb_data = {
                "name": "聊天测试知识库",
                "description": "用于测试聊天功能的知识库",
                "embedding_model": "text-embedding-ada-002"
            }
            
            async with self.session.post(f"{self.api_base}/knowledge-bases/", json=kb_data) as response:
                if response.status != 200:
                    self.log_test("Chat Test Setup", "FAIL", "创建测试知识库失败")
                    return False
                
                kb = await response.json()
                kb_id = kb["id"]
                
                # 测试聊天
                chat_data = {
                    "message": "你好，请介绍一下这个系统",
                    "knowledge_base_ids": [kb_id],
                    "stream": False
                }
                
                async with self.session.post(f"{self.api_base}/chat/", json=chat_data) as chat_response:
                    if chat_response.status == 200:
                        chat_result = await chat_response.json()
                        if "message" in chat_result and chat_result["message"]:
                            self.log_test("Chat Functionality", "PASS", "聊天功能正常", {
                                "response_length": len(chat_result["message"]),
                                "conversation_id": chat_result.get("conversation_id")
                            })
                            
                            # 清理
                            async with self.session.delete(f"{self.api_base}/knowledge-bases/{kb_id}"):
                                pass
                            
                            return True
                        else:
                            self.log_test("Chat Functionality", "FAIL", "聊天响应为空")
                            return False
                    else:
                        self.log_test("Chat Functionality", "FAIL", f"聊天请求失败，状态码: {chat_response.status}")
                        return False
                        
        except Exception as e:
            self.log_test("Chat Functionality", "FAIL", f"聊天功能测试异常: {str(e)}")
            return False
    
    async def test_search_functionality(self):
        """测试搜索功能"""
        try:
            search_data = {
                "query": "系统架构",
                "knowledge_base_ids": [],
                "top_k": 5
            }
            
            async with self.session.post(f"{self.api_base}/search/", json=search_data) as response:
                if response.status == 200:
                    search_results = await response.json()
                    self.log_test("Search Functionality", "PASS", f"搜索功能正常，返回 {len(search_results.get('results', []))} 个结果")
                    return True
                else:
                    self.log_test("Search Functionality", "FAIL", f"搜索请求失败，状态码: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Search Functionality", "FAIL", f"搜索功能测试异常: {str(e)}")
            return False
    
    async def test_user_management(self):
        """测试用户管理功能"""
        try:
            # 获取用户列表
            async with self.session.get(f"{self.api_base}/users/") as response:
                if response.status == 200:
                    users = await response.json()
                    self.log_test("User Management", "PASS", f"用户管理功能正常，共 {len(users)} 个用户")
                    return True
                else:
                    self.log_test("User Management", "FAIL", f"获取用户列表失败，状态码: {response.status}")
                    return False
        except Exception as e:
            self.log_test("User Management", "FAIL", f"用户管理测试异常: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """运行所有集成测试"""
        print(f"{Fore.CYAN}开始运行企业RAG系统集成测试...")
        print(f"{Fore.CYAN}测试目标: {self.base_url}")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # 运行各项测试
            tests = [
                self.test_health_check(),
                self.test_knowledge_base_crud(),
                self.test_document_upload_and_processing(),
                self.test_chat_functionality(),
                self.test_search_functionality(),
                self.test_user_management()
            ]
            
            results = await asyncio.gather(*tests, return_exceptions=True)
            
            # 统计测试结果
            passed = sum(1 for result in self.test_results if result["status"] == "PASS")
            failed = sum(1 for result in self.test_results if result["status"] == "FAIL")
            total = len(self.test_results)
            
            print("=" * 60)
            print(f"{Fore.CYAN}测试完成！")
            print(f"{Fore.GREEN}通过: {passed}")
            print(f"{Fore.RED}失败: {failed}")
            print(f"{Fore.YELLOW}总计: {total}")
            print(f"{Fore.CYAN}成功率: {(passed/total*100):.1f}%")
            
            # 保存测试报告
            report = {
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "success_rate": passed/total*100
                },
                "tests": self.test_results,
                "timestamp": time.time()
            }
            
            report_file = Path("test_report.json")
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"{Fore.CYAN}测试报告已保存到: {report_file}")
            
            return passed == total
            
        finally:
            await self.cleanup()

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="企业RAG系统集成测试")
    parser.add_argument("--url", default="http://localhost:8000", help="系统URL")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时时间")
    
    args = parser.parse_args()
    
    tester = IntegrationTester(args.url)
    success = await tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
