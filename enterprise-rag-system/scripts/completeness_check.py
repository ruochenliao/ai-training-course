#!/usr/bin/env python3
"""
企业RAG系统完整性检查脚本
检查项目的完整性和功能实现情况
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from colorama import Fore, Style, init

# 初始化colorama
init(autoreset=True)

class CompletenessChecker:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results = {
            "backend": {},
            "frontend": {},
            "deployment": {},
            "documentation": {},
            "testing": {},
            "monitoring": {}
        }
        
    def log_result(self, category: str, item: str, status: str, details: str = ""):
        """记录检查结果"""
        if category not in self.results:
            self.results[category] = {}
        
        self.results[category][item] = {
            "status": status,
            "details": details
        }
        
        # 控制台输出
        color = Fore.GREEN if status == "PASS" else Fore.RED if status == "FAIL" else Fore.YELLOW
        print(f"{color}[{status}] {category}/{item}: {details}")
    
    def check_file_exists(self, file_path: str, category: str, item: str, description: str = ""):
        """检查文件是否存在"""
        full_path = self.project_root / file_path
        if full_path.exists():
            self.log_result(category, item, "PASS", f"{description} - 文件存在")
            return True
        else:
            self.log_result(category, item, "FAIL", f"{description} - 文件不存在: {file_path}")
            return False
    
    def check_directory_exists(self, dir_path: str, category: str, item: str, description: str = ""):
        """检查目录是否存在"""
        full_path = self.project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            file_count = len(list(full_path.rglob("*")))
            self.log_result(category, item, "PASS", f"{description} - 目录存在，包含{file_count}个文件")
            return True
        else:
            self.log_result(category, item, "FAIL", f"{description} - 目录不存在: {dir_path}")
            return False
    
    def check_backend_components(self):
        """检查后端组件"""
        print(f"\n{Fore.CYAN}检查后端组件...")
        
        # 核心文件
        backend_files = [
            ("backend/app/main.py", "主应用文件"),
            ("backend/app/core/config.py", "配置文件"),
            ("backend/app/core/database.py", "数据库配置"),
            ("backend/app/models/__init__.py", "数据模型"),
            ("backend/app/schemas/__init__.py", "数据模式"),
            ("backend/app/api/v1/api.py", "API路由"),
            ("backend/requirements.txt", "依赖文件"),
            ("backend/Dockerfile", "Docker配置")
        ]
        
        for file_path, description in backend_files:
            self.check_file_exists(file_path, "backend", f"file_{Path(file_path).name}", description)
        
        # 服务目录
        service_dirs = [
            ("backend/app/services", "业务服务"),
            ("backend/app/agents", "智能体服务"),
            ("backend/app/api/v1/endpoints", "API端点"),
            ("backend/tests", "测试文件")
        ]
        
        for dir_path, description in service_dirs:
            self.check_directory_exists(dir_path, "backend", f"dir_{Path(dir_path).name}", description)
    
    def check_frontend_components(self):
        """检查前端组件"""
        print(f"\n{Fore.CYAN}检查前端组件...")
        
        # 管理后台
        admin_files = [
            ("frontend/admin-app/nuxt.config.ts", "Nuxt配置"),
            ("frontend/admin-app/package.json", "依赖配置"),
            ("frontend/admin-app/Dockerfile", "Docker配置"),
            ("frontend/admin-app/layouts/default.vue", "默认布局"),
            ("frontend/admin-app/pages/index.vue", "首页"),
            ("frontend/admin-app/pages/knowledge-bases/index.vue", "知识库管理"),
            ("frontend/admin-app/pages/documents/index.vue", "文档管理"),
            ("frontend/admin-app/pages/users/index.vue", "用户管理"),
            ("frontend/admin-app/stores/knowledgeBase.ts", "知识库状态管理"),
            ("frontend/admin-app/stores/document.ts", "文档状态管理"),
            ("frontend/admin-app/stores/user.ts", "用户状态管理"),
            ("frontend/admin-app/composables/useApi.ts", "API组合函数"),
            ("frontend/admin-app/composables/useAuth.ts", "认证组合函数"),
            ("frontend/admin-app/composables/useWebSocket.ts", "WebSocket组合函数"),
            ("frontend/admin-app/plugins/naive-ui.client.ts", "UI插件")
        ]
        
        for file_path, description in admin_files:
            self.check_file_exists(file_path, "frontend", f"admin_{Path(file_path).name}", description)
        
        # 用户前端
        user_files = [
            ("frontend/user-app/next.config.js", "Next.js配置"),
            ("frontend/user-app/package.json", "依赖配置"),
            ("frontend/user-app/Dockerfile", "Docker配置"),
            ("frontend/user-app/src/app/page.tsx", "首页"),
            ("frontend/user-app/src/app/chat/page.tsx", "聊天页面"),
            ("frontend/user-app/src/components/ChatInterface.tsx", "聊天组件"),
            ("frontend/user-app/src/utils/api.ts", "API工具"),
            ("frontend/user-app/src/hooks/useChat.ts", "聊天Hook"),
            ("frontend/user-app/src/hooks/useWebSocket.ts", "WebSocket Hook"),
            ("frontend/user-app/jest.config.js", "Jest配置"),
            ("frontend/user-app/jest.setup.js", "Jest设置")
        ]
        
        for file_path, description in user_files:
            self.check_file_exists(file_path, "frontend", f"user_{Path(file_path).name}", description)
    
    def check_deployment_components(self):
        """检查部署组件"""
        print(f"\n{Fore.CYAN}检查部署组件...")
        
        deployment_files = [
            ("docker-compose.yml", "开发环境编排"),
            ("docker-compose.prod.yml", "生产环境编排"),
            ("nginx/conf.d/default.conf", "Nginx配置"),
            (".env.example", "环境变量模板"),
            ("scripts/deploy.sh", "部署脚本"),
            ("scripts/integration_test.py", "集成测试"),
            ("scripts/simple_verify.py", "简单验证"),
            ("scripts/completeness_check.py", "完整性检查")
        ]
        
        for file_path, description in deployment_files:
            self.check_file_exists(file_path, "deployment", Path(file_path).name, description)
    
    def check_documentation(self):
        """检查文档"""
        print(f"\n{Fore.CYAN}检查文档...")
        
        doc_files = [
            ("README.md", "项目说明"),
            ("docs/architecture.md", "架构设计"),
            ("docs/development-plan.md", "开发计划"),
            ("docs/功能实现清单.md", "功能清单"),
            ("docs/文件结构分析.md", "文件结构"),
            ("docs/快速启动指南.md", "启动指南"),
            ("docs/完整启动指南.md", "完整启动指南"),
            ("docs/项目完成度总结.md", "完成度总结"),
            ("docs/项目交付报告.md", "交付报告")
        ]
        
        for file_path, description in doc_files:
            self.check_file_exists(file_path, "documentation", Path(file_path).name, description)
    
    def check_testing_components(self):
        """检查测试组件"""
        print(f"\n{Fore.CYAN}检查测试组件...")
        
        test_files = [
            ("backend/tests/test_api.py", "后端API测试"),
            ("backend/pytest.ini", "Pytest配置"),
            ("frontend/user-app/src/__tests__/components/ChatInterface.test.tsx", "前端组件测试")
        ]
        
        for file_path, description in test_files:
            self.check_file_exists(file_path, "testing", Path(file_path).name, description)
    
    def check_monitoring_components(self):
        """检查监控组件"""
        print(f"\n{Fore.CYAN}检查监控组件...")
        
        monitoring_files = [
            ("monitoring/prometheus/prometheus.yml", "Prometheus配置"),
            ("monitoring/grafana/datasources/prometheus.yml", "Grafana数据源"),
            ("monitoring/grafana/dashboards/rag-system-overview.json", "Grafana仪表板")
        ]
        
        for file_path, description in monitoring_files:
            self.check_file_exists(file_path, "monitoring", Path(file_path).name, description)
    
    def calculate_completion_rate(self):
        """计算完成率"""
        total_items = 0
        passed_items = 0
        
        for category, items in self.results.items():
            for item, result in items.items():
                total_items += 1
                if result["status"] == "PASS":
                    passed_items += 1
        
        completion_rate = (passed_items / total_items * 100) if total_items > 0 else 0
        return completion_rate, passed_items, total_items
    
    def generate_report(self):
        """生成报告"""
        completion_rate, passed_items, total_items = self.calculate_completion_rate()
        
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}完整性检查报告")
        print(f"{Fore.CYAN}{'='*60}")
        
        # 分类统计
        for category, items in self.results.items():
            category_total = len(items)
            category_passed = sum(1 for item in items.values() if item["status"] == "PASS")
            category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
            
            print(f"\n{Fore.YELLOW}{category.upper()}:")
            print(f"  通过: {category_passed}/{category_total} ({category_rate:.1f}%)")
            
            # 显示失败的项目
            failed_items = [name for name, result in items.items() if result["status"] == "FAIL"]
            if failed_items:
                print(f"  {Fore.RED}失败项目: {', '.join(failed_items)}")
        
        # 总体统计
        print(f"\n{Fore.CYAN}总体完成情况:")
        print(f"{Fore.GREEN}通过: {passed_items}")
        print(f"{Fore.RED}失败: {total_items - passed_items}")
        print(f"{Fore.YELLOW}总计: {total_items}")
        print(f"{Fore.CYAN}完成率: {completion_rate:.1f}%")
        
        # 保存详细报告
        report_file = self.project_root / "completeness_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "completion_rate": completion_rate,
                    "passed_items": passed_items,
                    "total_items": total_items
                },
                "details": self.results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n{Fore.CYAN}详细报告已保存到: {report_file}")
        
        return completion_rate >= 90  # 90%以上认为完成
    
    def run_all_checks(self):
        """运行所有检查"""
        print(f"{Fore.CYAN}开始企业RAG系统完整性检查...")
        print(f"{Fore.CYAN}项目根目录: {self.project_root.absolute()}")
        
        self.check_backend_components()
        self.check_frontend_components()
        self.check_deployment_components()
        self.check_documentation()
        self.check_testing_components()
        self.check_monitoring_components()
        
        return self.generate_report()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="企业RAG系统完整性检查")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    
    args = parser.parse_args()
    
    checker = CompletenessChecker(args.project_root)
    success = checker.run_all_checks()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
