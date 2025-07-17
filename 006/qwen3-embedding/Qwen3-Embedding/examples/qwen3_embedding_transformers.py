#coding:utf8
# 导入必要的库
import os
from typing import Dict, Optional, List, Union
import torch
from torch import nn
import torch.nn.functional as F

from torch import Tensor
from transformers import AutoTokenizer, AutoModel
from transformers.utils import is_flash_attn_2_available
import numpy as np
from collections import defaultdict

class Qwen3Embedding:
    """
    Qwen3 嵌入模型类
    用于将文本转换为向量表示，支持查询和文档的编码
    """
    
    def __init__(self, model_name_or_path, instruction=None, use_fp16: bool = True, use_cuda: bool = False, max_length=8192):
        """
        初始化 Qwen3Embedding 模型
        
        Args:
            model_name_or_path: 模型路径或模型名称（如 "Qwen/Qwen3-Embedding-0.6B"）
            instruction: 默认指令，用于指导模型理解任务
            use_fp16: 是否使用半精度浮点数（float16）以节省显存
            use_cuda: 是否使用 GPU 加速
            max_length: 最大输入序列长度
        """
        # 设置默认指令，用于检索任务
        if instruction is None:
            instruction = '给定一个网络搜索查询，检索能够回答该查询的相关段落'
        self.instruction = instruction
        
        # 根据是否支持 Flash Attention 2 和是否使用 CUDA 来加载模型
        if is_flash_attn_2_available() and use_cuda:
            # 使用 Flash Attention 2 优化注意力计算，提高效率
            self.model = AutoModel.from_pretrained(
                model_name_or_path, 
                trust_remote_code=True, 
                # attn_implementation="flash_attention_2", 
                torch_dtype=torch.float16
            )
        else:
            # 使用标准注意力机制
            self.model = AutoModel.from_pretrained(
                model_name_or_path, 
                trust_remote_code=True, 
                torch_dtype=torch.float16
            )
        
        # 如果使用 CUDA，将模型移到 GPU 上
        if use_cuda:
            self.model = self.model.cuda()
            
        # 初始化分词器，设置左侧填充（适合生成任务）
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path, 
            trust_remote_code=True, 
            padding_side='left'
        )
        self.max_length = max_length
    
    def last_token_pool(self, last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
        """
        最后一个 token 的池化操作
        从序列的最后一个有效位置提取表示向量
        
        Args:
            last_hidden_states: 模型最后一层的隐藏状态 [batch_size, seq_len, hidden_size]
            attention_mask: 注意力掩码，标识哪些位置是有效的 token [batch_size, seq_len]
            
        Returns:
            池化后的向量表示 [batch_size, hidden_size]
        """
        # 检查是否使用了左侧填充
        left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
        
        if left_padding:
            # 如果是左侧填充，直接取最后一个位置的向量
            return last_hidden_states[:, -1]
        else:
            # 如果是右侧填充，需要找到每个序列的实际结束位置
            sequence_lengths = attention_mask.sum(dim=1) - 1  # 计算每个序列的实际长度
            batch_size = last_hidden_states.shape[0]
            # 提取每个序列最后一个真实token的向量表示
            return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]

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
            dim: 输出向量的维度，-1 表示使用完整维度
            
        Returns:
            标准化后的向量表示 [batch_size, hidden_size] 或 [batch_size, dim]
        """
        # 确保输入是列表格式
        if isinstance(sentences, str):
            sentences = [sentences]
            
        # 如果是查询文本，添加指令前缀
        if is_query:
            sentences = [self.get_detailed_instruct(instruction, sent) for sent in sentences]
            
        # 使用分词器处理输入文本
        inputs = self.tokenizer(
            sentences, 
            padding=True,           # 填充到相同长度
            truncation=True,        # 截断超长序列
            max_length=self.max_length, 
            return_tensors='pt'     # 返回PyTorch张量
        )
        
        # 将输入移到模型所在的设备（GPU/CPU）
        inputs.to(self.model.device)
        
        # 通过模型获取隐藏状态
        model_outputs = self.model(**inputs)
        
        # 使用最后token池化提取表示向量
        output = self.last_token_pool(model_outputs.last_hidden_state, inputs['attention_mask'])
        
        # 如果指定了维度，截取对应维度
        if dim != -1:
            # 设置为其他正整数，则只保留前 dim 个维度
            output = output[:, :dim]
            
        # L2 标准化，将向量标准化为单位向量（长度为1）
        # 统一量纲：消除向量长度差异，只保留方向信息
        output = F.normalize(output, p=2, dim=1)
        return output

# 主程序示例
if __name__ == "__main__":
    # 设置模型路径
    model_path = "C:/Users/86134/Desktop/qwen3/Qwen3-Embedding-0.6B"
    
    # 初始化嵌入模型
    model = Qwen3Embedding(model_path)
    
    # 定义查询和文档
    queries = ['中国的首都是什么？', '解释一下重力是什么？']
    documents = [
        "中国的首都是北京。",
        "重力是一种使两个物体相互吸引的力。它赋予物理物体重量，并负责行星围绕太阳运动的原因。"
    ]
    
    # 编码查询（设置 is_query=True 以添加指令前缀）
    query_outputs = model.encode(queries, is_query=True)
    
    # 编码文档（不需要指令前缀）
    doc_outputs = model.encode(documents)
    
    # 打印输出向量
    print('query outputs: \n', query_outputs)
    print('doc outputs: \n', doc_outputs)
    
    # 计算相似度得分（点积乘以100用于缩放）
    scores = (query_outputs @ doc_outputs.T) * 100
    print(f"相似度得分：{scores.tolist()}")
