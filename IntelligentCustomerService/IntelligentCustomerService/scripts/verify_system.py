#!/usr/bin/env python3
"""
系统验证脚本
验证智能客服系统的所有组件是否正常工作
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
import json
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemVerifier:
    """系统验证器"""
    
    def __init__(self):
        """初始化系统验证器"""
        self.verification_results = {}
        self.start_time = time.time()
    
    async def verify_python_environment(self) -> Dict[str, Any]:
        """验证Python环境"""
        logger.info("验证Python环境...")
        
        result = {
            "status": "success",
            "details": {},
            "errors": []
        }
        
        try:
            # Python版本
            python_version = sys.version_info
            result["details"]["python_version"] = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
            
            if python_version < (3, 8):
                result["status"] = "error"
                result["errors"].append(f"Python版本过低: {python_version}, 需要3.8+")
            
            # 检查关键包
            required_packages = {
                "fastapi": "Web框架",
                "uvicorn": "ASGI服务器",
                "tortoise": "ORM框架",
                "autogen_agentchat": "AutoGen智能体框架",
                "pymilvus": "Milvus向量数据库",
                "neo4j": "Neo4j图数据库",
                "redis": "Redis缓存",
                "transformers": "Transformers模型库",
                "torch": "PyTorch深度学习框架",
                "PIL": "图像处理库",
                "modelscope": "ModelScope模型库"
            }
            
            installed_packages = {}
            missing_packages = []
            
            for package, description in required_packages.items():
                try:
                    module = __import__(package)
                    version = getattr(module, '__version__', 'unknown')
                    installed_packages[package] = {
                        "version": version,
                        "description": description,
                        "status": "installed"
                    }
                except ImportError:
                    missing_packages.append(package)
                    installed_packages[package] = {
                        "version": None,
                        "description": description,
                        "status": "missing"
                    }
            
            result["details"]["packages"] = installed_packages
            
            if missing_packages:
                result["status"] = "warning"
                result["errors"].extend([f"缺少包: {pkg}" for pkg in missing_packages])
            
            logger.info(f"✅ Python环境验证完成: {result['status']}")
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"Python环境验证失败: {str(e)}")
            logger.error(f"❌ Python环境验证失败: {str(e)}")
        
        return result
    
    async def verify_models(self) -> Dict[str, Any]:
        """验证模型文件"""
        logger.info("验证模型文件...")
        
        result = {
            "status": "success",
            "details": {},
            "errors": []
        }
        
        try:
            models_dir = Path("./models")
            
            expected_models = {
                "Qwen--Qwen3-0.6B": "嵌入模型",
                "Qwen--Qwen3-Reranker-0.6B": "重排模型"
            }
            
            model_status = {}
            
            for model_name, description in expected_models.items():
                model_path = models_dir / model_name
                
                if model_path.exists():
                    # 检查关键文件
                    required_files = ["config.json", "pytorch_model.bin", "tokenizer.json"]
                    missing_files = []
                    
                    for file_name in required_files:
                        if not (model_path / file_name).exists():
                            missing_files.append(file_name)
                    
                    if missing_files:
                        model_status[model_name] = {
                            "status": "incomplete",
                            "description": description,
                            "missing_files": missing_files
                        }
                        result["errors"].append(f"模型 {model_name} 文件不完整: {missing_files}")
                    else:
                        # 计算模型大小
                        total_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
                        model_status[model_name] = {
                            "status": "complete",
                            "description": description,
                            "size_mb": round(total_size / 1024 / 1024, 1)
                        }
                else:
                    model_status[model_name] = {
                        "status": "missing",
                        "description": description
                    }
                    result["errors"].append(f"模型 {model_name} 不存在")
            
            result["details"]["models"] = model_status
            
            # 检查是否有模型缺失
            missing_models = [name for name, status in model_status.items() if status["status"] == "missing"]
            incomplete_models = [name for name, status in model_status.items() if status["status"] == "incomplete"]
            
            if missing_models or incomplete_models:
                result["status"] = "warning" if not missing_models else "error"
            
            logger.info(f"✅ 模型文件验证完成: {result['status']}")
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"模型验证失败: {str(e)}")
            logger.error(f"❌ 模型验证失败: {str(e)}")
        
        return result
    
    async def verify_databases(self) -> Dict[str, Any]:
        """验证数据库连接"""
        logger.info("验证数据库连接...")
        
        result = {
            "status": "success",
            "details": {},
            "errors": []
        }
        
        # 验证MySQL
        try:
            import aiomysql
            # 这里应该从配置文件读取
            connection = await aiomysql.connect(
                host="localhost",
                port=3306,
                user="root",
                password="root_password",
                db="intelligent_customer_service"
            )
            await connection.ensure_closed()
            result["details"]["mysql"] = {"status": "connected", "type": "关系数据库"}
            logger.info("✅ MySQL连接成功")
        except Exception as e:
            result["details"]["mysql"] = {"status": "error", "error": str(e)}
            result["errors"].append(f"MySQL连接失败: {str(e)}")
            result["status"] = "warning"
        
        # 验证Milvus
        try:
            from pymilvus import connections, utility
            connections.connect(alias="verify", host="localhost", port=19530)
            collections = utility.list_collections()
            connections.disconnect("verify")
            result["details"]["milvus"] = {
                "status": "connected", 
                "type": "向量数据库",
                "collections": len(collections)
            }
            logger.info(f"✅ Milvus连接成功，集合数量: {len(collections)}")
        except Exception as e:
            result["details"]["milvus"] = {"status": "error", "error": str(e)}
            result["errors"].append(f"Milvus连接失败: {str(e)}")
            result["status"] = "warning"
        
        # 验证Neo4j
        try:
            from neo4j import AsyncGraphDatabase
            driver = AsyncGraphDatabase.driver(
                "bolt://localhost:7687",
                auth=("neo4j", "neo4j_password")
            )
            async with driver.session() as session:
                result_neo4j = await session.run("RETURN 1 as test")
                await result_neo4j.single()
            await driver.close()
            result["details"]["neo4j"] = {"status": "connected", "type": "图数据库"}
            logger.info("✅ Neo4j连接成功")
        except Exception as e:
            result["details"]["neo4j"] = {"status": "error", "error": str(e)}
            result["errors"].append(f"Neo4j连接失败: {str(e)}")
            result["status"] = "warning"
        
        # 验证Redis
        try:
            import redis.asyncio as redis
            redis_client = redis.Redis(host="localhost", port=6379, db=0)
            await redis_client.ping()
            await redis_client.close()
            result["details"]["redis"] = {"status": "connected", "type": "缓存数据库"}
            logger.info("✅ Redis连接成功")
        except Exception as e:
            result["details"]["redis"] = {"status": "error", "error": str(e)}
            result["errors"].append(f"Redis连接失败: {str(e)}")
            result["status"] = "warning"
        
        return result
    
    async def verify_agents(self) -> Dict[str, Any]:
        """验证智能体系统"""
        logger.info("验证智能体系统...")
        
        result = {
            "status": "success",
            "details": {},
            "errors": []
        }
        
        try:
            # 导入智能体模块
            from app.agents import AgentManager
            from app.core.model_manager import model_manager
            
            # 创建智能体管理器
            agent_manager = AgentManager()
            
            # 初始化智能体
            await agent_manager.initialize()
            
            # 检查智能体状态
            agent_status = await agent_manager.get_agent_status()
            result["details"]["agents"] = agent_status
            
            # 测试简单对话
            test_message = "你好，这是一个测试消息"
            response = await agent_manager.process_message(test_message)
            
            result["details"]["test_response"] = {
                "input": test_message,
                "output": response[:100] + "..." if len(response) > 100 else response,
                "length": len(response)
            }
            
            logger.info("✅ 智能体系统验证成功")
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"智能体系统验证失败: {str(e)}")
            logger.error(f"❌ 智能体系统验证失败: {str(e)}")
        
        return result
    
    async def verify_api_server(self) -> Dict[str, Any]:
        """验证API服务器"""
        logger.info("验证API服务器...")
        
        result = {
            "status": "success",
            "details": {},
            "errors": []
        }
        
        try:
            import httpx
            
            # 测试健康检查接口
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get("http://localhost:9999/api/v1/health", timeout=10)
                    if response.status_code == 200:
                        result["details"]["health_check"] = {
                            "status": "success",
                            "response_time": response.elapsed.total_seconds(),
                            "data": response.json()
                        }
                    else:
                        result["status"] = "warning"
                        result["errors"].append(f"健康检查返回状态码: {response.status_code}")
                except httpx.ConnectError:
                    result["status"] = "warning"
                    result["errors"].append("API服务器未启动或无法连接")
                except Exception as e:
                    result["status"] = "error"
                    result["errors"].append(f"API测试失败: {str(e)}")
            
            logger.info(f"✅ API服务器验证完成: {result['status']}")
            
        except ImportError:
            result["status"] = "warning"
            result["errors"].append("httpx未安装，无法测试API服务器")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"API服务器验证失败: {str(e)}")
        
        return result
    
    async def verify_system_resources(self) -> Dict[str, Any]:
        """验证系统资源"""
        logger.info("验证系统资源...")
        
        result = {
            "status": "success",
            "details": {},
            "errors": []
        }
        
        try:
            import psutil
            import shutil
            
            # CPU信息
            cpu_count = psutil.cpu_count()
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # 内存信息
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            memory_usage = memory.percent
            
            # 磁盘信息
            disk_usage = shutil.disk_usage(".")
            disk_free_gb = disk_usage.free / (1024**3)
            disk_total_gb = disk_usage.total / (1024**3)
            
            result["details"] = {
                "cpu": {
                    "cores": cpu_count,
                    "usage_percent": cpu_usage
                },
                "memory": {
                    "total_gb": round(memory_gb, 1),
                    "usage_percent": memory_usage,
                    "available_gb": round(memory.available / (1024**3), 1)
                },
                "disk": {
                    "total_gb": round(disk_total_gb, 1),
                    "free_gb": round(disk_free_gb, 1),
                    "usage_percent": round((disk_usage.used / disk_usage.total) * 100, 1)
                }
            }
            
            # 检查资源是否充足
            warnings = []
            if memory_gb < 8:
                warnings.append(f"内存不足: {memory_gb:.1f}GB，建议至少8GB")
            if disk_free_gb < 10:
                warnings.append(f"磁盘空间不足: {disk_free_gb:.1f}GB，建议至少10GB")
            if cpu_count < 4:
                warnings.append(f"CPU核心数较少: {cpu_count}，建议至少4核")
            
            if warnings:
                result["status"] = "warning"
                result["errors"].extend(warnings)
            
            logger.info(f"✅ 系统资源验证完成: {result['status']}")
            
        except ImportError:
            result["status"] = "warning"
            result["errors"].append("psutil未安装，无法检查系统资源")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"系统资源验证失败: {str(e)}")
        
        return result
    
    async def run_full_verification(self) -> Dict[str, Any]:
        """运行完整的系统验证"""
        logger.info("开始完整系统验证...")
        
        verification_tasks = [
            ("python_environment", self.verify_python_environment()),
            ("models", self.verify_models()),
            ("databases", self.verify_databases()),
            ("agents", self.verify_agents()),
            ("api_server", self.verify_api_server()),
            ("system_resources", self.verify_system_resources())
        ]
        
        results = {}
        overall_status = "success"
        
        for task_name, task_coro in verification_tasks:
            try:
                logger.info(f"执行验证任务: {task_name}")
                task_result = await task_coro
                results[task_name] = task_result
                
                if task_result["status"] == "error":
                    overall_status = "error"
                elif task_result["status"] == "warning" and overall_status != "error":
                    overall_status = "warning"
                    
            except Exception as e:
                logger.error(f"验证任务 {task_name} 执行失败: {str(e)}")
                results[task_name] = {
                    "status": "error",
                    "errors": [f"任务执行失败: {str(e)}"]
                }
                overall_status = "error"
        
        # 计算总体结果
        total_time = time.time() - self.start_time
        
        summary = {
            "overall_status": overall_status,
            "total_time_seconds": round(total_time, 2),
            "verification_results": results,
            "summary": self._generate_summary(results)
        }
        
        return summary
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成验证摘要"""
        total_tasks = len(results)
        success_tasks = sum(1 for r in results.values() if r["status"] == "success")
        warning_tasks = sum(1 for r in results.values() if r["status"] == "warning")
        error_tasks = sum(1 for r in results.values() if r["status"] == "error")
        
        all_errors = []
        for task_name, task_result in results.items():
            if task_result.get("errors"):
                all_errors.extend([f"{task_name}: {error}" for error in task_result["errors"]])
        
        return {
            "total_tasks": total_tasks,
            "success_tasks": success_tasks,
            "warning_tasks": warning_tasks,
            "error_tasks": error_tasks,
            "success_rate": round(success_tasks / total_tasks * 100, 1),
            "all_errors": all_errors
        }


