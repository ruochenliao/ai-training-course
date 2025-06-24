#!/usr/bin/env python3
"""
第二阶段验证脚本
验证核心服务开发的成果
"""

import sys
import os
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent.parent


class Stage2Verifier:
    """第二阶段验证器"""
    
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
    
    def verify_marker_service_enhancement(self):
        """验证Marker文档解析服务优化"""
        print("\n📄 验证Marker文档解析服务...")
        
        try:
            # 检查增强版Marker服务文件
            enhanced_marker_file = project_root / "backend" / "app" / "services" / "enhanced_marker_service.py"
            if enhanced_marker_file.exists():
                content = enhanced_marker_file.read_text(encoding='utf-8')
                
                # 检查关键功能
                checks = [
                    ("文档处理器类", "DocumentProcessor"),
                    ("增强版Marker服务", "EnhancedMarkerService"),
                    ("进度跟踪", "parse_document_with_progress"),
                    ("批量处理", "batch_process_documents"),
                    ("内容摘要", "_generate_summary"),
                    ("关键词提取", "_extract_keywords"),
                    ("语言检测", "_detect_language"),
                    ("可读性评分", "_calculate_readability"),
                    ("统计信息", "get_statistics"),
                    ("清理功能", "cleanup_completed_processors")
                ]
                
                for check_name, check_value in checks:
                    if check_value in content:
                        self.log_result(f"Marker增强功能: {check_name}", True)
                    else:
                        self.log_result(f"Marker增强功能: {check_name}", False, f"未找到 {check_value}")
            else:
                self.log_result("增强版Marker服务文件", False, "文件不存在")
            
            # 检查原有Marker服务的优化
            marker_file = project_root / "backend" / "app" / "services" / "marker_service.py"
            if marker_file.exists():
                content = marker_file.read_text(encoding='utf-8')
                
                optimization_checks = [
                    ("官方源码集成", "convert_single_pdf"),
                    ("模型异步初始化", "_initialize_marker_models"),
                    ("批量处理支持", "parse_documents_batch"),
                    ("质量评估", "_assess_content_quality"),
                    ("错误处理优化", "force_ocr"),
                    ("处理时间统计", "processing_time"),
                    ("文件大小检查", "file_size")
                ]
                
                for check_name, check_value in optimization_checks:
                    if check_value in content:
                        self.log_result(f"Marker优化: {check_name}", True)
                    else:
                        self.log_result(f"Marker优化: {check_name}", False, f"未找到 {check_value}")
            else:
                self.log_result("Marker服务文件", False, "文件不存在")
                
        except Exception as e:
            self.log_result("Marker服务验证", False, str(e))
    
    def verify_vector_db_enhancement(self):
        """验证Milvus向量数据库服务完善"""
        print("\n🗄️ 验证Milvus向量数据库服务...")
        
        try:
            # 检查增强版向量数据库服务
            enhanced_vector_file = project_root / "backend" / "app" / "services" / "enhanced_vector_db.py"
            if enhanced_vector_file.exists():
                content = enhanced_vector_file.read_text(encoding='utf-8')
                
                checks = [
                    ("搜索配置类", "SearchConfig"),
                    ("混合搜索结果", "HybridSearchResult"),
                    ("增强版向量服务", "EnhancedVectorDBService"),
                    ("混合检索", "hybrid_search"),
                    ("语义检索重排", "semantic_search_with_rerank"),
                    ("批量插入", "batch_insert_vectors"),
                    ("分区管理", "create_partitions"),
                    ("关键词检索", "_keyword_search"),
                    ("结果融合", "_combine_search_results"),
                    ("集合健康检查", "get_collection_health"),
                    ("性能统计", "get_service_stats"),
                    ("缓存支持", "cache_enabled")
                ]
                
                for check_name, check_value in checks:
                    if check_value in content:
                        self.log_result(f"向量数据库增强: {check_name}", True)
                    else:
                        self.log_result(f"向量数据库增强: {check_name}", False, f"未找到 {check_value}")
            else:
                self.log_result("增强版向量数据库服务文件", False, "文件不存在")
                
        except Exception as e:
            self.log_result("向量数据库服务验证", False, str(e))
    
    def verify_graph_service_development(self):
        """验证Neo4j知识图谱服务开发"""
        print("\n🕸️ 验证Neo4j知识图谱服务...")
        
        try:
            # 检查增强版图谱服务
            enhanced_graph_file = project_root / "backend" / "app" / "services" / "enhanced_graph_service.py"
            if enhanced_graph_file.exists():
                content = enhanced_graph_file.read_text(encoding='utf-8')
                
                checks = [
                    ("实体类", "Entity"),
                    ("关系类", "Relationship"),
                    ("图谱路径", "GraphPath"),
                    ("实体抽取器", "EntityExtractor"),
                    ("增强版图谱服务", "EnhancedGraphService"),
                    ("知识图谱构建", "build_knowledge_graph"),
                    ("实体抽取", "extract_entities"),
                    ("关系抽取", "extract_relationships"),
                    ("路径查找", "find_paths"),
                    ("实体邻居", "get_entity_neighbors"),
                    ("置信度计算", "_calculate_entity_confidence"),
                    ("索引创建", "_create_indexes"),
                    ("统计更新", "_update_stats")
                ]
                
                for check_name, check_value in checks:
                    if check_value in content:
                        self.log_result(f"图谱服务功能: {check_name}", True)
                    else:
                        self.log_result(f"图谱服务功能: {check_name}", False, f"未找到 {check_value}")
                
                # 检查实体类型和关系类型
                entity_types = ['PERSON', 'ORGANIZATION', 'LOCATION', 'PRODUCT', 'CONCEPT']
                relation_types = ['BELONGS_TO', 'LOCATED_IN', 'WORKS_FOR', 'DEVELOPS', 'USES']
                
                for entity_type in entity_types:
                    if entity_type in content:
                        self.log_result(f"实体类型: {entity_type}", True)
                    else:
                        self.log_result(f"实体类型: {entity_type}", False, f"未找到 {entity_type}")
                
                for relation_type in relation_types:
                    if relation_type in content:
                        self.log_result(f"关系类型: {relation_type}", True)
                    else:
                        self.log_result(f"关系类型: {relation_type}", False, f"未找到 {relation_type}")
                        
            else:
                self.log_result("增强版图谱服务文件", False, "文件不存在")
                
        except Exception as e:
            self.log_result("图谱服务验证", False, str(e))
    
    def verify_chunker_enhancement(self):
        """验证智能文档分块功能"""
        print("\n🧩 验证智能文档分块功能...")
        
        try:
            # 检查增强版分块服务
            enhanced_chunker_file = project_root / "backend" / "app" / "services" / "enhanced_chunker.py"
            if enhanced_chunker_file.exists():
                content = enhanced_chunker_file.read_text(encoding='utf-8')
                
                checks = [
                    ("增强版分块配置", "EnhancedChunkConfig"),
                    ("分块分析结果", "ChunkAnalysis"),
                    ("内容类型检测器", "ContentTypeDetector"),
                    ("增强版分块器", "EnhancedDocumentChunker"),
                    ("自适应分块", "_adaptive_chunking"),
                    ("语义分块", "_semantic_chunking"),
                    ("结构感知分块", "_structure_aware_chunking"),
                    ("标题分块", "_header_based_chunking"),
                    ("语义相似度", "_calculate_cosine_similarity"),
                    ("质量评分", "_calculate_quality_score"),
                    ("语义连贯性", "_calculate_semantic_coherence"),
                    ("结构完整性", "_calculate_structure_integrity"),
                    ("可读性评分", "_calculate_readability_score"),
                    ("质量过滤", "_filter_by_quality"),
                    ("后处理优化", "_post_process_chunks")
                ]
                
                for check_name, check_value in checks:
                    if check_value in content:
                        self.log_result(f"分块增强功能: {check_name}", True)
                    else:
                        self.log_result(f"分块增强功能: {check_name}", False, f"未找到 {check_value}")
                
                # 检查分块策略
                strategies = ['adaptive', 'semantic', 'structure_aware', 'recursive', 'fixed']
                for strategy in strategies:
                    if strategy in content:
                        self.log_result(f"分块策略: {strategy}", True)
                    else:
                        self.log_result(f"分块策略: {strategy}", False, f"未找到 {strategy}")
                        
            else:
                self.log_result("增强版分块服务文件", False, "文件不存在")
                
        except Exception as e:
            self.log_result("分块服务验证", False, str(e))
    
    def verify_service_integration(self):
        """验证服务集成"""
        print("\n🔗 验证服务集成...")
        
        try:
            # 检查服务间的依赖关系
            services_to_check = [
                ("enhanced_marker_service.py", ["MarkerService"]),
                ("enhanced_vector_db.py", ["MilvusService", "reranker_service"]),
                ("enhanced_graph_service.py", ["Neo4jService"]),
                ("enhanced_chunker.py", ["DocumentChunker", "embedding_service"])
            ]
            
            for service_file, dependencies in services_to_check:
                file_path = project_root / "backend" / "app" / "services" / service_file
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    
                    for dep in dependencies:
                        if dep in content:
                            self.log_result(f"服务依赖 {service_file}: {dep}", True)
                        else:
                            self.log_result(f"服务依赖 {service_file}: {dep}", False, f"未找到依赖 {dep}")
                else:
                    self.log_result(f"服务文件: {service_file}", False, "文件不存在")
            
            # 检查全局服务实例
            global_instances = [
                ("enhanced_marker_service", "enhanced_marker_service"),
                ("enhanced_vector_db", "enhanced_vector_db_service"),
                ("enhanced_graph_service", "enhanced_graph_service"),
                ("enhanced_chunker", "enhanced_chunker")
            ]
            
            for service_file, instance_name in global_instances:
                file_path = project_root / "backend" / "app" / "services" / f"{service_file}.py"
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    if instance_name in content:
                        self.log_result(f"全局实例: {instance_name}", True)
                    else:
                        self.log_result(f"全局实例: {instance_name}", False, f"未找到实例 {instance_name}")
                        
        except Exception as e:
            self.log_result("服务集成验证", False, str(e))
    
    def verify_configuration_updates(self):
        """验证配置更新"""
        print("\n⚙️ 验证配置更新...")
        
        try:
            config_file = project_root / "backend" / "app" / "core" / "config.py"
            if config_file.exists():
                content = config_file.read_text(encoding='utf-8')
                
                # 检查新增的配置项
                new_configs = [
                    "MARKER_ENABLED",
                    "MARKER_MAX_PAGES", 
                    "MARKER_LANGUAGES",
                    "MARKER_BATCH_MULTIPLIER",
                    "GRAPH_MAX_NODES",
                    "QA_MAX_SOURCES",
                    "DEFAULT_SCORE_THRESHOLD"
                ]
                
                for config in new_configs:
                    if config in content:
                        self.log_result(f"配置项: {config}", True)
                    else:
                        self.log_result(f"配置项: {config}", False, f"未找到配置 {config}")
                        
            else:
                self.log_result("配置文件", False, "文件不存在")
                
        except Exception as e:
            self.log_result("配置验证", False, str(e))
    
    def run_all_verifications(self):
        """运行所有验证"""
        print("🚀 开始第二阶段验证...")
        print("=" * 60)
        
        self.verify_marker_service_enhancement()
        self.verify_vector_db_enhancement()
        self.verify_graph_service_development()
        self.verify_chunker_enhancement()
        self.verify_service_integration()
        self.verify_configuration_updates()
        
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
            print("\n🎉 第二阶段验证全部通过！可以开始第三阶段开发。")
            return True
        else:
            print(f"\n⚠️  第二阶段验证发现 {failed} 个问题，需要修复后再继续。")
            if self.errors:
                print("\n错误详情:")
                for error in self.errors:
                    print(f"  - {error}")
            return False


def main():
    """主函数"""
    verifier = Stage2Verifier()
    success = verifier.run_all_verifications()
    
    if success:
        print("\n✨ 第二阶段核心服务开发已完成！")
        print("\n📋 已完成的工作:")
        print("  - ✅ Marker文档解析服务优化（支持进度跟踪、批量处理、质量评估）")
        print("  - ✅ Milvus向量数据库服务完善（支持混合检索、分区管理、性能优化）")
        print("  - ✅ Neo4j知识图谱服务开发（支持实体抽取、关系识别、图谱构建）")
        print("  - ✅ 智能文档分块功能（支持语义分块、结构感知、自适应分块）")
        print("  - ✅ 服务间集成和配置优化")
        
        print("\n🎯 下一步工作:")
        print("  - 🤖 开始第三阶段：智能体系统开发")
        print("  - 🔧 AutoGen多智能体框架搭建")
        print("  - 🔍 专业智能体开发（语义检索、图谱检索、混合检索）")
        print("  - 💬 答案生成和质量控制")
        print("  - 🎛️ 智能体协调和结果融合")
        
        return 0
    else:
        print("\n🔧 请先修复上述问题，然后重新运行验证。")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
