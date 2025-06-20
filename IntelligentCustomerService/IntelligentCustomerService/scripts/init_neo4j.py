#!/usr/bin/env python3
"""
Neo4j图数据库初始化脚本
创建约束、索引和示例数据
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.graph_store import get_graph_store, GraphStoreException
from app.services.knowledge_graph_service import knowledge_graph_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Neo4jInitializer:
    """Neo4j初始化器"""
    
    def __init__(self):
        """初始化"""
        self.graph_store = get_graph_store()
    
    async def initialize_database(self):
        """初始化数据库"""
        logger.info("开始初始化Neo4j数据库...")
        
        try:
            # 1. 连接数据库
            await self.graph_store.connect()
            logger.info("✅ Neo4j连接成功")
            
            # 2. 清理现有数据（可选）
            await self._clean_database()
            
            # 3. 创建示例数据
            await self._create_sample_data()
            
            # 4. 验证数据
            await self._verify_data()
            
            logger.info("✅ Neo4j数据库初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ Neo4j数据库初始化失败: {str(e)}")
            return False
    
    async def _clean_database(self):
        """清理数据库（谨慎使用）"""
        try:
            # 询问用户是否清理
            response = input("是否清理现有数据？(y/N): ").strip().lower()
            if response == 'y':
                query = "MATCH (n) DETACH DELETE n"
                await self.graph_store.execute_cypher(query)
                logger.info("✅ 数据库清理完成")
            else:
                logger.info("跳过数据库清理")
                
        except Exception as e:
            logger.error(f"数据库清理失败: {str(e)}")
    
    async def _create_sample_data(self):
        """创建示例数据"""
        logger.info("创建示例数据...")
        
        try:
            # 示例文本
            sample_texts = [
                {
                    "text": "智能客服系统是一个基于人工智能技术的客户服务解决方案。它使用自然语言处理技术来理解用户问题，并提供准确的回答。",
                    "knowledge_base_id": "kb_001"
                },
                {
                    "text": "FastAPI是一个现代、快速的Web框架，用于构建API。它基于Python类型提示，支持异步编程和自动API文档生成。",
                    "knowledge_base_id": "kb_002"
                },
                {
                    "text": "Neo4j是一个图数据库管理系统，专门用于存储和查询图形数据。它使用Cypher查询语言来操作图数据。",
                    "knowledge_base_id": "kb_003"
                }
            ]
            
            # 处理每个示例文本
            for sample in sample_texts:
                logger.info(f"处理示例文本: {sample['text'][:50]}...")
                
                # 抽取实体和关系
                extraction_result = await knowledge_graph_service.extract_entities_and_relations(
                    text=sample["text"],
                    knowledge_base_id=sample["knowledge_base_id"]
                )
                
                # 构建知识图谱
                build_result = await knowledge_graph_service.build_knowledge_graph(extraction_result)
                
                logger.info(f"创建实体: {build_result['created_entities']}, 关系: {build_result['created_relations']}")
            
            # 创建一些手动实体和关系
            await self._create_manual_entities()
            
            logger.info("✅ 示例数据创建完成")
            
        except Exception as e:
            logger.error(f"创建示例数据失败: {str(e)}")
    
    async def _create_manual_entities(self):
        """创建手动实体和关系"""
        try:
            # 创建技术栈实体
            tech_entities = [
                {
                    "id": "tech_python",
                    "name": "Python",
                    "type": "技术",
                    "properties": {
                        "description": "高级编程语言",
                        "category": "编程语言",
                        "popularity": "高"
                    }
                },
                {
                    "id": "tech_fastapi",
                    "name": "FastAPI",
                    "type": "技术",
                    "properties": {
                        "description": "现代Web框架",
                        "category": "Web框架",
                        "language": "Python"
                    }
                },
                {
                    "id": "tech_neo4j",
                    "name": "Neo4j",
                    "type": "技术",
                    "properties": {
                        "description": "图数据库",
                        "category": "数据库",
                        "type": "图数据库"
                    }
                },
                {
                    "id": "product_ics",
                    "name": "智能客服系统",
                    "type": "产品",
                    "properties": {
                        "description": "AI驱动的客户服务解决方案",
                        "category": "软件产品",
                        "version": "2.0"
                    }
                }
            ]
            
            # 创建实体
            for entity in tech_entities:
                await self.graph_store.create_entity(
                    entity_id=entity["id"],
                    name=entity["name"],
                    entity_type=entity["type"],
                    properties=entity["properties"],
                    knowledge_base_id="manual_kb"
                )
            
            # 创建关系
            relationships = [
                {
                    "source": "tech_fastapi",
                    "target": "tech_python",
                    "type": "基于",
                    "properties": {"description": "FastAPI基于Python开发"}
                },
                {
                    "source": "product_ics",
                    "target": "tech_fastapi",
                    "type": "使用",
                    "properties": {"description": "智能客服系统使用FastAPI框架"}
                },
                {
                    "source": "product_ics",
                    "target": "tech_neo4j",
                    "type": "使用",
                    "properties": {"description": "智能客服系统使用Neo4j存储知识图谱"}
                }
            ]
            
            for rel in relationships:
                await self.graph_store.create_relationship(
                    source_entity_id=rel["source"],
                    target_entity_id=rel["target"],
                    relationship_type=rel["type"],
                    properties=rel["properties"]
                )
            
            logger.info("✅ 手动实体和关系创建完成")
            
        except Exception as e:
            logger.error(f"创建手动实体失败: {str(e)}")
    
    async def _verify_data(self):
        """验证数据"""
        try:
            # 获取统计信息
            stats = await self.graph_store.get_graph_statistics()
            
            logger.info("📊 数据库统计信息:")
            logger.info(f"  实体数量: {stats['entity_count']}")
            logger.info(f"  关系数量: {stats['relationship_count']}")
            logger.info(f"  实体类型: {', '.join(stats['entity_types'])}")
            logger.info(f"  关系类型: {', '.join(stats['relationship_types'])}")
            
            # 测试查询
            test_entities = await self.graph_store.find_entities(limit=5)
            logger.info(f"  测试查询返回 {len(test_entities)} 个实体")
            
            # 测试路径查找
            if len(test_entities) >= 2:
                entity1 = test_entities[0]
                entity2 = test_entities[1]
                
                path = await self.graph_store.find_shortest_path(
                    entity1["id"], 
                    entity2["id"]
                )
                
                if path:
                    logger.info(f"  测试路径查找: 找到长度为 {path['path_length']} 的路径")
                else:
                    logger.info("  测试路径查找: 未找到路径")
            
            logger.info("✅ 数据验证完成")
            
        except Exception as e:
            logger.error(f"数据验证失败: {str(e)}")
    
    async def health_check(self):
        """健康检查"""
        try:
            health = await self.graph_store.health_check()
            
            if health["status"] == "healthy":
                logger.info("✅ Neo4j健康检查通过")
                logger.info(f"  响应时间: {health['response_time']:.3f}秒")
                return True
            else:
                logger.error(f"❌ Neo4j健康检查失败: {health.get('error', '未知错误')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 健康检查异常: {str(e)}")
            return False


async def main():
    """主函数"""
    logger.info("🚀 开始Neo4j初始化...")
    
    try:
        # 初始化知识图谱服务
        await knowledge_graph_service.initialize()
        
        # 创建初始化器
        initializer = Neo4jInitializer()
        
        # 健康检查
        if not await initializer.health_check():
            logger.error("❌ Neo4j服务不可用，请检查连接配置")
            return False
        
        # 初始化数据库
        success = await initializer.initialize_database()
        
        if success:
            logger.info("🎉 Neo4j初始化完成！")
            
            # 显示使用提示
            print("\n📋 使用提示:")
            print("1. 可以通过Neo4j Browser查看图谱: http://localhost:7474")
            print("2. 使用Cypher查询语言操作图数据")
            print("3. 通过API接口进行图谱查询和管理")
            print("4. 查看知识图谱统计信息")
            
            return True
        else:
            logger.error("❌ Neo4j初始化失败")
            return False
            
    except KeyboardInterrupt:
        logger.info("用户中断初始化")
        return False
    except Exception as e:
        logger.error(f"初始化过程中发生错误: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
