# 导入必要的库
import json
import sys
import logging
import os
from dataclasses import dataclass, field
from functools import partial
from typing import Optional, Any

import torch
from transformers import HfArgumentParser
import mteb
from pathlib import Path
from mteb import AbsTaskRetrieval,RetrievalEvaluator
from time import time
from mteb.models.sentence_transformer_wrapper import SentenceTransformerWrapper
import csv
from mteb.benchmarks.benchmarks import Benchmark
from qwen3_embedding_model import Qwen3Embedding
from utils import *

# 配置日志记录器，设置日志格式和级别
logging.basicConfig(
    format="%(levelname)s|%(asctime)s|%(name)s#%(lineno)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
    level=logging.INFO
)
logger = logging.getLogger('run_mteb.py')


# 定义 RARB 任务列表，包含各种推理和问答任务
RARB_tasks = [ "ARCChallenge",
            "AlphaNLI",
            "HellaSwag",
            "WinoGrande",
            "PIQA",
            "SIQA",
            "Quail",
            "SpartQA",
            "TempReasonL1",
            "TempReasonL2Pure",
            "TempReasonL2Fact",
            "TempReasonL2Context",
            "TempReasonL3Pure",
            "TempReasonL3Fact",
            "TempReasonL3Context",
            "RARbCode",
            "RARbMath",
        ]

def evaluate(
    self,
    model,
    split: str = "test",
    subsets_to_run: list | None = None,
    *,
    encode_kwargs: dict[str, Any] = {},
    **kwargs,
):
    """
    评估检索任务的主要方法
    
    Args:
        model: 用于检索的模型
        split: 数据集分割（默认为 "test"）
        subsets_to_run: 要运行的子集列表
        encode_kwargs: 编码参数字典
        **kwargs: 其他关键字参数
    
    Returns:
        scores: 各子集的评估分数字典
    """
    # 创建检索评估器
    retriever = RetrievalEvaluator(
        retriever=model,
        task_name=self.metadata.name,
        encode_kwargs=encode_kwargs,
        **kwargs,
    )
    scores = {}
    
    # 获取要评估的子集列表
    hf_subsets = list(self.hf_subsets) if self.is_multilingual else ["default"]
    if subsets_to_run is not None:
        hf_subsets = [s for s in hf_subsets if s in subsets_to_run]
    
    # 对每个子集进行评估
    for hf_subset in hf_subsets:
        logger.info(f"Subset: {hf_subset}")
        
        # 根据子集类型获取相应的数据
        if hf_subset == "default":
            corpus, queries, relevant_docs = (
                self.corpus[split],
                self.queries[split],
                self.relevant_docs[split],
            )
        else:
            corpus, queries, relevant_docs = (
                self.corpus[hf_subset][split],
                self.queries[hf_subset][split],
                self.relevant_docs[hf_subset][split],
            )
        
        # 评估当前子集
        scores[hf_subset] = self._evaluate_subset(
            retriever, corpus, queries, relevant_docs, hf_subset, split=split, **kwargs
        )
    return scores

