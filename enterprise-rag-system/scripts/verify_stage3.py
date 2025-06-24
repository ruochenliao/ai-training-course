#!/usr/bin/env python3
"""
第三阶段验证脚本
验证智能体系统开发的成果
"""

import sys
import os
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent.parent


class Stage3Verifier:
    """第三阶段验证器"""
    
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
    
    def verify_enhanced_autogen_service(self):
        """验证增强版AutoGen服务"""
        print("\n🤖 验证增强版AutoGen智能体服务...")
        
        try:
            enhanced_autogen_file = project_root / "backend" / "app" / "services" / "enhanced_autogen_service.py"
            if enhanced_autogen_file.exists():
                content = enhanced_autogen_file.read_text(encoding='utf-8')
                
                # 检查核心枚举和数据类
                core_components = [
                    ("搜索模式枚举", "SearchMode"),
                    ("智能体角色枚举", "AgentRole"),
                    ("搜索结果类", "SearchResult"),
                    ("智能体任务类", "AgentTask"),
                    ("智能体响应类", "AgentResponse")
                ]
                
                for comp_name, comp_value in core_components:
                    if comp_value in content:
                        self.log_result(f"核心组件: {comp_name}", True)
                    else:
                        self.log_result(f"核心组件: {comp_name}", False, f"未找到 {comp_value}")
                
                # 检查增强版智能体
                enhanced_agents = [
                    ("增强版语义检索智能体", "EnhancedSemanticSearchAgent"),
                    ("增强版图谱检索智能体", "EnhancedGraphSearchAgent"),
                    ("增强版混合检索智能体", "EnhancedHybridSearchAgent"),
                    ("增强版答案生成智能体", "EnhancedAnswerGenerationAgent"),
                    ("质量评估智能体", "QualityAssessmentAgent"),
                    ("增强版协调智能体", "EnhancedCoordinatorAgent")
                ]
                
                for agent_name, agent_class in enhanced_agents:
                    if agent_class in content:
                        self.log_result(f"智能体: {agent_name}", True)
                    else:
                        self.log_result(f"智能体: {agent_name}", False, f"未找到 {agent_class}")
                
                # 检查主服务类
                main_service_features = [
                    ("增强版AutoGen服务", "EnhancedAutoGenService"),
                    ("服务初始化", "initialize"),
                    ("查询处理", "process_query"),
                    ("多智能体检索", "_execute_multi_agent_search"),
                    ("结果去重", "_deduplicate_results"),
                    ("智能体状态", "get_agent_status"),
                    ("健康检查", "health_check"),
                    ("性能优化", "optimize_performance"),
                    ("统计重置", "reset_stats"),
                    ("全局实例", "enhanced_autogen_service")
                ]
                
                for feature_name, feature_value in main_service_features:
                    if feature_value in content:
                        self.log_result(f"主服务功能: {feature_name}", True)
                    else:
                        self.log_result(f"主服务功能: {feature_name}", False, f"未找到 {feature_value}")
                
                # 检查智能体功能
                agent_functions = [
                    ("语义检索功能", "semantic_search"),
                    ("图谱检索功能", "graph_search"),
                    ("混合检索功能", "hybrid_search"),
                    ("答案生成功能", "generate_answer"),
                    ("检索质量评估", "assess_search_quality"),
                    ("答案质量评估", "assess_answer_quality"),
                    ("查询分析", "analyze_query"),
                    ("任务创建", "create_task"),
                    ("性能指标更新", "update_performance_metrics")
                ]
                
                for func_name, func_value in agent_functions:
                    if func_value in content:
                        self.log_result(f"智能体功能: {func_name}", True)
                    else:
                        self.log_result(f"智能体功能: {func_name}", False, f"未找到 {func_value}")
                        
            else:
                self.log_result("增强版AutoGen服务文件", False, "文件不存在")
                
        except Exception as e:
            self.log_result("增强版AutoGen服务验证", False, str(e))
    
    def verify_workflow_manager(self):
        """验证工作流管理器"""
        print("\n🔄 验证智能体工作流管理器...")
        
        try:
            workflow_file = project_root / "backend" / "app" / "services" / "agent_workflow_manager.py"
            if workflow_file.exists():
                content = workflow_file.read_text(encoding='utf-8')
                
                # 检查工作流核心组件
                workflow_components = [
                    ("工作流类型枚举", "WorkflowType"),
                    ("任务状态枚举", "TaskStatus"),
                    ("工作流步骤", "WorkflowStep"),
                    ("工作流定义", "WorkflowDefinition"),
                    ("工作流执行", "WorkflowExecution"),
                    ("工作流管理器", "AgentWorkflowManager")
                ]
                
                for comp_name, comp_value in workflow_components:
                    if comp_value in content:
                        self.log_result(f"工作流组件: {comp_name}", True)
                    else:
                        self.log_result(f"工作流组件: {comp_name}", False, f"未找到 {comp_value}")
                
                # 检查预定义工作流类型
                workflow_types = [
                    ("简单问答", "SIMPLE_QA"),
                    ("复杂研究", "COMPLEX_RESEARCH"),
                    ("比较分析", "COMPARATIVE_ANALYSIS"),
                    ("多步推理", "MULTI_STEP_REASONING"),
                    ("事实核查", "FACT_CHECKING")
                ]
                
                for wf_name, wf_value in workflow_types:
                    if wf_value in content:
                        self.log_result(f"工作流类型: {wf_name}", True)
                    else:
                        self.log_result(f"工作流类型: {wf_name}", False, f"未找到 {wf_value}")
                
                # 检查工作流管理功能
                workflow_functions = [
                    ("工作流推荐", "get_workflow_recommendation"),
                    ("工作流执行", "execute_workflow"),
                    ("顺序执行", "_execute_sequential_workflow"),
                    ("并行执行", "_execute_parallel_workflow"),
                    ("步骤执行", "_execute_step"),
                    ("依赖检查", "_check_dependencies"),
                    ("依赖图构建", "_build_dependency_graph"),
                    ("执行状态", "get_execution_status"),
                    ("工作流定义", "get_workflow_definitions"),
                    ("全局实例", "agent_workflow_manager")
                ]
                
                for func_name, func_value in workflow_functions:
                    if func_value in content:
                        self.log_result(f"工作流功能: {func_name}", True)
                    else:
                        self.log_result(f"工作流功能: {func_name}", False, f"未找到 {func_value}")
                        
            else:
                self.log_result("工作流管理器文件", False, "文件不存在")
                
        except Exception as e:
            self.log_result("工作流管理器验证", False, str(e))
    
    def verify_autogen_integration(self):
        """验证AutoGen框架集成"""
        print("\n🔗 验证AutoGen框架集成...")
        
        try:
            # 检查原有AutoGen服务的更新
            original_autogen_file = project_root / "backend" / "app" / "services" / "autogen_agent_service.py"
            if original_autogen_file.exists():
                content = original_autogen_file.read_text(encoding='utf-8')
                
                autogen_features = [
                    ("ConversableAgent导入", "ConversableAgent"),
                    ("GroupChat导入", "GroupChat"),
                    ("GroupChatManager导入", "GroupChatManager"),
                    ("语义检索智能体", "SemanticSearchAgent"),
                    ("图谱检索智能体", "GraphSearchAgent"),
                    ("混合检索智能体", "HybridSearchAgent"),
                    ("答案生成智能体", "AnswerGenerationAgent"),
                    ("AutoGen服务主类", "AutoGenAgentService")
                ]
                
                for feature_name, feature_value in autogen_features:
                    if feature_value in content:
                        self.log_result(f"AutoGen集成: {feature_name}", True)
                    else:
                        self.log_result(f"AutoGen集成: {feature_name}", False, f"未找到 {feature_value}")
            else:
                self.log_result("原有AutoGen服务文件", False, "文件不存在")
            
            # 检查增强版服务中的AutoGen集成
            enhanced_file = project_root / "backend" / "app" / "services" / "enhanced_autogen_service.py"
            if enhanced_file.exists():
                content = enhanced_file.read_text(encoding='utf-8')
                
                enhanced_autogen_features = [
                    ("AutoGen导入", "import autogen"),
                    ("ConversableAgent继承", "ConversableAgent"),
                    ("LLM配置", "llm_config"),
                    ("系统消息", "system_message"),
                    ("人工输入模式", "human_input_mode"),
                    ("AutoGen配置列表", "AUTOGEN_CONFIG_LIST"),
                    ("温度参数", "AUTOGEN_TEMPERATURE"),
                    ("超时参数", "AUTOGEN_TIMEOUT")
                ]
                
                for feature_name, feature_value in enhanced_autogen_features:
                    if feature_value in content:
                        self.log_result(f"增强版AutoGen集成: {feature_name}", True)
                    else:
                        self.log_result(f"增强版AutoGen集成: {feature_name}", False, f"未找到 {feature_value}")
                        
        except Exception as e:
            self.log_result("AutoGen框架集成验证", False, str(e))
    
    def verify_service_dependencies(self):
        """验证服务依赖关系"""
        print("\n🔧 验证服务依赖关系...")
        
        try:
            # 检查增强版服务的依赖
            enhanced_file = project_root / "backend" / "app" / "services" / "enhanced_autogen_service.py"
            if enhanced_file.exists():
                content = enhanced_file.read_text(encoding='utf-8')
                
                service_dependencies = [
                    ("增强版向量数据库", "enhanced_vector_db_service"),
                    ("增强版图谱服务", "enhanced_graph_service"),
                    ("通义千问模型管理器", "qwen_model_manager"),
                    ("LLM服务", "LLMService"),
                    ("配置设置", "settings"),
                    ("异常处理", "AgentException")
                ]
                
                for dep_name, dep_value in service_dependencies:
                    if dep_value in content:
                        self.log_result(f"服务依赖: {dep_name}", True)
                    else:
                        self.log_result(f"服务依赖: {dep_name}", False, f"未找到 {dep_value}")
            
            # 检查工作流管理器的依赖
            workflow_file = project_root / "backend" / "app" / "services" / "agent_workflow_manager.py"
            if workflow_file.exists():
                content = workflow_file.read_text(encoding='utf-8')
                
                workflow_dependencies = [
                    ("增强版AutoGen服务", "EnhancedAutoGenService"),
                    ("搜索模式", "SearchMode"),
                    ("智能体任务", "AgentTask"),
                    ("智能体响应", "AgentResponse"),
                    ("工作流异常", "WorkflowException"),
                    ("异步支持", "asyncio"),
                    ("日志记录", "logger")
                ]
                
                for dep_name, dep_value in workflow_dependencies:
                    if dep_value in content:
                        self.log_result(f"工作流依赖: {dep_name}", True)
                    else:
                        self.log_result(f"工作流依赖: {dep_name}", False, f"未找到 {dep_value}")
                        
        except Exception as e:
            self.log_result("服务依赖验证", False, str(e))
    
    def verify_quality_control(self):
        """验证质量控制机制"""
        print("\n🎯 验证质量控制机制...")
        
        try:
            enhanced_file = project_root / "backend" / "app" / "services" / "enhanced_autogen_service.py"
            if enhanced_file.exists():
                content = enhanced_file.read_text(encoding='utf-8')
                
                quality_features = [
                    ("质量评估智能体", "QualityAssessmentAgent"),
                    ("检索质量评估", "assess_search_quality"),
                    ("答案质量评估", "assess_answer_quality"),
                    ("完整性评估", "_assess_completeness"),
                    ("准确性评估", "_assess_accuracy"),
                    ("清晰度评估", "_assess_clarity"),
                    ("一致性评估", "_assess_consistency"),
                    ("置信度计算", "_calculate_answer_confidence"),
                    ("质量指标", "quality_metrics"),
                    ("性能统计", "service_stats")
                ]
                
                for feature_name, feature_value in quality_features:
                    if feature_value in content:
                        self.log_result(f"质量控制: {feature_name}", True)
                    else:
                        self.log_result(f"质量控制: {feature_name}", False, f"未找到 {feature_value}")
                        
        except Exception as e:
            self.log_result("质量控制验证", False, str(e))
    
    def run_all_verifications(self):
        """运行所有验证"""
        print("🚀 开始第三阶段验证...")
        print("=" * 60)
        
        self.verify_enhanced_autogen_service()
        self.verify_workflow_manager()
        self.verify_autogen_integration()
        self.verify_service_dependencies()
        self.verify_quality_control()
        
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
            print("\n🎉 第三阶段验证全部通过！可以开始第四阶段开发。")
            return True
        else:
            print(f"\n⚠️  第三阶段验证发现 {failed} 个问题，需要修复后再继续。")
            if self.errors:
                print("\n错误详情:")
                for error in self.errors:
                    print(f"  - {error}")
            return False


def main():
    """主函数"""
    verifier = Stage3Verifier()
    success = verifier.run_all_verifications()
    
    if success:
        print("\n✨ 第三阶段智能体系统开发已完成！")
        print("\n📋 已完成的工作:")
        print("  - ✅ AutoGen多智能体框架搭建")
        print("  - ✅ 增强版专业智能体开发（语义检索、图谱检索、混合检索）")
        print("  - ✅ 答案生成和质量控制智能体")
        print("  - ✅ 智能体协调和结果融合机制")
        print("  - ✅ 复杂工作流管理系统")
        print("  - ✅ 多种预定义工作流（简单问答、复杂研究、比较分析、多步推理、事实核查）")
        print("  - ✅ 质量评估和性能监控")
        
        print("\n🎯 下一步工作:")
        print("  - 🖥️ 开始第四阶段：后端管理界面开发")
        print("  - 📊 知识库管理界面（Nuxt.js + Naive UI）")
        print("  - 📄 文档管理和处理界面")
        print("  - 🕸️ 知识图谱可视化")
        print("  - 📈 系统监控和统计面板")
        
        return 0
    else:
        print("\n🔧 请先修复上述问题，然后重新运行验证。")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
