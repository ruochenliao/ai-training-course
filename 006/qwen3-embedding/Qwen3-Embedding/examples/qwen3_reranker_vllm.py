#coding:utf8

import logging  # 用于记录运行时信息和调试
import json     # 用于处理JSON格式数据

import logging

from collections import defaultdict  # 提供默认值的字典，避免KeyError
from contextlib import nullcontext    # 提供空上下文管理器，用于条件性上下文管理
from dataclasses import dataclass, field  # 用于创建数据类，简化类定义
from pathlib import Path            # 面向对象的文件系统路径操作
from tqdm import tqdm              # 进度条显示库，用于显示长时间运行任务的进度
from typing import Union, List, Tuple, Any  # 类型注解，提高代码可读性和IDE支持

import numpy as np            

import torch                   
from torch import Tensor, nn    
import torch.nn.functional as F   
from torch.utils.data._utils.worker import ManagerWatchdog  # PyTorch数据加载器的工作进程监控

from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSequenceClassification, AutoModel, is_torch_npu_available

# 设置日志记录器
logger = logging.getLogger(__name__)

# 导入 vLLM 相关库
from vllm import LLM, SamplingParams
from vllm.distributed.parallel_state import destroy_model_parallel
import gc
import math
from sentence_transformers import CrossEncoder, SentenceTransformer
from vllm.inputs.data import TokensPrompt