def _evaluate_subset(
    self, retriever, corpus, queries, relevant_docs, hf_subset: str, **kwargs
):
    """
    评估单个子集的内部方法
    
    Args:
        retriever: 检索评估器
        corpus: 文档语料库
        queries: 查询集合
        relevant_docs: 相关文档
        hf_subset: 子集名称
        **kwargs: 其他关键字参数
    
    Returns:
        scores: 评估分数字典
    """
    # 记录开始时间
    start_time = time()
    # 执行检索
    results = retriever(corpus, queries)
    # 记录结束时间
    end_time = time()

    # 检查是否需要保存预测结果或导出错误
    save_predictions = kwargs.get("save_predictions", False)
    export_errors = kwargs.get("export_errors", False)
    if save_predictions or export_errors:
        output_folder = Path(kwargs.get("output_folder", "results"))
        if not os.path.isdir(output_folder):
            os.makedirs(output_folder)

    # 保存预测结果
    if save_predictions:
        top_k = kwargs.get("top_k", None)
        # 如果指定了 top_k，则只保留前 k 个结果
        if top_k is not None:
            for qid in list(results.keys()):
                doc_ids = set(
                    sorted(
                        results[qid], key=lambda x: results[qid][x], reverse=True
                    )[:top_k]
                )
                results[qid] = {
                    k: v for k, v in results[qid].items() if k in doc_ids
                }
        
        # 构建保存路径
        split = kwargs.get('split', 'test')
        if split != 'test':
            qrels_save_path = (
                output_folder / f"{self.metadata.name}_{hf_subset}_{split}_predictions.json"
            )
        else:
            qrels_save_path = (
                output_folder / f"{self.metadata.name}_{hf_subset}_predictions.json"
            )

        # 保存预测结果到 JSON 文件
        with open(qrels_save_path, "w") as f:
            json.dump(results, f)

    # 计算各种评估指标
    ndcg, _map, recall, precision, naucs = retriever.evaluate(
        relevant_docs,
        results,
        retriever.k_values,
        ignore_identical_ids=self.ignore_identical_ids,
    )
    # 计算 MRR（平均倒数排名）指标
    mrr, naucs_mrr = retriever.evaluate_custom(
        relevant_docs, results, retriever.k_values, "mrr"
    )
    
    # 整合所有评估分数
    scores = {
        **{f"ndcg_at_{k.split('@')[1]}": v for (k, v) in ndcg.items()},
        **{f"map_at_{k.split('@')[1]}": v for (k, v) in _map.items()},
        **{f"recall_at_{k.split('@')[1]}": v for (k, v) in recall.items()},
        **{f"precision_at_{k.split('@')[1]}": v for (k, v) in precision.items()},
        **{f"mrr_at_{k.split('@')[1]}": v for (k, v) in mrr.items()},
        **{
            k.replace("@", "_at_").replace("_P", "_precision").lower(): v
            for k, v in naucs.items()
        },
        **{
            k.replace("@", "_at_").replace("_P", "_precision").lower(): v
            for k, v in naucs_mrr.items()
        },
    }
    # 添加主要分数
    self._add_main_score(scores)

    # 导出错误分析
    if export_errors:
        errors = {}

        top_k = kwargs.get("top_k", 1)
        # 如果没有保存预测结果且 top_k 为 1，则只保留最高分的文档
        if not save_predictions and top_k == 1:
            for qid in results.keys():
                doc_scores = results[qid]
                sorted_docs = sorted(
                    doc_scores.items(), key=lambda x: x[1], reverse=True
                )[:top_k]
                results[qid] = dict(sorted_docs)
        
        # 分析每个查询的错误
        for qid, retrieved_docs in results.items():
            expected_docs = relevant_docs[qid]
            # 找出假阳性（检索到但不相关的文档）
            false_positives = [
                doc for doc in retrieved_docs if doc not in expected_docs
            ]
            # 找出假阴性（相关但未检索到的文档）
            false_negatives = [
                doc for doc in expected_docs if doc not in retrieved_docs
            ]
            # 如果存在错误，记录下来
            if false_positives or false_negatives:
                errors[qid] = {
                    "false_positives": false_positives,
                    "false_negatives": false_negatives,
                }
        
        # 构建错误文件保存路径
        split = kwargs.get('split', 'test')
        if split != 'test':
            errors_save_path = (
                output_folder / f"{self.metadata.name}_{hf_subset}_{split}_errors.json"
            )
        else:
            errors_save_path = (
                output_folder / f"{self.metadata.name}_{hf_subset}_errors.json"
            )
        
        # 保存错误分析到 JSON 文件
        with open(errors_save_path, "w") as f:
            json.dump(errors, f)

    return scores

# 将自定义的评估方法绑定到 AbsTaskRetrieval 类
AbsTaskRetrieval.evaluate = evaluate
AbsTaskRetrieval._evaluate_subset = _evaluate_subset

