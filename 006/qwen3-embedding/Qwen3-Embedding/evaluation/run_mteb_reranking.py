# 导入必要的库
import json
import csv
import sys
import logging
import os
from dataclasses import dataclass, field
from functools import partial
from typing import Optional
import torch
from transformers import HfArgumentParser
import mteb
from utils import *
from qwen3_reranker_model import Qwen3RerankerInferenceModel

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

@dataclass
class EvalArguments:
    """
    评估参数的数据类，定义了所有可配置的评估选项
    """
    model: Optional[str] = field(
        default=None,
        metadata={"help": "预训练模型的路径或来自 huggingface.co/models 的模型标识符"}
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
    previous_results: Optional[str] = field(default='results', metadata={"help": "之前结果的目录"})

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
    获取要执行的任务列表，只保留检索类型的任务
    
    Args:
        names: 任务名称列表
        languages: 语言列表
        benchmark: 基准测试名称
    
    Returns:
        running_tasks: 过滤后的检索任务列表
    """
    if benchmark:
        # 如果指定了基准测试，获取基准测试中的所有任务
        tasks = mteb.get_benchmark(benchmark).tasks
    else:
        # 否则根据语言和任务名称获取任务
        tasks = mteb.get_tasks(languages=languages, tasks=names)

    running_tasks = []
    # 只保留检索类型的任务
    for t in tasks:
        task_type = t.metadata.type
        if task_type not in ['Retrieval']:
            continue
        running_tasks.append(t)
    return running_tasks


def get_model(model_name: str,  precision: str = 'fp16', **kwargs):
    """
    创建并返回 Qwen3RerankerInferenceModel 模型实例
    
    Args:
        model_name: 模型名称或路径
        precision: 精度设置
        **kwargs: 其他模型参数
    
    Returns:
        model: Qwen3RerankerInferenceModel 模型实例
    """
    model = Qwen3RerankerInferenceModel(model_name, **kwargs)
    return model



def run_eval(model, tasks: list, args: EvalArguments, **kwargs):
    """
    运行评估任务的主函数
    
    Args:
        model: 重排序模型实例
        tasks: 要执行的任务列表
        args: 评估参数
        **kwargs: 其他运行参数
    """
    # 定义 Bright 数据集的指令映射
    Bright_Instructions = {
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
    
    # 检查是否有任务被选中
    if not tasks:
        raise RuntimeError("没有选择任何任务")
    
    # 加载任务提示配置文件
    task_prompts_path = "task_prompts.json"
    with open(task_prompts_path) as f:
        task_prompts = json.load(f)

    # 获取编码参数
    encode_kwargs = args.encode_kwargs or dict()

    # 检查 GPU 数量并启动多 GPU 模型（如果支持）
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
        
        # 为 RARB 任务加载数据
        if t.metadata.name in RARB_tasks:
            load_rarb_data(t)
        
        # 为特定任务加载数据
        if t.metadata.name == 'MLQARetrieval':
            load_mlqa_data(t)
        if t.metadata.name == 'HagridRetrieval':
            load_hagrid_data(t)
        if t.metadata.name == 'BelebeleRetrieval':
            load_belebel_data(t)
        
        # 创建 MTEB 评估器
        evaluation = mteb.MTEB(tasks=[t])
        eval_splits = evaluation.tasks[0].metadata.eval_splits

        task_name = evaluation.tasks[0].metadata.name
        previous_results = args.previous_results
        
        # 设置任务特定的指令
        if task_name in task_prompts:
            model.instruction = task_prompts[task_name]
        
        subsets = t.hf_subsets
        
        # 遍历每个评估分割和子集
        for split in eval_splits:
            for sub_set in subsets:
                # 为 Bright 数据集设置特定指令
                if sub_set in Bright_Instructions:
                    t.metadata.prompt = Bright_Instructions[sub_set]
                
                # 构建预测结果保存路径
                if split == 'test':
                    retrieval_save_path = os.path.join(previous_results, f"{task_name}_{sub_set}_predictions.json")
                else:
                    retrieval_save_path = os.path.join(previous_results, f"{task_name}_{sub_set}_{split}_predictions.json")
                
                try:
                    # 首先尝试离线模式运行
                    os.environ['HF_DATASETS_OFFLINE'] = "1"
                    result = evaluation.run(
                        model,
                        eval_splits=[split],
                        eval_subsets=[sub_set],
                        top_k=100,
                        save_predictions=True,
                        output_folder=args.output_dir,
                        previous_results=retrieval_save_path
                    )
                except Exception as e:
                    try:
                        # 如果离线模式失败，尝试在线模式
                        os.environ['HF_DATASETS_OFFLINE'] = "0"
                        result = evaluation.run(
                            model,
                            eval_splits=[split],
                            eval_subsets=[sub_set],
                            top_k=100,
                            save_predictions=True,
                            output_folder=args.output_dir,
                            previous_results=retrieval_save_path
                        )
                    except Exception as e:
                        print(f'运行失败 {task_name} 子集 {sub_set}', e)
                        continue
    
    # 停止多 GPU 模型（如果已启动）
    if model is not None and _started and hasattr(model, 'stop'):
        model.stop()
    return


def main():
    """
    主函数：解析命令行参数并运行评估
    """
    # 创建参数解析器
    parser = HfArgumentParser(EvalArguments)
    
    # 检查是否使用 JSON 配置文件
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        # 从 JSON 文件加载配置
        with open(os.path.abspath(sys.argv[1])) as f:
            config = json.load(f)
        logger.warning(f"Json 配置 {f.name} : \n{json.dumps(config, indent=2)}")
        args, *_ = parser.parse_dict(config)
        del config, f
    else:
        # 从命令行参数解析
        args, *_ = parser.parse_args_into_dataclasses()
        logger.warning(f"参数 {args}")
    del parser

    # 获取要执行的任务列表
    tasks = get_tasks(args.tasks, args.langs, args.benchmark)
    logger.warning(f"选择了 {len(tasks)} 个任务:\n" + '\n'.join(str(t) for t in tasks))
    
    # 如果只是加载数据模式
    if args.only_load:
        for t in tasks:
            logger.warning(f"加载 {t}")
            t.load_data()
        if not args.load_model:
            return
    
    # 创建模型实例
    model = get_model(args.model, **args.model_kwargs)
    if args.only_load:
        return

    # 更新编码参数中的批处理大小
    args.encode_kwargs.update(batch_size=args.batch_size)
    
    # 运行评估
    run_eval(model, tasks, args, **args.run_kwargs)
    logger.warning(f"完成 {len(tasks)} 个任务。")
    return


if __name__ == '__main__':
    main()