class Qwen3Rerankervllm(CrossEncoder):
    """
    基于 vLLM 的 Qwen3 重排序模型类
    继承自 CrossEncoder，使用 vLLM 框架来加速推理
    用于对查询-文档对进行相关性评分，判断文档是否与查询相关
    """
    
    def __init__(self, model_name_or_path, instruction="Given the user query, retrieval the relevant passages", **kwargs):
        """
        初始化 Qwen3Rerankervllm 模型
        
        Args:
            model_name_or_path: 模型路径或模型名称（如 "Qwen/Qwen3-Reranker-0.6B"）
            instruction: 默认指令，用于指导模型理解任务
            **kwargs: 其他参数，如 max_length
        """
        # 获取可用的 GPU 数量，用于张量并行
        number_of_gpu = torch.cuda.device_count()
        
        # 设置默认指令
        self.instruction = instruction
        
        # 初始化分词器，设置左侧填充
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.tokenizer.padding_side = "left"  # 左侧填充，适合生成任务
        self.tokenizer.pad_token = self.tokenizer.eos_token  # 使用结束符作为填充符
        
        # 定义后缀模板，用于生成任务的提示格式
        self.suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
        
        # 设置最大序列长度
        self.max_length = kwargs.get('max_length', 8192)
        
        # 将后缀转换为 token IDs
        self.suffix_tokens = self.tokenizer.encode(self.suffix, add_special_tokens=False)
        
        # 获取 "yes" 和 "no" 对应的 token ID，用于二分类判断
        self.true_token = self.tokenizer("yes", add_special_tokens=False).input_ids[0]
        self.false_token = self.tokenizer("no", add_special_tokens=False).input_ids[0]
        
        # 配置采样参数
        self.sampling_params = SamplingParams(
            temperature=0,  # 温度为0，确保确定性输出
            top_p=0.95,     # 核采样参数
            max_tokens=1,   # 只生成一个 token（yes 或 no）
            logprobs=20,    # 返回前20个 token 的对数概率
            allowed_token_ids=[self.true_token, self.false_token],  # 只允许输出 yes 或 no
        )
        
        # 初始化 vLLM 模型
        self.lm = LLM(
            model=model_name_or_path, 
            tensor_parallel_size=number_of_gpu,  # 张量并行大小
            max_model_len=10000,                 # 最大模型长度
            enable_prefix_caching=True,          # 启用前缀缓存以提高效率
            distributed_executor_backend='ray',  # 使用 Ray 作为分布式后端
            gpu_memory_utilization=0.8           # GPU 内存利用率
        )

    def format_instruction(self, instruction, query, doc):
        """
        格式化指令，将查询和文档组合成模型期望的输入格式
        
        Args:
            instruction: 任务指令
            query: 用户查询，可能是元组格式 (instruction, query)
            doc: 文档内容
            
        Returns:
            格式化后的消息列表，符合聊天模板格式
        """
        # 如果查询是元组格式，提取指令和查询
        if isinstance(query, tuple):
            instruction = query[0]
            query = query[1]
            
        # 构建聊天格式的消息
        text = [
            {
                "role": "system", 
                "content": "Judge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\"."
            },
            {
                "role": "user", 
                "content": f"<Instruct>: {instruction}\n\n<Query>: {query}\n\n<Document>: {doc}"
            }
        ]
        return text

    def compute_scores(self, pairs, **kwargs):
        """
        计算查询-文档对的相关性分数
        
        Args:
            pairs: 查询-文档对的列表，每个元素为 (query, document) 元组
            **kwargs: 其他参数
            
        Returns:
            相关性分数列表，每个分数在 [0, 1] 范围内
        """
        # 为每个查询-文档对格式化指令
        messages = [self.format_instruction(self.instruction, query, doc) for query, doc in pairs]
        
        # 应用聊天模板，将消息转换为 token IDs
        messages = self.tokenizer.apply_chat_template(
            messages, 
            tokenize=True,              # 转换为 token IDs
            add_generation_prompt=False, # 不添加生成提示
            enable_thinking=False       # 不启用思考模式
        )
        
        # 截断到最大长度并添加后缀 tokens
        messages = [ele[:self.max_length] + self.suffix_tokens for ele in messages]
        
        # 转换为 TokensPrompt 格式
        messages = [TokensPrompt(prompt_token_ids=ele) for ele in messages]
        
        # 使用 vLLM 生成输出
        outputs = self.lm.generate(messages, self.sampling_params, use_tqdm=False)
        
        scores = []
        # 处理每个输出，计算相关性分数
        for i in range(len(outputs)):
            # 获取最后一个 token 的对数概率分布
            final_logits = outputs[i].outputs[0].logprobs[-1]
            token_count = len(outputs[i].outputs[0].token_ids)
            
            # 获取 "yes" token 的对数概率
            if self.true_token not in final_logits:
                true_logit = -10  # 如果没有找到，设置为很小的值
            else:
                true_logit = final_logits[self.true_token].logprob
                
            # 获取 "no" token 的对数概率
            if self.false_token not in final_logits:
                false_logit = -10  # 如果没有找到，设置为很小的值
            else:
                false_logit = final_logits[self.false_token].logprob
            
            # 将对数概率转换为概率
            true_score = math.exp(true_logit)
            false_score = math.exp(false_logit)
            
            # 计算归一化的相关性分数（softmax）
            score = true_score / (true_score + false_score)
            scores.append(score)

        return scores

    def stop(self):
        """
        停止模型并清理资源
        销毁模型并行状态，释放 GPU 内存
        """
        destroy_model_parallel()


if __name__ == '__main__':
    """
    主函数：演示如何使用 Qwen3Rerankervllm 模型
    """
    # 初始化重排序模型
    model = Qwen3Rerankervllm(
        model_name_or_path='/root/autodl-tmp/models/Qwen3-Reranker-0.6B', 
        instruction="Retrieval document that can answer user's query", 
        max_length=2048
    )
    
    # 准备测试数据
    queries = ['What is the capital of China?', 'Explain gravity']
    documents = [
        "The capital of China is Beijing.",
        "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun."
    ]
    
    # 创建查询-文档对
    pairs = list(zip(queries, documents))
    
    # 计算相关性分数
    new_scores = model.compute_scores(pairs)
    print('scores', new_scores)
    
    # 停止模型并清理资源
    model.stop()