@dataclass
class EvalArguments:
    """
    评估参数的数据类，定义了所有可配置的评估选项
    """
    model: Optional[str] = field(
        default=None,
        metadata={"help": "预训练模型的路径或来自 huggingface.co/models 的模型标识符"}
    )
    model_name: Optional[str] = field(
        default=None,
        metadata={"help": "用于保存路径的模型名称"}
    )
    model_kwargs: Optional[str] = field(
        default=None,
        metadata={"help": "特定的模型参数，JSON 字符串格式"},
    )
    encode_kwargs: Optional[str] = field(
        default=None,
        metadata={"help": "特定的编码参数，JSON 字符串格式"},
    )
    run_kwargs: Optional[str] = field(
        default=None,
        metadata={"help": "`MTEB.run()` 的特定参数，JSON 字符串格式"},
    )

    output_dir: Optional[str] = field(default='results', metadata={"help": "结果输出目录"})
    benchmark: Optional[str] = field(default=None, metadata={"help": "基准测试名称"})
    tasks: Optional[str] = field(default=None, metadata={"help": "逗号分隔的任务列表"})
    langs: Optional[str] = field(default=None, metadata={"help": "逗号分隔的语言列表"})
    only_load: bool = field(default=False, metadata={"help": "是否只加载数据"})
    load_model: bool = field(default=False, metadata={"help": "在 only_load 模式下是否加载模型"})

    batch_size: int = field(default=128, metadata={"help": "批处理大小，将设置到 encode_kwargs 中"})
    precision: str = field(default='fp16', metadata={"help": "精度设置：amp_fp16,amp_bf16,fp16,bf16,fp32"})

    def __post_init__(self):
        """
        初始化后处理方法，用于解析字符串参数
        """
        # 解析任务列表
        if isinstance(self.tasks, str):
            self.tasks = self.tasks.split(',')
        # 解析语言列表
        if isinstance(self.langs, str):
            self.langs = self.langs.split(',')
        
        # 解析 JSON 格式的参数
        for name in ('model', 'encode', 'run'):
            name = name + '_kwargs'
            attr = getattr(self, name)
            if attr is None:
                setattr(self, name, dict())
            elif isinstance(attr, str):
                setattr(self, name, json.loads(attr))


def get_tasks(names: list[str] | None, languages: list[str] | None = None, benchmark: str | None = None):
    """
    获取要执行的任务列表
    
    Args:
        names: 任务名称列表
        languages: 语言列表
        benchmark: 基准测试名称
    
    Returns:
        tasks: 任务列表
    """
    if benchmark:
        # 如果指定了基准测试，获取基准测试中的所有任务
        tasks = mteb.get_benchmark(benchmark).tasks
    else:
        # 否则根据语言和任务名称获取任务
        tasks = mteb.get_tasks(languages=languages, tasks=names)
    return tasks


def get_model(model_path: str, model_name: str, precision: str = 'fp16', **kwargs):
    """
    创建并返回 Qwen3Embedding 模型实例
    
    Args:
        model_path: 模型路径
        model_name: 模型名称
        precision: 精度设置
        **kwargs: 其他模型参数
    
    Returns:
        model: Qwen3Embedding 模型实例
    """
    model = Qwen3Embedding(model_path, model_name=model_name, precision=precision, **kwargs)
    return model

def run_bright(t, model, args, **kwargs):
    """
    运行 BrightRetrieval 任务的特殊处理函数
    
    Args:
        t: 任务对象
        model: 模型实例
        args: 评估参数
        **kwargs: 其他关键字参数
    """
    # 定义不同子任务的指令模板
    Instructions = {
        "aops" : "给定一个数学问题，检索有助于回答该问题的相关示例。",
        "biology": "给定一个帖子，检索有助于回答该帖子的相关段落。",
        "earth_science": "给定一个帖子，检索有助于回答该帖子的相关段落。",
        "economics": "给定一个经济学帖子，检索有助于回答该帖子的相关段落。",
        "leetcode": "给定一个编程问题，检索有助于回答该问题的相关示例。",
        "pony": "给定一个关于 pony 编程语言的问题，检索有助于回答该问题的相关段落。",
        "psychology": "给定一个心理学帖子，检索有助于回答该帖子的相关段落。",
        "theoremqa_questions": "给定一个数学问题，检索有助于回答该问题的相关示例。",
        "theoremqa_theorems": "给定一个数学问题，检索有助于回答该问题的相关定理。",
        "robotics": "给定一个机器人学帖子，检索有助于回答该帖子的相关段落。",
        "stackoverflow": "给定一个 stackoverflow 帖子，检索有助于回答该帖子的相关段落。",
        "sustainable_living": "给定一个可持续生活帖子，检索有助于回答该帖子的相关段落。"
    }
    encode_kwargs = args.encode_kwargs or dict()

    # 遍历每个子任务
    for task in Instructions.keys():
        instruct = Instructions[task]
        # 设置任务的查询提示
        t.metadata.prompt = {'query': instruct}
        # 创建 MTEB 评估器
        evaluation = mteb.MTEB(tasks=[t])
        eval_splits = evaluation.tasks[0].metadata.eval_splits
        # 运行评估
        results = evaluation.run(
            model,
            output_folder=args.output_dir,
            encode_kwargs=encode_kwargs,
            eval_splits=eval_splits,
            eval_subsets=[task],
            **kwargs
        )
        break  # 只运行第一个任务（用于测试）


