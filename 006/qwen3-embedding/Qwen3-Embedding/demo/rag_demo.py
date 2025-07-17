"""
这个 Demo 演示了如何结合使用 Qwen3 Embedding 和 Reranker 模型
来实现高效的文档检索和重排序系统。

工作流程：
1. 使用Embedding模型将文档库向量化
2. 对用户查询进行向量化
3. 通过向量相似度快速检索候选文档（粗排）
4. 使用Reranker模型对候选文档进行精确排序（精排）
"""

import sys
import os
import time
import numpy as np
import torch
import torch.nn.functional as F
from typing import List, Tuple, Dict

# 添加上级目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples import Qwen3Embedding, Qwen3Reranker

class EmbeddingRerankingDemo:

    def __init__(self, embedding_model_path: str, reranker_model_path: str):
        """
        Args:
            embedding_model_path: Embedding 模型路径
            reranker_model_path: Reranker 模型路径
        """
        
        # 初始化Embedding模型
        print("加载Embedding模型")
        self.embedding_model = Qwen3Embedding(
            model_name_or_path=embedding_model_path,
            instruction="给定一个搜索查询，检索能够回答该查询的相关段落"
        )
        
        # 初始化 Reranker 模型
        print("加载Reranker模型")
        self.reranker_model = Qwen3Reranker(
            model_name_or_path=reranker_model_path,
            instruction="给定一个搜索查询，检索能够回答该查询的相关段落",
            max_length=2048
        )
        
        # 文档库和对应的向量表示
        self.documents = []
        self.document_embeddings = None
        
        print("系统初始化完成！\n")
    
    def load_document_corpus(self, documents: List[str]):
        """
        加载文档库并进行向量化
        
        Args:
            documents: 文档列表
        """
        print(f"正在加载文档库 ({len(documents)} 个文档)...")
        
        self.documents = documents
        
        # 对所有文档进行embedding
        start_time = time.time()
        self.document_embeddings = self.embedding_model.encode(documents, is_query=False)
        embedding_time = time.time() - start_time
        
        print(f"文档向量化完成，耗时: {embedding_time:.2f}s")
        print(f"向量维度: {self.document_embeddings.shape}")
        print()
    

    def search(self, query: str, top_k_embedding: int = 10, top_k_rerank: int = 5) -> List[Dict]:
        """
        执行搜索：先用 embedding 粗排，再用 reranker 精排
        
        Args:
            query: 查询文本
            top_k_embedding: embedding 阶段返回的候选文档数量
            top_k_rerank: reranker 阶段返回的最终文档数量
            
        Returns:
            排序后的文档结果列表
        """
        print(f"搜索查询: '{query}'")
        print("=" * 60)
        
        # 第一阶段：Embedding 粗排
        print("第一阶段：Embedding 向量检索 (粗排)")
        start_time = time.time()
        
        # 对查询进行向量化
        query_embedding = self.embedding_model.encode(query, is_query=True)
        
        # 计算与所有文档的余弦相似度
        similarity_scores = torch.nn.functional.cosine_similarity(
            query_embedding, self.document_embeddings, dim=1
        )

        # 使用 orch.topk获取相似度最高的k个文档的索引
        # min(top_k_embedding, len(self.documents)) 确保 k 不超过文档总数
        top_k_indices = torch.topk(similarity_scores, min(top_k_embedding, len(self.documents))).indices
        
        # 构建候选文档列表，每个元素包含:
        # 1. 文档索引 (i.item())
        # 2. 文档内容 (self.documents[i.item()])
        # 3. 相似度分数 (similarity_scores[i].item())
        candidate_docs = [(i.item(), self.documents[i.item()], similarity_scores[i].item()) 
                         for i in top_k_indices]
        
        embedding_time = time.time() - start_time
        print(f"Embedding 检索完成，耗时: {embedding_time:.3f}s")
        print(f"候选文档数量: {len(candidate_docs)}")
        
        # 显示候选文档
        print("\nEmbedding 粗排结果:")
        for i, (doc_idx, doc, score) in enumerate(candidate_docs, 1):
            print(f"  {i}. [得分: {score:.3f}] {doc[:100]}{'...' if len(doc) > 100 else ''}")
        
        # 第二阶段：Reranker 精排
        print(f"\n第二阶段：Reranker 精确排序 (精排)")
        start_time = time.time()
        
        # 准备查询-文档对
        query_doc_pairs = [(query, doc) for _, doc, _ in candidate_docs]
        
        # 使用reranker计算精确相关性分数
        rerank_scores = self.reranker_model.compute_scores(query_doc_pairs)
        
        # 结合原始文档信息和重排序分数
        reranked_results = []
        for i, ((doc_idx, doc, embedding_score), rerank_score) in enumerate(zip(candidate_docs, rerank_scores)):
            reranked_results.append({
                'document_id': doc_idx,
                'document': doc,
                'embedding_score': embedding_score,
                'rerank_score': rerank_score,
                'original_rank': i + 1
            })
        
        # 按重排序分数排序
        reranked_results.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        # 获取最终的top-k结果
        final_results = reranked_results[:top_k_rerank]
        
        rerank_time = time.time() - start_time
        print(f"Reranker 精排完成，耗时: {rerank_time:.3f}s")
        
        return final_results
    
    def display_results(self, results: List[Dict], query: str):
        """
        展示搜索结果
        
        Args:
            results: 搜索结果列表
            query: 原始查询
        """
        print(f"\n最终搜索结果 (查询: '{query}'):")
        print("=" * 60)
        
        for i, result in enumerate(results, 1):
            print(f"\n排名 {i}:")
            print(f"Embedding 分数: {result['embedding_score']:.3f}")
            print(f"Rerank 分数: {result['rerank_score']:.3f}")
            print(f"原始排名: {result['original_rank']}")
            print(f"文档内容: {result['document']}")
            print("-" * 60)
    
    def stop(self):
        """
        停止所有模型并清理资源
        """
        print("\n正在清理系统资源...")
        self.embedding_model.stop()
        self.reranker_model.stop()
        print("资源清理完成")


