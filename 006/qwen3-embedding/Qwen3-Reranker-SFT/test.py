
import os
from FlagEmbedding import FlagAutoReranker

def test_finetuned_reranker():
    # 加载你的微调模型
    model = FlagAutoReranker.from_finetuned(
        model_name_or_path="/root/autodl-tmp/models/finetuned-qwen3-reranker",
        model_class="decoder-only-base",
        use_fp16=True,
        devices=["cuda:0"]
    )
    
    # 测试
    test_pairs = [
        ["什么是人工智能？", "人工智能（AI）是计算机科学的一个分支，致力于创建能够模拟人类智能行为的机器和软件系统。"],
        ["什么是人工智能？", "机器学习是一种统计方法"],
        ["如何预防感冒？", "预防感冒的方法包括：勤洗手、保持充足睡眠、均衡饮食、适量运动、避免接触感冒患者等。"],
        ["如何预防感冒？", "Python是编程语言"],
    ]
    
    scores = model.compute_score(test_pairs)
    
    print("测试结果:")
    for i, (query, passage) in enumerate(test_pairs):
        print(f"Query: {query}")
        print(f"Passage: {passage}")
        print(f"Score: {scores[i]:.4f}")
        print("-" * 50)

if __name__ == '__main__':
    test_finetuned_reranker()