def run_eval(model, tasks: list, args: EvalArguments, **kwargs):
    """
    运行评估的主函数
    
    Args:
        model: 要评估的模型
        tasks: 任务列表
        args: 评估参数
        **kwargs: 其他关键字参数
    """
    if not tasks:
        raise RuntimeError("未选择任何任务")

    encode_kwargs = args.encode_kwargs or dict()

    # 检查是否有多个 GPU，如果有则启动模型的分布式模式
    _num_gpus, _started = torch.cuda.device_count(), False
    if _num_gpus > 1 and not _started and hasattr(model, 'start'):
        model.start()
        _started = True

    # 遍历每个任务进行评估
    for t in tasks:
        # 特殊处理 BrightRetrieval 任务
        if t.metadata.name == 'BrightRetrieval':
            run_bright(t, model, args, **kwargs)
            continue
        
        # 为特定任务加载数据
        if t.metadata.name == 'MLQARetrieval':
            load_mlqa_data(t)
        if t.metadata.name == 'HagridRetrieval':
            load_hagrid_data(t)
        if t.metadata.name == 'BelebeleRetrieval':
            load_belebel_data(t)
        if t.metadata.name in RARB_tasks:
            load_rarb_data(t)
        
        # 创建 MTEB 评估器
        evaluation = mteb.MTEB(tasks=[t])
        
        try:
            # 首先尝试离线模式运行
            os.environ['HF_DATASETS_OFFLINE'] = "1"
            results = evaluation.run(
                model,
                output_folder=args.output_dir,
                encode_kwargs=encode_kwargs,
                **kwargs
            )
        except Exception as e:
            try:
                # 如果离线模式失败，尝试在线模式
                os.environ['HF_DATASETS_OFFLINE'] = "0"
                results = evaluation.run(
                    model,
                    output_folder=args.output_dir,
                    encode_kwargs=encode_kwargs,
                    **kwargs
                )
            except Exception as e:
                # 如果仍然失败，记录错误并继续下一个任务
                print(f'运行任务时遇到错误: {t.metadata.name}. {str(e)}')
                continue

    # 如果启动了分布式模式，则停止模型
    if model is not None and _started and hasattr(model, 'stop'):
        model.stop()
    return


def main():
    """
    主函数：解析参数并运行评估
    """
    # 创建参数解析器
    parser = HfArgumentParser(EvalArguments)
    
    # 检查是否通过 JSON 配置文件传递参数
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        # 如果只传递一个参数且是 JSON 文件路径，则解析 JSON 配置
        with open(os.path.abspath(sys.argv[1])) as f:
            config = json.load(f)
        logger.warning(f"Json 配置 {f.name} : \n{json.dumps(config, indent=2)}")
        args, *_ = parser.parse_dict(config)
        del config, f
    else:
        # 否则从命令行参数解析
        args, *_ = parser.parse_args_into_dataclasses()
        logger.warning(f"参数 {args}")
    del parser

    # 获取要执行的任务
    tasks = get_tasks(args.tasks, args.langs, args.benchmark)
    logger.warning(f"选择了 {len(tasks)} 个任务:\n" + '\n'.join(str(t) for t in tasks))
    
    # 如果只是加载数据模式
    if args.only_load:
        for t in tasks:
            logger.warning(f"正在加载 {t}")
            try:
                t.load_data()
            except Exception as e:
                # 如果加载失败，尝试强制下载
                t.load_data(force_download=True)
            else:
                continue
            
        # 如果不需要加载模型，直接返回
        if not args.load_model:
            return
    
    # 创建模型实例
    model = get_model(args.model, args.model_name, precision=args.precision, **args.model_kwargs)
    
    # 如果只是加载模式，创建模型后直接返回
    if args.only_load:
        return

    # 更新编码参数，添加批处理大小
    args.encode_kwargs.update(batch_size=args.batch_size)
    
    # 运行评估
    run_eval(model, tasks, args, **args.run_kwargs)
    logger.warning(f"完成了 {len(tasks)} 个任务的评估。")
    return


if __name__ == '__main__':
    main()
