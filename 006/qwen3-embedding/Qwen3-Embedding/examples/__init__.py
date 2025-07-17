try:
    from .qwen3_embedding_vllm import Qwen3EmbeddingVllm
    from .qwen3_reranker_vllm import Qwen3Rerankervllm
    from .qwen3_embedding_transformers import Qwen3Embedding
    from .qwen3_reranker_transformers import Qwen3Reranker
    
    __all__ = [
        'Qwen3EmbeddingVllm',
        'Qwen3Rerankervllm',
        'Qwen3Embedding',
        'Qwen3Reranker'
    ]
except ImportError as e:
    # 如果某些依赖不可用，仍然允许包被导入
    print(f"Warning: Some modules could not be imported: {e}")
    __all__ = []
