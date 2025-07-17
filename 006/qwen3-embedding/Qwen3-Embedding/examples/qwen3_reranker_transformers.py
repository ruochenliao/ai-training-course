#coding:utf8
# 导入必要的库
import logging
from typing import Dict, Optional, List
import os

import json
import logging
import os
import queue
import sys

from collections import defaultdict
from contextlib import nullcontext
from dataclasses import dataclass, field
from pathlib import Path
from tqdm import tqdm
from typing import Union, List, Tuple, Any

import numpy as np
import torch
from torch import Tensor, nn
import torch.nn.functional as F
from torch.utils.data._utils.worker import ManagerWatchdog

from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSequenceClassification, AutoModel, is_torch_npu_available

# 设置日志记录器
logger = logging.getLogger(__name__)


class Qwen3Reranker:
    """
    Qwen3 重排序模型类
    用于对查询-文档对进行相关性评分，判断文档是否与查询相关
    """
    
    def __init__(
        self,
        model_name_or_path: str,
        max_length: int = 4096,
        instruction=None,
        attn_type='causal',
    ) -> None:
        """
        初始化 Qwen3Reranker 模型
        
        Args:
            model_name_or_path: 模型路径或模型名称（如 "Qwen/Qwen3-Reranker-0.6B"）
            max_length: 最大输入序列长度
            instruction: 默认指令，用于指导模型理解任务
            attn_type: 注意力类型（默认为因果注意力）
        """
        # 获取可用的GPU数量
        n_gpu = torch.cuda.device_count()
        self.max_length = max_length
        
        # 初始化分词器，设置左侧填充（适合生成任务）
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path, 
            trust_remote_code=True, 
            padding_side='left'
        )
        
        # 加载因果语言模型，使用 Flash Attention 2 优化和半精度浮点数
        self.lm = AutoModelForCausalLM.from_pretrained(
            model_name_or_path, 
            trust_remote_code=True, 
            torch_dtype=torch.float16, 
            # attn_implementation="flash_attention_2"
        ).cuda().eval()
        
        # 获取 "no" 和 "yes" 对应的 token ID，用于二分类判断
        self.token_false_id = self.tokenizer.convert_tokens_to_ids("no")
        self.token_true_id = self.tokenizer.convert_tokens_to_ids("yes")

        # 定义输入格式的前缀和后缀模板
        # 前缀：系统提示和用户输入开始标记
        self.prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
        # 后缀：用户输入结束和助手回复开始标记，包含思考过程
        self.suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"

        # 将前缀和后缀转换为 token ID，用于后续拼接
        self.prefix_tokens = self.tokenizer.encode(self.prefix, add_special_tokens=False)
        self.suffix_tokens = self.tokenizer.encode(self.suffix, add_special_tokens=False)
        
        # 设置默认指令
        self.instruction = instruction
        if self.instruction is None:
            self.instruction = "Given the user query, retrieval the relevant passages"

    def format_instruction(self, instruction, query, doc):
        """
        格式化指令、查询和文档为模型期望的输入格式
        
        Args:
            instruction: 任务指令
            query: 用户查询
            doc: 待评估的文档
            
        Returns:
            格式化后的输入字符串
        """
        # 如果没有提供指令，使用默认指令
        if instruction is None:
            instruction = self.instruction
        # 按照特定格式组合指令、查询和文档
        output = "<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}".format(
            instruction=instruction, query=query, doc=doc
        )
        return output

    def process_inputs(self, pairs):
        """
        处理输入对，进行分词、截断和填充
        
        Args:
            pairs: 格式化后的查询-文档对列表
            
        Returns:
            处理后的模型输入张量
        """
        # 对输入进行分词，不填充，使用最长优先截断策略
        out = self.tokenizer(
            pairs, 
            padding=False, 
            truncation='longest_first',
            return_attention_mask=False, 
            max_length=self.max_length - len(self.prefix_tokens) - len(self.suffix_tokens)
        )
        
        # 为每个输入添加前缀和后缀 token
        for i, ele in enumerate(out['input_ids']):
            out['input_ids'][i] = self.prefix_tokens + ele + self.suffix_tokens
            
        # 进行填充，确保批次内所有序列长度一致
        out = self.tokenizer.pad(out, padding=True, return_tensors="pt", max_length=self.max_length)
        
        # 将输入张量移动到模型所在的设备（GPU）
        for key in out:
            out[key] = out[key].to(self.lm.device)
        return out

    @torch.no_grad()
    def compute_logits(self, inputs, **kwargs):
        """
        计算模型输出的 logits 并转换为相关性分数，
        将相关性判断转化为二分类问题
        
        Args:
            inputs: 处理后的模型输入
            **kwargs: 其他参数
            
        Returns:
            相关性分数列表，值在 [0, 1] 之间
        """
        # 获取模型最后一个位置的logits（即预测下一个token的概率分布）
        # [:, -1, :] 提取最后一个位置的 logits
        # 第一个 : 表示所有批次
        # -1 表示序列的最后一个位置（即模型即将预测的下一个token）
        # 第二个 : 表示词汇表中的所有token
        batch_scores = self.lm(**inputs).logits[:, -1, :]
        
        # 提取 "yes" 和 "no" 对应位置的logits
        # 即：从整个词汇表的预测分数中，只提取这两个关键词的分数
        true_vector = batch_scores[:, self.token_true_id]
        false_vector = batch_scores[:, self.token_false_id]
        
        # 将false和true的logits堆叠成二分类格式
        # batch_scores.shape = [batch_size, 2]
        # 其中 [:, 0]是"no"的分数，[:, 1]是"yes"的分数
        batch_scores = torch.stack([false_vector, true_vector], dim=1)
        
        # 应用log_softmax进行归一化，将原始logits转换为对数概率
        # 数值稳定：使用log_softmax避免数值溢出
        batch_scores = torch.nn.functional.log_softmax(batch_scores, dim=1)
        
        # 取"yes"的概率（索引为1），并转换为普通概率值
        scores = batch_scores[:, 1].exp().tolist()
        return scores

    def compute_scores(
        self,
        pairs,
        instruction=None,
        **kwargs
    ):
        """
        计算查询-文档对的相关性分数
        
        Args:
            pairs: 查询-文档对的列表，每个元素为 (query, document) 元组
            instruction: 自定义指令（可选）
            **kwargs: 其他参数
            
        Returns:
            相关性分数列表，每个分数表示对应文档与查询的相关程度
        """
        # 将查询-文档对格式化为模型输入格式
        pairs = [self.format_instruction(instruction, query, doc) for query, doc in pairs]
        
        # 处理输入，进行分词和填充
        inputs = self.process_inputs(pairs)
        
        # 计算相关性分数
        scores = self.compute_logits(inputs)
        return scores


if __name__ == '__main__':
    """
    示例用法：演示如何使用 Qwen3Reranker 进行文档重排序
    """
    # 初始化重排序模型
    model = Qwen3Reranker(
        model_name_or_path='C:/Users/86134/Desktop/qwen3/Qwen3-Reranker-0.6B',
        instruction="检索能回答用户查询的文档", 
        max_length=2048
    )
    
    # 准备测试数据
    queries = ['中国的首都是什么？', '重力是什么？']
    documents = [
        "中国的首都是北京。",
        "重力是一种使两个物体相互吸引的力。它赋予物理物体重量，并负责行星围绕太阳运动的原因。"
    ]
    
    # 创建查询-文档对
    pairs = list(zip(queries, documents))
    
    # 设置任务指令
    instruction = "检索能回答用户查询的文档"
    
    # 计算相关性分数
    new_scores = model.compute_scores(pairs, instruction)
    print('相关性得分：', new_scores)