def print_verification_report(results: Dict[str, Any]):
    """打印验证报告"""
    print("\n" + "="*80)
    print("智能客服系统验证报告")
    print("="*80)
    
    overall_status = results["overall_status"]
    status_icon = "✅" if overall_status == "success" else "⚠️" if overall_status == "warning" else "❌"
    
    print(f"\n总体状态: {status_icon} {overall_status.upper()}")
    print(f"验证时间: {results['total_time_seconds']} 秒")
    
    summary = results["summary"]
    print(f"\n任务统计:")
    print(f"  总任务数: {summary['total_tasks']}")
    print(f"  成功: {summary['success_tasks']}")
    print(f"  警告: {summary['warning_tasks']}")
    print(f"  错误: {summary['error_tasks']}")
    print(f"  成功率: {summary['success_rate']}%")
    
    print(f"\n详细结果:")
    for task_name, task_result in results["verification_results"].items():
        status = task_result["status"]
        status_icon = "✅" if status == "success" else "⚠️" if status == "warning" else "❌"
        print(f"  {status_icon} {task_name}: {status}")
        
        if task_result.get("errors"):
            for error in task_result["errors"]:
                print(f"    - {error}")
    
    if summary["all_errors"]:
        print(f"\n所有错误和警告:")
        for error in summary["all_errors"]:
            print(f"  - {error}")
    
    print("\n" + "="*80)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="验证智能客服系统")
    parser.add_argument(
        "--task",
        choices=["python", "models", "databases", "agents", "api", "resources", "all"],
        default="all",
        help="要验证的任务类型 (默认: all)"
    )
    parser.add_argument(
        "--output",
        help="输出结果到JSON文件"
    )
    
    args = parser.parse_args()
    
    verifier = SystemVerifier()
    
    try:
        if args.task == "all":
            results = await verifier.run_full_verification()
        else:
            # 运行单个验证任务
            task_map = {
                "python": verifier.verify_python_environment,
                "models": verifier.verify_models,
                "databases": verifier.verify_databases,
                "agents": verifier.verify_agents,
                "api": verifier.verify_api_server,
                "resources": verifier.verify_system_resources
            }
            
            task_result = await task_map[args.task]()
            results = {
                "overall_status": task_result["status"],
                "total_time_seconds": time.time() - verifier.start_time,
                "verification_results": {args.task: task_result},
                "summary": verifier._generate_summary({args.task: task_result})
            }
        
        # 打印报告
        print_verification_report(results)
        
        # 保存到文件
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n验证结果已保存到: {args.output}")
        
        # 设置退出码
        if results["overall_status"] == "error":
            sys.exit(1)
        elif results["overall_status"] == "warning":
            sys.exit(2)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("用户中断验证")
        sys.exit(1)
    except Exception as e:
        logger.error(f"验证过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