def create_sample_documents() -> List[str]:
    """
    创建示例文档库
    
    Returns:
        文档列表
    """
    documents = [
        # 1. 关于中国首都
        "北京是中华人民共和国的首都，也是中国的政治、文化和教育中心。北京有着三千多年的历史，是中国四大古都之一。",
        "中国的首都是北京，北京位于华北地区，是全国的政治中心。天安门广场和故宫都位于北京。",
        "Beijing is the capital city of China and serves as the political and cultural center of the country.",
        
        # 2. 关于物理学
        "万有引力定律是由牛顿发现的，它描述了宇宙中任何两个物体之间都存在相互吸引的力。这个力与两物体质量的乘积成正比，与距离的平方成反比。",
        "重力是地球对物体的吸引力，使物体有重量。重力加速度在地球表面约为9.8米每秒的平方。",
        "Gravity is a fundamental force of nature that causes objects with mass to attract each other. On Earth, gravity gives weight to physical objects.",
        
        # 3. 关于人工智能
        "人工智能(AI)是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。",
        "机器学习是人工智能的一个子领域，它使计算机能够在没有明确编程的情况下学习和改进。",
        "Large Language Models (LLMs) are AI systems trained on vast amounts of text data to understand and generate human-like text.",
        
        # 4. 关于编程
        "Python是一种高级编程语言，以其简洁的语法和强大的功能而闻名。它广泛用于数据科学、Web开发和人工智能。",
        "JavaScript是一种编程语言，主要用于Web开发，可以在浏览器和服务器端运行。",
        "深度学习框架如PyTorch和TensorFlow为研究人员和开发者提供了构建神经网络的工具。",
        
        # 5. 关于历史
        "中国有五千年的悠久历史，创造了灿烂的古代文明。从夏朝开始，中国经历了多个朝代的更替。",
        "长城是中国古代的军事防御工程，是中国古代文明的象征，也是世界文化遗产。",
        "The Great Wall of China is one of the most famous landmarks in the world and represents ancient Chinese civilization.",
        
        # 6. 关于科技
        "量子计算是一种利用量子力学原理进行信息处理的计算方式，有潜力解决传统计算机无法处理的复杂问题。",
        "5G技术是第五代移动通信技术，提供更快的数据传输速度和更低的延迟。",
        "区块链技术是一种分布式账本技术，最初为比特币等加密货币提供支持，现在应用于多个领域。"
    ]
    return documents


def main():

    # 模型路径
    embedding_model_path = "C:/Users/86134/Desktop/qwen3/Qwen3-Embedding-0.6B"
    reranker_model_path = "C:/Users/86134/Desktop/qwen3/Qwen3-Reranker-0.6B"
    
    try:
        # 初始化
        demo = EmbeddingRerankingDemo(embedding_model_path, reranker_model_path)
        
        # 加载示例文档库
        documents = create_sample_documents()
        demo.load_document_corpus(documents)
        
        # 定义测试查询
        test_queries = [
            "中国的首都是哪里？",
            "什么是重力？",
        ]
        
        # 对每个查询进行搜索演示
        for i, query in enumerate(test_queries, 1):

            # 执行搜索
            results = demo.search(query, top_k_embedding=8, top_k_rerank=3)
            
            # 显示结果
            demo.display_results(results, query)
            
        
        # 交互式查询模式
        print(f"\n{'='*60}")
        print("交互式查询模式 (输入 'quit' 退出)")
        print(f"{'='*60}")
        
        while True:
            try:
                user_query = input("\n 请输入您的查询: ").strip()
                if user_query.lower() in ['quit', 'exit', '退出', 'q']:
                    break
                
                if user_query:
                    results = demo.search(user_query, top_k_embedding=5, top_k_rerank=3)
                    demo.display_results(results, user_query)
                    
            except KeyboardInterrupt:
                print("\n 用户中断，退出程序")
                break
            except Exception as e:
                print(f" 查询过程中出现错误: {str(e)}")
        
    except Exception as e:
        print(f" 初始化或运行过程中出现错误: {str(e)}")
        
    finally:
        # 清理资源
        try:
            demo.stop()
        except:
            pass
        print("\n Demo演示结束")


if __name__ == "__main__":
    main() 