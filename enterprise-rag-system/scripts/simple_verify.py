#!/usr/bin/env python3
"""
简化的第一阶段验证脚本
验证基础架构完善的成果（不依赖外部模块）
"""

import sys
import os
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent.parent


class SimpleVerifier:
    """简化验证器"""
    
    def __init__(self):
        self.results = []
        self.errors = []
    
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f": {message}"
        
        self.results.append(result)
        print(result)
        
        if not success:
            self.errors.append(f"{test_name}: {message}")
    
    def verify_project_structure(self):
        """验证项目结构"""
        print("\n📁 验证项目结构...")
        
        # 检查关键文件和目录
        key_paths = [
            "backend/app/services/autogen_agent_service.py",
            "backend/app/services/qwen_model_service.py", 
            "backend/app/core/config.py",
            "backend/requirements.txt",
            "frontend/admin-app/package.json",
            "frontend/user-app/package.json",
            "docs/architecture.md",
            "docs/development-plan.md"
        ]
        
        for path in key_paths:
            full_path = project_root / path
            if full_path.exists():
                self.log_result(f"文件存在: {path}", True)
            else:
                self.log_result(f"文件存在: {path}", False, "文件不存在")
    
    def verify_config_file(self):
        """验证配置文件内容"""
        print("\n🔧 验证配置文件...")
        
        try:
            config_file = project_root / "backend" / "app" / "core" / "config.py"
            if config_file.exists():
                content = config_file.read_text(encoding='utf-8')
                
                # 检查关键配置
                checks = [
                    ("项目名称", "企业级Agent+RAG知识库系统"),
                    ("DeepSeek模型", "deepseek-chat"),
                    ("通义千问VL模型", "qwen-vl-max-latest"),
                    ("通义千问嵌入模型", "Qwen/Qwen3-8B"),
                    ("通义千问重排模型", "Qwen/Qwen3-Reranker-8B"),
                    ("AutoGen配置", "AUTOGEN_CONFIG_LIST"),
                    ("Milvus配置", "MILVUS_HOST"),
                    ("Neo4j配置", "NEO4J_URI")
                ]
                
                for check_name, check_value in checks:
                    if check_value in content:
                        self.log_result(f"配置项: {check_name}", True)
                    else:
                        self.log_result(f"配置项: {check_name}", False, f"未找到 {check_value}")
            else:
                self.log_result("config.py文件", False, "文件不存在")
                
        except Exception as e:
            self.log_result("配置文件验证", False, str(e))
    
    def verify_dependencies(self):
        """验证依赖配置"""
        print("\n📦 验证依赖配置...")
        
        try:
            req_file = project_root / "backend" / "requirements.txt"
            if req_file.exists():
                content = req_file.read_text(encoding='utf-8')
                
                # 检查关键依赖
                key_deps = [
                    ("AutoGen框架", "pyautogen"),
                    ("AutoGen聊天", "autogen-agentchat"),
                    ("魔塔社区", "modelscope"),
                    ("通义千问API", "dashscope"),
                    ("Marker文档解析", "marker-pdf"),
                    ("Milvus向量库", "pymilvus"),
                    ("Neo4j图库", "neo4j"),
                    ("FastAPI框架", "fastapi"),
                    ("Tortoise ORM", "tortoise-orm")
                ]
                
                for dep_name, dep_package in key_deps:
                    if dep_package in content:
                        self.log_result(f"依赖: {dep_name}", True)
                    else:
                        self.log_result(f"依赖: {dep_name}", False, f"未找到 {dep_package}")
            else:
                self.log_result("requirements.txt文件", False, "文件不存在")
                
        except Exception as e:
            self.log_result("依赖配置验证", False, str(e))
    
    def verify_autogen_service(self):
        """验证AutoGen服务文件"""
        print("\n🤝 验证AutoGen智能体服务...")
        
        try:
            service_file = project_root / "backend" / "app" / "services" / "autogen_agent_service.py"
            if service_file.exists():
                content = service_file.read_text(encoding='utf-8')
                
                # 检查关键类和方法
                checks = [
                    ("语义检索智能体", "SemanticSearchAgent"),
                    ("图谱检索智能体", "GraphSearchAgent"),
                    ("混合检索智能体", "HybridSearchAgent"),
                    ("答案生成智能体", "AnswerGenerationAgent"),
                    ("AutoGen服务主类", "AutoGenAgentService"),
                    ("查询处理方法", "process_query"),
                    ("结果融合方法", "_deduplicate_results"),
                    ("置信度计算", "_calculate_confidence")
                ]
                
                for check_name, check_value in checks:
                    if check_value in content:
                        self.log_result(f"AutoGen组件: {check_name}", True)
                    else:
                        self.log_result(f"AutoGen组件: {check_name}", False, f"未找到 {check_value}")
            else:
                self.log_result("AutoGen服务文件", False, "文件不存在")
                
        except Exception as e:
            self.log_result("AutoGen服务验证", False, str(e))
    
    def verify_qwen_service(self):
        """验证通义千问服务文件"""
        print("\n🤖 验证通义千问模型服务...")
        
        try:
            service_file = project_root / "backend" / "app" / "services" / "qwen_model_service.py"
            if service_file.exists():
                content = service_file.read_text(encoding='utf-8')
                
                # 检查关键类和方法
                checks = [
                    ("嵌入服务类", "QwenEmbeddingService"),
                    ("重排服务类", "QwenRerankerService"),
                    ("模型管理器", "QwenModelManager"),
                    ("模型下载方法", "_download_model"),
                    ("本地模型加载", "_load_local_model"),
                    ("文本嵌入方法", "embed_texts"),
                    ("文档重排方法", "rerank"),
                    ("魔塔社区集成", "snapshot_download")
                ]
                
                for check_name, check_value in checks:
                    if check_value in content:
                        self.log_result(f"通义千问组件: {check_name}", True)
                    else:
                        self.log_result(f"通义千问组件: {check_name}", False, f"未找到 {check_value}")
            else:
                self.log_result("通义千问服务文件", False, "文件不存在")
                
        except Exception as e:
            self.log_result("通义千问服务验证", False, str(e))
    
    def verify_frontend_config(self):
        """验证前端配置"""
        print("\n🎨 验证前端配置...")
        
        # 检查管理端配置
        try:
            admin_config = project_root / "frontend" / "admin-app" / "package.json"
            if admin_config.exists():
                content = admin_config.read_text(encoding='utf-8')
                
                admin_checks = [
                    ("Nuxt.js框架", "nuxt"),
                    ("Vue3框架", "vue"),
                    ("Naive UI", "naive-ui"),
                    ("TailwindCSS", "tailwindcss"),
                    ("ECharts图表", "echarts"),
                    ("Socket.io", "socket.io-client")
                ]
                
                for check_name, check_value in admin_checks:
                    if check_value in content:
                        self.log_result(f"管理端依赖: {check_name}", True)
                    else:
                        self.log_result(f"管理端依赖: {check_name}", False, f"未找到 {check_value}")
            else:
                self.log_result("管理端配置文件", False, "文件不存在")
        except Exception as e:
            self.log_result("管理端配置验证", False, str(e))
        
        # 检查用户端配置
        try:
            user_config = project_root / "frontend" / "user-app" / "package.json"
            if user_config.exists():
                content = user_config.read_text(encoding='utf-8')
                
                user_checks = [
                    ("Next.js框架", "next"),
                    ("React框架", "react"),
                    ("Ant Design", "antd"),
                    ("TailwindCSS", "tailwindcss"),
                    ("Axios HTTP", "axios"),
                    ("Zustand状态", "zustand")
                ]
                
                for check_name, check_value in user_checks:
                    if check_value in content:
                        self.log_result(f"用户端依赖: {check_name}", True)
                    else:
                        self.log_result(f"用户端依赖: {check_name}", False, f"未找到 {check_value}")
            else:
                self.log_result("用户端配置文件", False, "文件不存在")
        except Exception as e:
            self.log_result("用户端配置验证", False, str(e))
    
    def verify_documentation(self):
        """验证文档"""
        print("\n📚 验证文档...")
        
        # 检查架构文档
        try:
            arch_doc = project_root / "docs" / "architecture.md"
            if arch_doc.exists():
                content = arch_doc.read_text(encoding='utf-8')
                
                doc_checks = [
                    ("系统架构", "系统架构"),
                    ("技术栈", "技术栈"),
                    ("AutoGen架构", "AutoGen多智能体架构"),
                    ("数据库设计", "数据库设计"),
                    ("API设计", "API设计"),
                    ("部署架构", "部署架构")
                ]
                
                for check_name, check_value in doc_checks:
                    if check_value in content:
                        self.log_result(f"架构文档: {check_name}", True)
                    else:
                        self.log_result(f"架构文档: {check_name}", False, f"未找到 {check_value}")
            else:
                self.log_result("架构文档", False, "文件不存在")
        except Exception as e:
            self.log_result("架构文档验证", False, str(e))
        
        # 检查开发计划
        try:
            plan_doc = project_root / "docs" / "development-plan.md"
            if plan_doc.exists():
                content = plan_doc.read_text(encoding='utf-8')
                
                plan_checks = [
                    ("第一阶段", "第一阶段"),
                    ("第二阶段", "第二阶段"),
                    ("第三阶段", "第三阶段"),
                    ("里程碑", "里程碑"),
                    ("风险控制", "风险控制"),
                    ("质量保证", "质量保证")
                ]
                
                for check_name, check_value in plan_checks:
                    if check_value in content:
                        self.log_result(f"开发计划: {check_name}", True)
                    else:
                        self.log_result(f"开发计划: {check_name}", False, f"未找到 {check_value}")
            else:
                self.log_result("开发计划文档", False, "文件不存在")
        except Exception as e:
            self.log_result("开发计划验证", False, str(e))
    
    def run_all_verifications(self):
        """运行所有验证"""
        print("🚀 开始第一阶段验证...")
        print("=" * 60)
        
        self.verify_project_structure()
        self.verify_config_file()
        self.verify_dependencies()
        self.verify_autogen_service()
        self.verify_qwen_service()
        self.verify_frontend_config()
        self.verify_documentation()
        
        print("\n" + "=" * 60)
        print("📊 验证结果汇总:")
        print("=" * 60)
        
        for result in self.results:
            print(result)
        
        print(f"\n总计: {len(self.results)} 项测试")
        passed = len([r for r in self.results if "✅" in r])
        failed = len([r for r in self.results if "❌" in r])
        
        print(f"通过: {passed} 项")
        print(f"失败: {failed} 项")
        
        if failed == 0:
            print("\n🎉 第一阶段验证全部通过！可以开始第二阶段开发。")
            return True
        else:
            print(f"\n⚠️  第一阶段验证发现 {failed} 个问题，需要修复后再继续。")
            if self.errors:
                print("\n错误详情:")
                for error in self.errors:
                    print(f"  - {error}")
            return False


def main():
    """主函数"""
    verifier = SimpleVerifier()
    success = verifier.run_all_verifications()
    
    if success:
        print("\n✨ 第一阶段基础架构完善已完成！")
        print("\n📋 已完成的工作:")
        print("  - ✅ 项目结构优化和依赖更新")
        print("  - ✅ AutoGen多智能体框架集成")
        print("  - ✅ 通义千问模型服务开发")
        print("  - ✅ 嵌入和重排服务优化")
        print("  - ✅ 系统架构设计文档")
        print("  - ✅ 分阶段开发计划")
        
        print("\n🎯 下一步工作:")
        print("  - 🔄 开始第二阶段：核心服务开发")
        print("  - 📄 优化Marker文档解析服务")
        print("  - 🗄️ 完善Milvus向量数据库集成")
        print("  - 🕸️ 开发Neo4j知识图谱服务")
        print("  - 🧩 实现智能文档分块功能")
        
        return 0
    else:
        print("\n🔧 请先修复上述问题，然后重新运行验证。")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
