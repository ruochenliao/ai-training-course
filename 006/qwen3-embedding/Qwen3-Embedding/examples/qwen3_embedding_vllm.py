#coding:utf8
# 导入必要的库
from typing import Dict, Optional, List, Union
import torch
import vllm
from vllm import LLM
from vllm.distributed.parallel_state import destroy_model_parallel

class Qwen3EmbeddingVllm:
    """
    基于 vLLM 的 Qwen3 嵌入模型类
    使用 vLLM 框架来加速推理，适用于大规模文本嵌入任务
    """
    
    def __init__(self, model_name_or_path, instruction=None, max_length=8192):
        """
        初始化 Qwen3EmbeddingVllm 模型
        
        Args:
            model_name_or_path: 模型路径或模型名称（如 "Qwen/Qwen3-Embedding-0.6B"）
            instruction: 默认指令，用于指导模型理解任务
            max_length: 最大输入序列长度
        """
        # 设置默认指令，用于检索任务
        if instruction is None:
            instruction = 'Given a web search query, retrieve relevant passages that answer the query'
        self.instruction = instruction
        
        # 使用 vLLM 加载模型，指定任务类型为嵌入（embed）
        self.model = LLM(model=model_name_or_path, task="embed")

    def get_detailed_instruct(self, task_description: str, query: str) -> str:
        """
        构建详细的指令格式
        将任务描述和查询组合成模型期望的输入格式
        
        Args:
            task_description: 任务描述
            query: 用户查询
            
        Returns:
            格式化后的指令字符串
        """
        # 如果没有提供任务描述，使用默认指令
        if task_description is None:
            task_description = self.instruction
        return f'Instruct: {task_description}\nQuery:{query}'

    def encode(self, sentences: Union[List[str], str], is_query: bool = False, instruction=None, dim: int = -1):
        """
        将文本编码为向量表示
        
        Args:
            sentences: 输入文本，可以是字符串或字符串列表
            is_query: 是否为查询文本（查询需要添加指令前缀）
            instruction: 自定义指令（可选）
            dim: 输出向量的维度，-1 表示使用完整维度（当前未使用）
            
        Returns:
            向量表示 [batch_size, hidden_size]
        """
        # 确保输入是列表格式
        if isinstance(sentences, str):
            sentences = [sentences]
            
        # 如果是查询文本，添加指令前缀
        if is_query:
            sentences = [self.get_detailed_instruct(instruction, sent) for sent in sentences]
            
        # 使用 vLLM 进行嵌入推理
        output = self.model.embed(sentences)
        
        # 提取嵌入向量并转换为 PyTorch 张量
        output = torch.tensor([o.outputs.embedding for o in output])
        return output

    def stop(self):
        """
        停止模型并清理分布式并行状态
        释放 GPU 资源，避免内存泄漏
        """
        destroy_model_parallel()

if __name__ == "__main__":
    # 模型路径
    model_path = "C:/Users/86134/Desktop/qwen3/Qwen3-Embedding-0.6B"
    
    # 初始化模型
    model = Qwen3EmbeddingVllm(model_path)
    
    # 定义查询和文档
    queries = ['What is the capital of China?', 'Explain gravity']
    documents = [
        "The capital of China is Beijing.",
        "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun."
    ]
    
    # 编码查询（添加指令前缀）
    query_outputs = model.encode(queries, is_query=True)
    
    # 编码文档（不添加指令前缀）
    doc_outputs = model.encode(documents)
    
    # 打印输出结果
    print('query outputs', query_outputs)
    print('doc outputs', doc_outputs)
    
    # 计算相似度分数（查询与文档的余弦相似度 * 100）
    scores = (query_outputs @ doc_outputs.T) * 100
    print(scores.tolist())
    
    # 停止模型并清理资源
    model.stop()
