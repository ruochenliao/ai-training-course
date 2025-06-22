#!/usr/bin/env python3
"""
系统测试脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.services.agent_service import (
    QueryContext,
    query_analyzer
)
from app.services.workflow_service import (
    workflow_orchestrator,
    WorkflowConfig,
    WorkflowType
)
from app.services.llm_service import LLMService
from app.services.embedding_service import embedding_service
from app.services.vector_db import VectorDBService
from app.services.graph_db_service import neo4j_service


async def test_llm_service():
    """测试LLM服务"""
    print("🧠 测试LLM服务...")
    
    try:
        llm = LLMService()
        
        # 测试健康检查
        health = await llm.check_model_health()
        print(f"LLM健康状态: {health}")
        
        # 测试文本生成
        response = await llm.generate_text(
            prompt="你好，请介绍一下你自己",
            max_tokens=100
        )
        print(f"LLM响应: {response[:100]}...")
        
        print("✅ LLM服务测试通过")
        return True
        
    except Exception as e:
        print(f"❌ LLM服务测试失败: {e}")
        return False


async def test_embedding_service():
    """测试嵌入服务"""
    print("🔢 测试嵌入服务...")
    
    try:
        # 测试健康检查
        health = await embedding_service.health_check()
        print(f"嵌入服务健康状态: {health}")
        
        # 测试单个文本嵌入
        text = "这是一个测试文本"
        embedding = await embedding_service.create_embeddings(text)
        print(f"嵌入向量维度: {len(embedding)}")
        
        # 测试批量嵌入
        texts = ["文本1", "文本2", "文本3"]
        embeddings = await embedding_service.create_embeddings(texts)
        print(f"批量嵌入结果: {len(embeddings)} 个向量")
        
        print("✅ 嵌入服务测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 嵌入服务测试失败: {e}")
        return False


async def test_vector_db():
    """测试向量数据库"""
    print("🗄️ 测试向量数据库...")
    
    try:
        vector_db = VectorDBService()
        
        # 测试连接
        await vector_db.connect()
        print("向量数据库连接成功")
        
        # 测试健康检查
        health = await vector_db.health_check()
        print(f"向量数据库健康状态: {health}")
        
        print("✅ 向量数据库测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 向量数据库测试失败: {e}")
        return False


async def test_graph_db():
    """测试图数据库"""
    print("🕸️ 测试图数据库...")
    
    try:
        # 测试连接
        await neo4j_service.connect()
        print("图数据库连接成功")
        
        # 测试健康检查
        health = await neo4j_service.health_check()
        print(f"图数据库健康状态: {health}")
        
        # 测试简单查询
        result = await neo4j_service.execute_query("RETURN 1 as test")
        print(f"测试查询结果: {result}")
        
        print("✅ 图数据库测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 图数据库测试失败: {e}")
        return False


async def test_agents():
    """测试智能体"""
    print("🤖 测试智能体系统...")
    
    try:
        # 创建测试查询上下文
        context = QueryContext(
            query="什么是人工智能？",
            user_id=1,
            knowledge_base_ids=[1],
            metadata={"test": True}
        )
        
        # 测试查询分析智能体
        print("测试查询分析智能体...")
        analysis_result = await query_analyzer.process(context)
        print(f"查询分析结果: {analysis_result}")
        
        print("✅ 智能体系统测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 智能体系统测试失败: {e}")
        return False


async def test_workflow():
    """测试工作流"""
    print("⚙️ 测试工作流系统...")
    
    try:
        # 创建测试查询上下文
        context = QueryContext(
            query="请介绍一下机器学习的基本概念",
            user_id=1,
            knowledge_base_ids=[1],
            metadata={"test": True}
        )
        
        # 配置工作流
        config = WorkflowConfig(
            workflow_type=WorkflowType.SIMPLE_QA,
            enable_vector_search=False,  # 暂时禁用，避免数据库依赖
            enable_graph_search=False,
            enable_result_fusion=False
        )
        
        # 执行工作流
        print("执行测试工作流...")
        result = await workflow_orchestrator.execute_workflow(context, config)
        print(f"工作流结果: {result.answer[:100]}...")
        print(f"处理时间: {result.processing_time:.2f}秒")
        print(f"置信度: {result.confidence_score:.2f}")
        
        print("✅ 工作流系统测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 工作流系统测试失败: {e}")
        return False


async def test_stream_workflow():
    """测试流式工作流"""
    print("🌊 测试流式工作流...")
    
    try:
        # 创建测试查询上下文
        context = QueryContext(
            query="请简单介绍一下深度学习",
            user_id=1,
            knowledge_base_ids=[1],
            metadata={"test": True}
        )
        
        # 配置工作流
        config = WorkflowConfig(
            workflow_type=WorkflowType.SIMPLE_QA,
            enable_vector_search=False,
            enable_graph_search=False,
            enable_result_fusion=False
        )
        
        # 执行流式工作流
        print("执行流式工作流...")
        answer_chunks = []
        
        async for event in workflow_orchestrator.execute_workflow_stream(context, config):
            if event["type"] == "answer_chunk":
                chunk = event["data"]["chunk"]
                answer_chunks.append(chunk)
                print(chunk, end="", flush=True)
            elif event["type"] == "workflow_complete":
                print(f"\n\n流式工作流完成")
                break
            elif event["type"] == "workflow_error":
                print(f"\n流式工作流错误: {event['data']['error']}")
                break
        
        full_answer = "".join(answer_chunks)
        print(f"完整答案长度: {len(full_answer)} 字符")
        
        print("✅ 流式工作流测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 流式工作流测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🚀 开始系统测试...\n")
    
    test_results = []
    
    # 基础服务测试
    test_results.append(await test_llm_service())
    print()
    
    test_results.append(await test_embedding_service())
    print()
    
    # 数据库测试（可能失败，因为需要外部服务）
    test_results.append(await test_vector_db())
    print()
    
    test_results.append(await test_graph_db())
    print()
    
    # 智能体和工作流测试
    test_results.append(await test_agents())
    print()
    
    test_results.append(await test_workflow())
    print()
    
    test_results.append(await test_stream_workflow())
    print()
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统运行正常。")
    else:
        print("⚠️ 部分测试失败，请检查相关服务配置。")
        print("注意：数据库相关测试需要Milvus和Neo4j服务运行。")
    
    return passed == total


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
