import logging

import json
import logging

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
logger = logging.getLogger(__name__)
from vllm import LLM, SamplingParams
from vllm.distributed.parallel_state import destroy_model_parallel
import gc
import math
from sentence_transformers import CrossEncoder, SentenceTransformer
from vllm.inputs.data import TokensPrompt


class Qwen3RerankerInferenceModel(CrossEncoder):
    """
    Qwen3重排序推理模型类
    
    该类继承自CrossEncoder，用于实现基于Qwen3模型的文档重排序功能。
    模型通过判断查询和文档的相关性来进行重排序，输出"yes"或"no"的概率分数。
    """
    
    def __init__(self, model_name, instruction="Given the user query, retrieval the relevant passages", **kwargs):
        """
        初始化Qwen3重排序推理模型
        
        Args:
            model_name (str): 模型名称或路径
            instruction (str): 默认指令，用于指导模型判断相关性
            **kwargs: 其他参数，包括max_length等
        """
        # 获取可用GPU数量，用于设置张量并行
        number_of_gpu = torch.cuda.device_count()
        
        # 设置默认指令
        self.instruction = instruction
        
        # 初始化分词器
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.padding_side = "left"  # 设置左填充
        self.tokenizer.pad_token = self.tokenizer.eos_token  # 使用结束符作为填充符
        
        # 定义后缀模板，用于生成思考过程
        self.suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
        
        # 设置最大长度，默认为8192
        self.max_length = kwargs.get('max_length', 8192)
        
        # 预编码后缀tokens，避免重复编码
        self.suffix_tokens = self.tokenizer.encode(self.suffix, add_special_tokens=False)
        
        # 缓存常用的token ID，提高效率
        self.true_token = self.tokenizer("yes", add_special_tokens=False).input_ids[0]  # "yes"对应的token ID
        self.false_token = self.tokenizer("no", add_special_tokens=False).input_ids[0]  # "no"对应的token ID
        
        # 配置采样参数
        self.sampling_params = SamplingParams(
            temperature=0,  # 设置为0以获得确定性输出
            top_p=0.95,     # 核采样参数
            max_tokens=1,   # 只生成一个token（yes或no）
            logprobs=20,    # 返回前20个token的对数概率
            allowed_token_ids=[self.true_token, self.false_token],  # 限制只能生成yes或no
        )
        
        # 初始化VLLM模型，支持多GPU并行推理
        self.lm = LLM(
            model=model_name, 
            tensor_parallel_size=number_of_gpu,  # 张量并行大小
            max_model_len=10000,                 # 最大模型长度
            enable_prefix_caching=True,          # 启用前缀缓存以提高效率
            distributed_executor_backend='ray',  # 使用Ray作为分布式后端
            gpu_memory_utilization=0.8           # GPU内存利用率
        )

    def format_instruction(self, instruction, query, doc):
        """
        格式化指令、查询和文档为模型输入格式
        
        Args:
            instruction (str): 指令文本
            query (str or tuple): 查询文本，如果是元组则第一个元素为指令，第二个为查询
            doc (str): 文档文本
            
        Returns:
            list: 格式化后的消息列表，包含系统消息和用户消息
        """
        # 如果query是元组，则提取指令和查询
        if isinstance(query, tuple):
            instruction = query[0]
            query = query[1]
            
        # 构建对话格式的消息
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

    def process_batch(self, pairs, **kwargs):
        """
        批量处理查询-文档对，计算相关性分数
        
        Args:
            pairs (list): 查询-文档对的列表，每个元素为(query, doc)元组
            **kwargs: 其他参数
            
        Returns:
            list: 相关性分数列表，每个分数表示对应文档与查询的相关程度
        """
        # 为每个查询-文档对格式化消息
        messages = [self.format_instruction(self.instruction, query, doc) for query, doc in pairs]
        
        # 应用聊天模板，将消息转换为token序列
        messages = self.tokenizer.apply_chat_template(
            messages, 
            tokenize=True,              # 进行分词
            add_generation_prompt=False, # 不添加生成提示
            enable_thinking=False       # 不启用思考模式
        )
        
        # 截断消息长度并添加后缀tokens
        messages = [ele[:self.max_length] + self.suffix_tokens for ele in messages]
        
        # 转换为TokensPrompt格式
        messages = [TokensPrompt(prompt_token_ids=ele) for ele in messages]
        
        # 使用VLLM生成输出
        outputs = self.lm.generate(messages, self.sampling_params, use_tqdm=False)
        
        scores = []
        # 处理每个输出，计算相关性分数
        for i in range(len(outputs)):
            # 获取最后一个token的对数概率分布
            final_logits = outputs[i].outputs[0].logprobs[-1]
            token_count = len(outputs[i].outputs[0].token_ids)
            
            # 获取"yes"token的对数概率，如果不存在则设为-10
            if self.true_token not in final_logits:
                true_logit = -10
            else:
                true_logit = final_logits[self.true_token].logprob
                
            # 获取"no"token的对数概率，如果不存在则设为-10
            if self.false_token not in final_logits:
                false_logit = -10
            else:
                false_logit = final_logits[self.false_token].logprob
            
            # 将对数概率转换为概率
            true_score = math.exp(true_logit)
            false_score = math.exp(false_logit)
            
            # 计算归一化的相关性分数（softmax）
            score = true_score / (true_score + false_score)
            scores.append(score)

        return scores

    def start(self):
        """
        启动模型（占位方法，用于兼容性）
        """
        pass

    def predict(
        self,
        sentences: list[tuple[str, str]] | list[list[str]],
        batch_size: int = None,
        show_progress_bar: bool | None = False,
        num_workers: int = 1,
        activation_fct = None,
        apply_softmax: bool | None = False,
        convert_to_numpy: bool = True,
        convert_to_tensor: bool = False,
        **kwargs
    ) -> list[torch.Tensor]:
        """
        预测方法，计算句子对的相关性分数
        
        Args:
            sentences: 句子对列表，每个元素为(query, doc)格式
            batch_size: 批处理大小（未使用，保持接口兼容性）
            show_progress_bar: 是否显示进度条（未使用）
            num_workers: 工作进程数（未使用）
            activation_fct: 激活函数（未使用）
            apply_softmax: 是否应用softmax（未使用，已在内部处理）
            convert_to_numpy: 是否转换为numpy数组（未使用）
            convert_to_tensor: 是否转换为tensor（未使用）
            **kwargs: 其他参数
            
        Returns:
            list: 相关性分数列表
        """
        # 调用批处理方法计算分数
        scores = self.process_batch(sentences)
        return scores

    def stop(self):
        """
        停止模型，清理分布式资源
        """
        # 销毁模型并行状态，释放GPU资源
        destroy_model_parallel()
