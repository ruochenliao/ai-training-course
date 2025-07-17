from __future__ import annotations

import logging
import queue
import json
from collections.abc import Sequence
from contextlib import nullcontext
from typing import Any

from tqdm.autonotebook import tqdm
import numpy as np
import torch
from torch.utils.data._utils.worker import ManagerWatchdog
from transformers import AutoModel, AutoTokenizer
from transformers.tokenization_utils_base import BatchEncoding
from mteb.encoder_interface import PromptType
from mteb.models.wrapper import Wrapper
from mteb.model_meta import ModelMeta
import mteb

logger = logging.getLogger(__name__)


class TransformersTextEmbedder(torch.nn.Module):
    """
    基于Transformers的文本嵌入器
    
    这个类封装了Transformers模型，用于将文本转换为向量表示。
    支持多种池化策略和自定义配置。
    """
    
    def __init__(
        self,
        model: str,  # 模型名称或路径
        pooler_type: str = 'last',  # 池化类型：'last', 'first', 'mean'
        do_norm: bool = False,  # 是否对输出向量进行归一化
        truncate_dim: int = 0,  # 向量截断维度，0表示不截断
        padding_left: bool = False,  # 是否左填充
        attn_type: str = 'causal',  # 注意力类型
        **kwargs,  # 传递给模型的其他参数
    ):
        super().__init__()
        # 加载预训练模型和分词器
        self.base_model = AutoModel.from_pretrained(model, **kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(model, **kwargs)
        # 设置分词器的填充方向为左填充
        self.tokenizer.padding_side = "left"
        
        # 保存配置参数
        self.pooler_type = pooler_type
        self.do_norm = do_norm
        self.truncate_dim = truncate_dim
        self.padding_left = padding_left
        self.attn_type = attn_type
        
        # 根据池化类型选择对应的池化函数
        if pooler_type == 'first':
            assert padding_left is False  # first pooling不能使用左填充
            self.pooling = self._pooling_first
        elif pooler_type == 'last':
            self.pooling = self._pooling_last
        elif pooler_type == 'mean':
            self.pooling = self._pooling_mean
        else:
            ValueError(f"Wrong pooler : {self.pooler_type}")

    def embed(
        self, 
        sentences: Sequence[str],  # 输入文本序列
        max_length: int,  # 最大序列长度
        prompt: str | None = None,  # 可选的提示词前缀
        device: str | torch.device = 'cpu',  # 计算设备
    ) -> torch.Tensor:
        """
        将文本序列编码为嵌入向量
        
        Args:
            sentences: 输入的文本序列
            max_length: 最大序列长度
            prompt: 可选的提示词前缀
            device: 计算设备
            
        Returns:
            编码后的嵌入向量张量
        """
        # 分词并移动到指定设备
        inputs = self.tokenize(sentences, max_length, prompt).to(device)
        # 前向传播获取嵌入向量
        embeddings = self.forward(**inputs.data)
        return embeddings

    def tokenize(self, texts, max_length: int, prompt=None) -> BatchEncoding:
        """
        对文本进行分词处理
        
        Args:
            texts: 输入文本
            max_length: 最大序列长度
            prompt: 可选的提示词前缀
            
        Returns:
            分词后的BatchEncoding对象
        """
        # 如果有提示词，将其添加到每个文本前面
        if prompt:
            texts = [prompt + t for t in texts] 
        # 使用分词器处理文本，启用填充和截断
        inputs = self.tokenizer(texts, padding=True, truncation=True, max_length=max_length, return_tensors='pt')
        return inputs

    def forward(
        self,
        input_ids: torch.LongTensor,  # 输入的token ID
        attention_mask: torch.Tensor,  # 注意力掩码
        **kwargs
    ) -> torch.Tensor:
        """
        前向传播函数
        
        Args:
            input_ids: 输入的token ID张量
            attention_mask: 注意力掩码张量
            **kwargs: 其他参数
            
        Returns:
            处理后的嵌入向量
        """
        # 通过基础模型获取隐藏状态
        output = self.base_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True,
            **kwargs
        )
        # 应用池化策略
        embeddings = self.pooling(output.last_hidden_state, attention_mask)
        
        # 如果指定了截断维度，则截断向量
        if self.truncate_dim > 0:
            embeddings = embeddings[:, :self.truncate_dim]
            
        # 如果需要归一化，则进行L2归一化
        if self.do_norm:
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        return embeddings

    @staticmethod
    def _pooling_last(hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """
        最后一个token的池化策略
        
        根据填充方向自动选择合适的最后token位置
        """
        mask = attention_mask
        # 检查是否为左填充
        left_padding = (mask[:, -1].sum() == mask.shape[0])
        if left_padding:
            # 左填充时直接取最后一个位置
            return hidden_state[:, -1]
        else:
            # 右填充时需要根据序列长度计算实际的最后位置
            sequence_lengths = mask.sum(dim=1) - 1
            batch_size = hidden_state.shape[0]
            return hidden_state[torch.arange(batch_size, device=hidden_state.device), sequence_lengths]

    @staticmethod
    def _pooling_first(hidden_state: torch.Tensor, _) -> torch.Tensor:
        """
        第一个token的池化策略（通常是CLS token）
        """
        return hidden_state[:, 0]

    @staticmethod
    def _pooling_last_left(hidden_state: torch.Tensor, _) -> torch.Tensor:
        """
        左填充时的最后token池化（直接取最后一个位置）
        """
        return hidden_state[:, -1]

    @staticmethod
    def _pooling_last_right(hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """
        右填充时的最后token池化（根据注意力掩码计算实际位置）
        """
        last_indices = attention_mask.sum(1) - 1  # 计算每个序列的最后有效位置
        batch_indices = torch.arange(hidden_state.size(0), device=hidden_state.device)
        pooled_output = hidden_state[batch_indices, last_indices]
        return pooled_output

    @staticmethod
    def _pooling_mean(hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """
        平均池化策略
        
        对所有有效token的隐藏状态进行加权平均
        """
        assert attention_mask.ndim == 2, f"Unexpected {attention_mask.ndim=}"
        attention_mask = attention_mask.float()
        lengths = attention_mask.sum(1)  # 计算每个序列的有效长度
        # 使用einsum进行加权平均计算
        pooled_output = torch.einsum('bsh,bs,b->bh', (hidden_state.float(), attention_mask, 1 / lengths))
        return pooled_output


def _encode_loop(
    model: TransformersTextEmbedder,  # 嵌入模型
    input_queue,  # 输入队列
    output_queue,  # 输出队列
    device: torch.device,  # 计算设备
    qsize: int = 4,  # 队列大小
    amp_dtype=None  # 混合精度数据类型
):
    """
    多进程编码循环函数
    
    这个函数在独立的进程中运行，从输入队列获取数据，
    进行编码处理后将结果放入输出队列。
    """
    # 将模型移动到指定设备
    model = model.to(device)
    # 创建进程监视器
    watchdog = ManagerWatchdog()
    # 创建保持队列，用于内存管理
    keep_queue = queue.Queue(qsize + 1)

    # 启用推理模式以提高性能
    with torch.inference_mode():
        # 如果指定了混合精度类型，则启用自动混合精度
        with torch.autocast(
            device_type=device.type, dtype=amp_dtype
        ) if amp_dtype is not None else nullcontext():
            # 持续处理队列中的数据，直到进程被终止
            while watchdog.is_alive():
                r = input_queue.get()
                if r is None:  # 接收到终止信号
                    break

                n, inputs = r  # 解包批次编号和输入数据
                # 进行编码
                embeddings = model.embed(*inputs, device=device)
                # 将结果放入输出队列
                output_queue.put((n, embeddings))
                
                # 内存管理：维护固定大小的缓存队列
                if keep_queue.full():
                    i = keep_queue.get()
                    del i
                keep_queue.put(embeddings)
                del r, n, inputs

    # 清理内存
    while not keep_queue.empty():
        i = keep_queue.get()
        del i
    del model, watchdog
    return


class Qwen3Embedding(Wrapper):
    """
    Qwen3嵌入模型包装器
    
    这个类实现了MTEB接口，用于评估Qwen3嵌入模型的性能。
    支持多GPU并行处理、指令感知和多种精度模式。
    """
    _model_class = TransformersTextEmbedder
    # `_model_class` 需要实现 `embed(batch, max_length, prompt_name, self.device)` 方法

    def __init__(
        self,
        model: str,  # 模型名称或路径
        use_instruction: bool = False,  # 是否使用指令
        device: str = 'cuda',  # 计算设备
        max_length: int = 512,  # 默认最大长度
        max_query_length: int | None = None,  # 查询的最大长度
        max_doc_length: int | None = None,  # 文档的最大长度
        precision: str = 'fp32',  # 精度模式：'fp32', 'fp16', 'bf16', 'amp_fp16', 'amp_bf16'
        mp_qsize: int = 4,  # 多进程队列大小
        instruction_dict_path=None,  # 指令字典文件路径
        instruction_template=None,  # 指令模板
        **kwargs,  # 传递给TransformersTextEmbedder的其他参数
    ) -> None:
        
        # 从模型路径中提取模型名称
        model_name = model.split('/')
        if model_name[-1] == '':
            model_name = model_name[-2]
        else:
            model_name = model_name[-1]
        model_name = kwargs.pop('model_name', model_name)
        
        # 初始化嵌入模型
        self.model = self._model_class(model, **kwargs)
        
        # 设置MTEB模型元信息
        self.mteb_model_meta = ModelMeta(
            name=model_name, revision=kwargs.get('revision', None), release_date=None, 
            languages=None, n_parameters=None, memory_usage_mb=None, max_tokens=None, 
            embed_dim=None, license=None, open_weights=False, public_training_code=None, 
            public_training_data=None, framework=["Sentence Transformers"], 
            similarity_fn_name="cosine", use_instructions=True, training_datasets=None
        )

        # 保存配置参数
        self.use_instruction = use_instruction
        self.device = device
        self.max_query_length = max_query_length or max_length
        self.max_doc_length = max_doc_length or max_length
        self.amp_dtype = None
        
        # 根据精度模式设置模型精度
        if precision == 'fp16':
            self.model.half()  # 转换为半精度
        elif precision == 'bf16':
            self.model.bfloat16()  # 转换为bfloat16
        elif precision.startswith('amp_'):
            # 设置自动混合精度类型
            self.amp_dtype = torch.float16 if precision.endswith('fp16') else torch.bfloat16
            
        self.mp_qsize = mp_qsize
        
        # 检查GPU数量并初始化多进程相关变量
        n_gpu = torch.cuda.device_count()
        self.world_size = n_gpu
        assert n_gpu > 0, 'woho, no no no!'  # 确保有可用的GPU
        logger.info(f"We have {n_gpu=}, good.")
        
        # 初始化多进程队列和工作进程列表
        self._input_queues = list()
        self._output_queues = list()
        self._workers = list()
        
        # 初始化指令字典
        self.instruction_dict = dict()
        if instruction_dict_path is not None:
            instruction_dict_path = instruction_dict_path
            with open(instruction_dict_path) as f:
                self.instruction_dict = json.load(f)
        if instruction_template is not None:
            self.instruction_template = instruction_template

    def get_instruction(self, task_name, prompt_type):
        """
        根据任务名称和提示类型获取相应的指令
        
        Args:
            task_name: 任务名称
            prompt_type: 提示类型（如'query', 'passage'等）
            
        Returns:
            对应的指令字符串
        """
        sym_task = False
        
        # 首先检查自定义指令字典
        if task_name in self.instruction_dict:
            instruction = self.instruction_dict[task_name]
            if isinstance(instruction, dict):
                instruction = instruction.get(prompt_type, "")
                sym_task = True
        else:
            # 使用父类的默认指令获取方法
            instruction = super().get_instruction(task_name, prompt_type)
            
        # 获取任务类型
        task_type = mteb.get_tasks(tasks=[task_name])[0].metadata.type
        
        # 对于检索任务的特殊处理
        if 'Retrieval' in task_type and not sym_task and prompt_type != 'query':
            return ""
            
        # 根据任务类型设置默认指令
        if task_type in ["STS", "PairClassification"]:
            return "Retrieve semantically similar text"
        if task_type in "Bitext Mining":
            return "Retrieve parallel sentences"
        if 'Retrieval' in task_type and prompt_type == 'query' and instruction is None:
            instruction = "Retrieval relevant passage for the given query."
            
        return instruction
        
    def format_instruction(self, instruction, prompt_type):
        """
        格式化指令文本
        
        Args:
            instruction: 原始指令
            prompt_type: 提示类型
            
        Returns:
            格式化后的指令
        """
        if instruction is not None and len(instruction.strip()) > 0:
            instruction = self.instruction_template.format(instruction)
            return instruction
        return ""

    def encode(
        self,
        sentences: Sequence[str],  # 输入文本序列
        *,
        task_name: str,  # 任务名称
        prompt_type: PromptType | None = None,  # 提示类型
        batch_size: int = 32,  # 批处理大小
        show_progress_bar: bool = True,  # 是否显示进度条
        **kwargs: Any,  # 其他参数
    ) -> np.ndarray:
        """
        编码文本序列为嵌入向量
        
        这是主要的编码接口，支持批处理和多进程并行处理。
        
        Args:
            sentences: 输入的文本序列
            task_name: 任务名称，用于确定指令
            prompt_type: 提示类型，用于确定是查询还是文档
            batch_size: 批处理大小
            show_progress_bar: 是否显示进度条
            
        Returns:
            numpy数组形式的嵌入向量
        """
        instruction = None
        
        # 如果启用了指令功能，获取相应的指令
        if self.use_instruction:
            instruction = self.get_instruction(task_name, prompt_type)
            if self.instruction_template:
                instruction = self.format_instruction(instruction, prompt_type)
            logger.info(f"Using instruction: '{instruction}' for task: '{task_name}'")

        num_texts = len(sentences)
        logger.info(f"Encoding {num_texts} sentences.")
        num_batches = num_texts // batch_size + int(num_texts % batch_size > 0)

        def _receive(oq, timeout=0.00125):
            """
            从输出队列接收结果的内部函数
            """
            try:
                n, embed = oq.get(timeout=timeout)
                result_dict[n] = embed.cpu()  # 将结果移到CPU并保存
                pbar.update(1)  # 更新进度条
                del embed  # 释放GPU内存
            except queue.Empty:
                pass

        # 根据提示类型选择最大长度
        max_length = self.max_query_length if prompt_type == PromptType.query else self.max_doc_length

        # 初始化进度条和结果字典
        pbar = tqdm(
            total=num_batches, disable=not show_progress_bar, desc='encode',
            mininterval=1, miniters=10
        )
        result_dict = dict()
        
        # 如果没有工作进程，直接在当前进程中处理
        if not self._workers:
            self.model.to(self.device)

        # 根据是否有工作进程选择不同的上下文管理器
        with nullcontext() if self._workers else torch.inference_mode():
            with nullcontext() if self._workers or self.amp_dtype is None else torch.autocast(
                device_type=self.device, dtype=self.amp_dtype
            ):
                # 分批处理文本
                for n, i in enumerate(range(0, num_texts, batch_size)):
                    batch = sentences[i: i + batch_size]
                    if self._workers:
                        # 多进程模式：将任务分发到不同的GPU
                        rank = n % self.world_size
                        self._input_queues[rank].put((n, (batch, max_length, instruction)))
                        # 当有足够的批次时开始接收结果
                        if n >= self.world_size:
                            _receive(self._output_queues[rank])
                    else:
                        # 单进程模式：直接处理
                        result_dict[n] = self.model.embed(batch, max_length, instruction, self.device)
                        pbar.update(1)
                        
        # 多进程模式：接收剩余的结果
        if self._workers:
            while len(result_dict) < num_batches:
                for oq in self._output_queues:
                    _receive(oq)

        pbar.close()
        
        # 按顺序合并结果
        results = [result_dict[n] for n in range(len(result_dict))]
        embeddings = torch.cat(results).float()
        assert embeddings.shape[0] == num_texts
        embeddings = embeddings.cpu().numpy()
        return embeddings

    def start(self):
        """
        启动多进程工作模式
        
        为每个GPU创建一个独立的工作进程，用于并行处理编码任务。
        """
        # 使模型在进程间共享内存
        self.model.share_memory()
        logger.warning(f"Starting {self.world_size} worker processes.")
        
        # 使用spawn方式创建多进程上下文
        mp_ctx = torch.multiprocessing.get_context('spawn')
        
        # 为每个GPU创建输入和输出队列
        self._input_queues = [mp_ctx.Queue(self.mp_qsize) for _ in range(self.world_size)]
        self._output_queues = [mp_ctx.Queue(self.mp_qsize) for _ in range(self.world_size)]
        self._workers = list()
        
        # 为每个GPU创建一个工作进程
        for i, (iq, oq) in enumerate(zip(self._input_queues, self._output_queues)):
            device = torch.device(f'cuda:{i}')
            encode_worker = mp_ctx.Process(
                target=_encode_loop, name=f'encode_{i}', args=(
                    self.model, iq, oq, device, self.mp_qsize, self.amp_dtype
                )
            )
            encode_worker.start()
            self._workers.append(encode_worker)
            logger.warning(f"GPU {i} worker initiated.")

    def stop(self):
        """
        停止多进程工作模式
        
        向所有工作进程发送终止信号，等待进程结束并清理资源。
        """
        # 向所有输入队列发送终止信号
        [q.put(None) for q in self._input_queues]
        # 等待所有工作进程结束
        [w.join() for w in self._workers]
        # 关闭所有工作进程
        [w.close() for w in self._workers]
        # 清理队列
        for qs in (self._input_queues, self._output_queues):
            [q.put(None) for q in qs]
