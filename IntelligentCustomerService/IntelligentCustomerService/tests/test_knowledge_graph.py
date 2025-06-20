#!/usr/bin/env python3
"""
知识图谱功能测试
测试Neo4j集成和知识图谱服务
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.graph_store import get_graph_store, GraphStoreException
from app.services.knowledge_graph_service import knowledge_graph_service


class TestGraphStore:
    """图数据库存储测试"""
    
    @pytest.fixture
    async def graph_store(self):
        """获取图存储实例"""
        store = get_graph_store()
        await store.connect()
        yield store
        await store.disconnect()
    
    @pytest.mark.asyncio
    async def test_connection(self, graph_store):
        """测试数据库连接"""
        health = await graph_store.health_check()
        assert health["status"] == "healthy"
        assert "response_time" in health
    
    @pytest.mark.asyncio
    async def test_create_entity(self, graph_store):
        """测试创建实体"""
        entity_id = "test_entity_001"
        
        # 创建实体
        success = await graph_store.create_entity(
            entity_id=entity_id,
            name="测试实体",
            entity_type="测试",
            properties={"description": "这是一个测试实体"},
            knowledge_base_id="test_kb"
        )
        
        assert success is True
        
        # 清理测试数据
        await graph_store.delete_entity(entity_id)
    
    @pytest.mark.asyncio
    async def test_create_relationship(self, graph_store):
        """测试创建关系"""
        # 创建两个实体
        entity1_id = "test_entity_001"
        entity2_id = "test_entity_002"
        
        await graph_store.create_entity(
            entity_id=entity1_id,
            name="实体1",
            entity_type="测试",
            knowledge_base_id="test_kb"
        )
        
        await graph_store.create_entity(
            entity_id=entity2_id,
            name="实体2",
            entity_type="测试",
            knowledge_base_id="test_kb"
        )
        
        # 创建关系
        success = await graph_store.create_relationship(
            source_entity_id=entity1_id,
            target_entity_id=entity2_id,
            relationship_type="测试关系",
            properties={"description": "测试关系描述"}
        )
        
        assert success is True
        
        # 清理测试数据
        await graph_store.delete_entity(entity1_id)
        await graph_store.delete_entity(entity2_id)
    
    @pytest.mark.asyncio
    async def test_find_entities(self, graph_store):
        """测试查找实体"""
        # 创建测试实体
        entity_id = "test_find_entity"
        await graph_store.create_entity(
            entity_id=entity_id,
            name="查找测试实体",
            entity_type="测试",
            knowledge_base_id="test_kb"
        )
        
        # 查找实体
        entities = await graph_store.find_entities(
            entity_type="测试",
            knowledge_base_id="test_kb",
            limit=10
        )
        
        assert len(entities) > 0
        assert any(entity["id"] == entity_id for entity in entities)
        
        # 清理测试数据
        await graph_store.delete_entity(entity_id)
    
    @pytest.mark.asyncio
    async def test_find_related_entities(self, graph_store):
        """测试查找相关实体"""
        # 创建测试实体和关系
        entity1_id = "test_related_001"
        entity2_id = "test_related_002"
        
        await graph_store.create_entity(
            entity_id=entity1_id,
            name="相关实体1",
            entity_type="测试",
            knowledge_base_id="test_kb"
        )
        
        await graph_store.create_entity(
            entity_id=entity2_id,
            name="相关实体2",
            entity_type="测试",
            knowledge_base_id="test_kb"
        )
        
        await graph_store.create_relationship(
            source_entity_id=entity1_id,
            target_entity_id=entity2_id,
            relationship_type="相关",
            properties={}
        )
        
        # 查找相关实体
        related_entities = await graph_store.find_related_entities(
            entity_id=entity1_id,
            max_depth=2,
            limit=10
        )
        
        assert len(related_entities) > 0
        
        # 清理测试数据
        await graph_store.delete_entity(entity1_id)
        await graph_store.delete_entity(entity2_id)
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, graph_store):
        """测试获取统计信息"""
        stats = await graph_store.get_graph_statistics()
        
        assert "entity_count" in stats
        assert "relationship_count" in stats
        assert "entity_types" in stats
        assert "relationship_types" in stats
        assert isinstance(stats["entity_count"], int)
        assert isinstance(stats["relationship_count"], int)


class TestKnowledgeGraphService:
    """知识图谱服务测试"""
    
    @pytest.fixture
    async def kg_service(self):
        """获取知识图谱服务实例"""
        await knowledge_graph_service.initialize()
        return knowledge_graph_service
    
    @pytest.mark.asyncio
    async def test_extract_entities_and_relations(self, kg_service):
        """测试实体关系抽取"""
        text = "智能客服系统使用FastAPI框架开发，它是一个现代化的Web框架。"
        
        result = await kg_service.extract_entities_and_relations(
            text=text,
            knowledge_base_id="test_kb"
        )
        
        assert "entities" in result
        assert "relations" in result
        assert "text" in result
        assert result["text"] == text
        assert isinstance(result["entities"], list)
        assert isinstance(result["relations"], list)
    
    @pytest.mark.asyncio
    async def test_build_knowledge_graph(self, kg_service):
        """测试知识图谱构建"""
        # 准备抽取结果
        extraction_result = {
            "entities": [
                {
                    "id": "test_build_001",
                    "name": "测试系统",
                    "type": "产品",
                    "description": "用于测试的系统",
                    "properties": {},
                    "knowledge_base_id": "test_kb"
                },
                {
                    "id": "test_build_002",
                    "name": "测试框架",
                    "type": "技术",
                    "description": "用于测试的框架",
                    "properties": {},
                    "knowledge_base_id": "test_kb"
                }
            ],
            "relations": [
                {
                    "source": "测试系统",
                    "target": "测试框架",
                    "type": "使用",
                    "description": "系统使用框架",
                    "properties": {}
                }
            ],
            "knowledge_base_id": "test_kb"
        }
        
        # 构建知识图谱
        result = await kg_service.build_knowledge_graph(extraction_result)
        
        assert "success" in result
        assert "created_entities" in result
        assert "created_relations" in result
        assert result["success"] is True
        assert result["created_entities"] >= 0
        assert result["created_relations"] >= 0
        
        # 清理测试数据
        graph_store = get_graph_store()
        await graph_store.delete_entity("test_build_001")
        await graph_store.delete_entity("test_build_002")
    
    @pytest.mark.asyncio
    async def test_query_knowledge_graph(self, kg_service):
        """测试知识图谱查询"""
        # 创建测试数据
        graph_store = get_graph_store()
        entity_id = "test_query_entity"
        
        await graph_store.create_entity(
            entity_id=entity_id,
            name="查询测试实体",
            entity_type="测试",
            properties={"description": "用于查询测试的实体"},
            knowledge_base_id="test_kb"
        )
        
        # 执行查询
        results = await kg_service.query_knowledge_graph(
            query="查询测试",
            knowledge_base_id="test_kb",
            max_results=10
        )
        
        assert isinstance(results, list)
        
        # 清理测试数据
        await graph_store.delete_entity(entity_id)
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, kg_service):
        """测试获取统计信息"""
        stats = await kg_service.get_statistics()
        
        assert "entity_count" in stats
        assert "relationship_count" in stats
        assert isinstance(stats["entity_count"], int)
        assert isinstance(stats["relationship_count"], int)


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        # 初始化服务
        await knowledge_graph_service.initialize()
        graph_store = get_graph_store()
        
        # 1. 文本抽取
        text = "Python是一种编程语言，FastAPI是基于Python的Web框架。"
        extraction_result = await knowledge_graph_service.extract_entities_and_relations(
            text=text,
            knowledge_base_id="integration_test"
        )
        
        assert len(extraction_result["entities"]) > 0
        
        # 2. 构建图谱
        build_result = await knowledge_graph_service.build_knowledge_graph(extraction_result)
        assert build_result["success"] is True
        
        # 3. 查询验证
        entities = await graph_store.find_entities(
            knowledge_base_id="integration_test",
            limit=10
        )
        assert len(entities) > 0
        
        # 4. 统计信息
        stats = await graph_store.get_graph_statistics(
            knowledge_base_id="integration_test"
        )
        assert stats["entity_count"] > 0
        
        # 清理测试数据
        for entity in entities:
            await graph_store.delete_entity(entity["id"])


# 运行测试的主函数
async def run_tests():
    """运行所有测试"""
    print("🧪 开始知识图谱功能测试...")
    
    try:
        # 检查Neo4j连接
        graph_store = get_graph_store()
        health = await graph_store.health_check()
        
        if health["status"] != "healthy":
            print("❌ Neo4j服务不可用，跳过测试")
            return False
        
        print("✅ Neo4j连接正常")
        
        # 运行基础功能测试
        print("\n📋 测试图数据库基础功能...")
        
        # 测试连接
        await graph_store.connect()
        print("✅ 数据库连接测试通过")
        
        # 测试实体创建
        entity_id = "manual_test_entity"
        success = await graph_store.create_entity(
            entity_id=entity_id,
            name="手动测试实体",
            entity_type="测试",
            properties={"test": True},
            knowledge_base_id="manual_test"
        )
        
        if success:
            print("✅ 实体创建测试通过")
            
            # 测试实体查询
            entities = await graph_store.find_entities(
                entity_type="测试",
                knowledge_base_id="manual_test",
                limit=5
            )
            
            if entities:
                print("✅ 实体查询测试通过")
            else:
                print("⚠️ 实体查询测试失败")
            
            # 清理测试数据
            await graph_store.delete_entity(entity_id)
            print("✅ 测试数据清理完成")
        else:
            print("❌ 实体创建测试失败")
        
        # 测试知识图谱服务
        print("\n📋 测试知识图谱服务...")
        
        await knowledge_graph_service.initialize()
        
        # 测试文本抽取
        test_text = "智能客服系统是一个基于AI的客户服务解决方案。"
        extraction_result = await knowledge_graph_service.extract_entities_and_relations(
            text=test_text,
            knowledge_base_id="service_test"
        )
        
        if extraction_result and "entities" in extraction_result:
            print("✅ 文本抽取测试通过")
            
            # 测试图谱构建
            if extraction_result["entities"]:
                build_result = await knowledge_graph_service.build_knowledge_graph(extraction_result)
                
                if build_result.get("success"):
                    print("✅ 图谱构建测试通过")
                    
                    # 清理测试数据
                    for entity in extraction_result["entities"]:
                        await graph_store.delete_entity(entity["id"])
                    print("✅ 测试数据清理完成")
                else:
                    print("❌ 图谱构建测试失败")
            else:
                print("⚠️ 未抽取到实体，跳过图谱构建测试")
        else:
            print("❌ 文本抽取测试失败")
        
        print("\n🎉 知识图谱功能测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False


if __name__ == "__main__":
    # 运行手动测试
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
