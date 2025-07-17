<p align="center">
    <img src="https://qianwen-res.oss-accelerate.aliyuncs.com/logo_qwen_embedding.png" width="400"/>
<p>

<p align="center">
   🤗 <a href="https://huggingface.co/collections/Qwen/qwen3-embedding-6841b2055b99c44d9a4c371f">Huggingface</a> | 
   🤖 <a href="https://modelscope.cn/collections/Qwen3-Embedding-3edc3762d50f48">ModelScope</a> | 
   📝 <a href="https://qwenlm.github.io/blog/qwen3-embedding/">技术博客</a> | 
   📄 <a href="https://arxiv.org/abs/2506.05176">论文</a> | 
   🚀 <a href="https://bailian.console.aliyun.com/?tab=model#/model-market/detail/text-embedding-v4">API服务</a> | 
   💬 <a href="https://discord.gg/yPEP2vHTu4">Discord</a> 
</p>

# Qwen3 Embedding: 下一代文本嵌入与重排序模型

## 📖 项目简介

Qwen3 Embedding 是通义千问团队推出的最新一代专业文本嵌入与重排序模型系列，专门针对文本嵌入和排序任务进行优化。该系列基于 Qwen3 密集基础模型构建，提供了多种规模（0.6B、4B、8B）的文本嵌入和重排序模型，继承了基础模型卓越的多语言能力、长文本理解和推理技能。

### 🌟 核心亮点

**🎯 卓越性能**: 
- 8B 嵌入模型在 MTEB 多语言排行榜上获得 **第1名**（截至2025年6月5日，得分**70.58**）
- 在文本检索、代码检索、文本分类、文本聚类和双语挖掘等多个任务上达到最先进性能

**🔧 灵活多样**:
- 提供完整的模型规模选择（0.6B 到 8B）
- 支持自定义向量维度（MRL，Matryoshka表示学习）
- 支持用户自定义指令，增强特定任务、语言或场景的性能

**🌍 多语言支持**:
- 支持超过100种语言，包括各种编程语言
- 提供强大的多语言、跨语言和代码检索能力

## 📊 模型列表

| 模型类型 | 模型名称 | 参数量 | 层数 | 序列长度 | 嵌入维度 | MRL支持 | 指令感知 |
|---------|---------|------|------|---------|---------|---------|---------|
| 文本嵌入 | [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) | 0.6B | 28 | 32K | 1024 | ✅ | ✅ |
| 文本嵌入 | [Qwen3-Embedding-4B](https://huggingface.co/Qwen/Qwen3-Embedding-4B) | 4B | 36 | 32K | 2560 | ✅ | ✅ |
| 文本嵌入 | [Qwen3-Embedding-8B](https://huggingface.co/Qwen/Qwen3-Embedding-8B) | 8B | 36 | 32K | 4096 | ✅ | ✅ |
| 文本重排序 | [Qwen3-Reranker-0.6B](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B) | 0.6B | 28 | 32K | - | - | ✅ |
| 文本重排序 | [Qwen3-Reranker-4B](https://huggingface.co/Qwen/Qwen3-Reranker-4B) | 4B | 36 | 32K | - | - | ✅ |
| 文本重排序 | [Qwen3-Reranker-8B](https://huggingface.co/Qwen/Qwen3-Reranker-8B) | 8B | 36 | 32K | - | - | ✅ |

> **注意**:
> - `MRL支持` 表示嵌入模型是否支持自定义最终嵌入的维度
> - `指令感知` 表示嵌入或重排序模型是否支持根据不同任务自定义输入指令
> - 我们的评估表明，对于大多数下游任务，使用指令通常比不使用指令提高1%到5%的性能

## 🚀 快速开始

### 环境要求

```bash
# 建议使用 transformers>=4.51.0
pip install transformers torch numpy
```

### 嵌入模型使用

#### 1. 使用 Transformers

```python
import torch
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel

def last_token_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    """最后一个token的池化操作"""
    left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
    if left_padding:
        return last_hidden_states[:, -1]
    else:
        sequence_lengths = attention_mask.sum(dim=1) - 1
        batch_size = last_hidden_states.shape[0]
        return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]

def get_detailed_instruct(task_description: str, query: str) -> str:
    """构建详细指令"""
    return f'Instruct: {task_description}\nQuery:{query}'

# 初始化模型和分词器
tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3-Embedding-0.6B', padding_side='left')
model = AutoModel.from_pretrained('Qwen/Qwen3-Embedding-0.6B')

# 建议启用 flash_attention_2 以获得更好的加速和内存节省
# model = AutoModel.from_pretrained('Qwen/Qwen3-Embedding-0.6B', 
#                                  attn_implementation="flash_attention_2", 
#                                  torch_dtype=torch.float16).cuda()

# 定义任务和文本
task = 'Given a web search query, retrieve relevant passages that answer the query'
queries = [
    get_detailed_instruct(task, 'What is the capital of China?'),
    get_detailed_instruct(task, 'Explain gravity')
]
documents = [
    "The capital of China is Beijing.",
    "Gravity is a force that attracts two bodies towards each other."
]

# 编码
input_texts = queries + documents
batch_dict = tokenizer(input_texts, padding=True, truncation=True, 
                      max_length=8192, return_tensors="pt")
batch_dict.to(model.device)

outputs = model(**batch_dict)
embeddings = last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])

# 标准化并计算相似度
embeddings = F.normalize(embeddings, p=2, dim=1)
scores = (embeddings[:2] @ embeddings[2:].T)
print(scores.tolist())
```

#### 2. 使用 vLLM（推荐用于生产环境）

```python
import torch
import vllm
from vllm import LLM

# 初始化模型
model = LLM(model="Qwen/Qwen3-Embedding-0.6B", task="embed")

# 编码文本
input_texts = [
    'Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery:What is the capital of China?',
    "The capital of China is Beijing."
]

outputs = model.embed(input_texts)
embeddings = torch.tensor([o.outputs.embedding for o in outputs])
scores = (embeddings[:1] @ embeddings[1:].T)
print(scores.tolist())
```

#### 3. 使用 Sentence Transformers

```python
from sentence_transformers import SentenceTransformer

# 加载模型
model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")

# 编码查询和文档
queries = ["What is the capital of China?", "Explain gravity"]
documents = [
    "The capital of China is Beijing.",
    "Gravity is a force that attracts two bodies towards each other."
]

# 使用预定义的查询提示编码
query_embeddings = model.encode(queries, prompt_name="query")
document_embeddings = model.encode(documents)

# 计算相似度
similarity = model.similarity(query_embeddings, document_embeddings)
print(similarity)
```

### 重排序模型使用

#### 使用 Transformers

```python
import torch
from transformers import AutoModel, AutoTokenizer, AutoModelForCausalLM

def format_instruction(instruction, query, doc):
    """格式化重排序输入"""
    if instruction is None:
        instruction = 'Given a web search query, retrieve relevant passages that answer the query'
    return f"<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}"

# 初始化模型
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-Reranker-0.6B", padding_side='left')
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-Reranker-0.6B").eval()

# 设置特殊token
token_false_id = tokenizer.convert_tokens_to_ids("no")
token_true_id = tokenizer.convert_tokens_to_ids("yes")

# 准备输入
task = 'Given a web search query, retrieve relevant passages that answer the query'
queries = ["What is the capital of China?", "Explain gravity"]
documents = [
    "The capital of China is Beijing.",
    "Gravity is a force that attracts two bodies towards each other."
]

pairs = [format_instruction(task, query, doc) for query, doc in zip(queries, documents)]

# 详细的处理过程请参考 examples/qwen3_reranker_transformers.py
```

## 📁 项目结构

```
Qwen3-Embedding/
├── examples/                          # 使用示例
│   ├── qwen3_embedding_transformers.py    # 嵌入模型 Transformers 示例
│   ├── qwen3_embedding_vllm.py           # 嵌入模型 vLLM 示例
│   ├── qwen3_reranker_transformers.py    # 重排序模型 Transformers 示例
│   └── qwen3_reranker_vllm.py           # 重排序模型 vLLM 示例
├── evaluation/                        # 评估脚本和工具
│   ├── run_mteb.py                    # MTEB 嵌入评估脚本
│   ├── run_mteb_reranking.py          # MTEB 重排序评估脚本
│   ├── qwen3_embedding_model.py       # 嵌入模型包装器
│   ├── qwen3_reranker_model.py        # 重排序模型包装器
│   └── requirements.txt               # 评估依赖
├── qwen3_embedding_technical_report.pdf  # 技术报告
└── README.md                          # 本文档
```

## 🔧 支持的语言

Qwen3-Embedding 支持超过100种语言，包括：

<details>
<summary>点击展开支持的语言列表</summary>

| 语系 | 支持的语言 |
|-----|----------|
| 印欧语系 | 英语、法语、葡萄牙语、德语、罗马尼亚语、瑞典语、丹麦语、保加利亚语、俄语、捷克语、希腊语、乌克兰语、西班牙语、荷兰语、斯洛伐克语、克罗地亚语、波兰语、立陶宛语、挪威语、波斯语、斯洛文尼亚语、古吉拉特语、拉脱维亚语、意大利语、尼泊尔语、马拉地语、白俄罗斯语、塞尔维亚语、印地语、旁遮普语、孟加拉语、奥里亚语、塔吉克语、意第绪语、爱尔兰语、法罗语、信德语、亚美尼亚语等 |
| 汉藏语系 | 中文（简体中文、繁体中文、粤语）、缅甸语 |
| 闪含语系 | 阿拉伯语（标准阿拉伯语、各方言）、希伯来语、马耳他语 |
| 南岛语系 | 印尼语、马来语、他加禄语、宿务语、爪哇语、巽他语等 |
| 达罗毗荼语系 | 泰米尔语、泰卢固语、卡纳达语、马拉雅拉姆语 |
| 突厥语系 | 土耳其语、阿塞拜疆语、乌兹别克语、哈萨克语、巴什基尔语、鞑靼语 |
| 壮侗语系 | 泰语、老挝语 |
| 乌拉尔语系 | 芬兰语、爱沙尼亚语、匈牙利语 |
| 南亚语系 | 越南语、高棉语 |
| 其他 | 日语、韩语、格鲁吉亚语、巴斯克语、海地克里奥尔语、斯瓦希里语等 |

</details>

## 📈 性能评估

### MTEB 多语言基准测试

| 模型 | 参数量 | 平均分(任务) | 平均分(类型) | 双语挖掘 | 分类 | 聚类 | 指令检索 | 多语言分类 | 配对分类 | 重排序 | 检索 | 语义相似度 |
|-----|-------|------------|------------|----------|------|------|----------|-----------|----------|--------|------|-----------|
| **Qwen3-Embedding-8B** | 8B | **70.58** | **61.69** | **80.89** | **74.00** | **57.65** | 10.06 | 28.66 | **86.40** | **65.63** | **70.88** | **81.08** |
| **Qwen3-Embedding-4B** | 4B | 69.45 | 60.86 | 79.36 | 72.33 | 57.15 | **11.56** | 26.77 | 85.05 | 65.08 | 69.60 | 80.86 |
| **Qwen3-Embedding-0.6B** | 0.6B | 64.33 | 56.00 | 72.22 | 66.83 | 52.33 | 5.09 | 24.59 | 80.83 | 61.41 | 64.64 | 76.17 |

### MTEB 英文基准测试 v2

| 模型 | 参数量 | 平均分(任务) | 平均分(类型) | 分类 | 聚类 | 配对分类 | 重排序 | 检索 | 语义相似度 | 摘要 |
|-----|-------|------------|------------|------|------|----------|--------|------|-----------|------|
| **Qwen3-Embedding-8B** | 8B | **75.22** | **68.71** | **90.43** | 58.57 | 87.52 | **51.56** | **69.44** | 88.58 | 34.83 |
| **Qwen3-Embedding-4B** | 4B | 74.60 | 68.10 | 89.84 | 57.51 | 87.01 | 50.76 | 68.46 | **88.72** | 34.39 |
| **Qwen3-Embedding-0.6B** | 0.6B | 70.70 | 64.88 | 85.76 | 54.05 | 84.37 | 48.18 | 61.83 | 86.57 | 33.43 |

### C-MTEB 中文基准测试

| 模型 | 参数量 | 平均分(任务) | 平均分(类型) | 分类 | 聚类 | 配对分类 | 重排序 | 检索 | 语义相似度 |
|-----|-------|------------|------------|------|------|----------|--------|------|-----------|
| **Qwen3-Embedding-8B** | 8B | **73.84** | **75.00** | **76.97** | **80.08** | 84.23 | 66.99 | **78.21** | 63.53 |
| **Qwen3-Embedding-4B** | 4B | 72.27 | 73.51 | 75.46 | 77.89 | 83.34 | 66.05 | 77.03 | 61.26 |
| **Qwen3-Embedding-0.6B** | 0.6B | 66.33 | 67.45 | 71.40 | 68.74 | 76.42 | 62.58 | 71.03 | 54.52 |

## 🔬 评估和测试

本项目提供了完整的评估工具来复现论文中的结果。

### 评估嵌入模型

```bash
cd evaluation
bash run_mteb.sh ${model_path} ${model_name} ${benchmark_name}
```

参数说明：
- `model_path`: 模型权重文件的路径或名称（如 "Qwen/Qwen3-Embedding-0.6B"）
- `model_name`: 模型名称，用于命名结果目录
- `benchmark_name`: 基准测试名称，支持的值："MTEB(eng, v2)"、"MTEB(cmn, v1)"、"MTEB(Code, v1)"、"MTEB(Multilingual, v2)"

### 评估重排序模型

```bash
bash run_mteb_reranking.sh ${model_path} ${model_name} ${retrieval_path} ${benchmark}
```

参数说明：
- `model_path`: 重排序模型权重文件路径
- `model_name`: 模型名称
- `retrieval_path`: 嵌入评估阶段生成的检索结果路径
- `benchmark`: 基准测试名称

### 汇总评估结果

```bash
python3 summary.py results/${model_name}/${model_name}/no_version_available benchmark_name
```

## 💡 使用建议

1. **指令优化**: 建议开发者根据具体场景、任务和语言自定义指令，通常可以带来1%-5%的性能提升
2. **多语言场景**: 在多语言环境下，建议使用英文编写指令，因为训练过程中大部分指令都是英文
3. **性能优化**: 
   - 推荐使用 Flash Attention 2 以获得更好的加速和内存节省
   - 生产环境建议使用 vLLM 以获得更好的推理性能
   - 可以根据需求使用 MRL 功能自定义向量维度

## 🤝 贡献

欢迎为项目贡献代码和建议！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📜 许可证

本项目采用与原始 Qwen 项目相同的许可证。详细信息请参考模型页面的许可证部分。

## 📚 引用

如果您觉得我们的工作对您有帮助，请考虑引用我们的论文：

```bibtex
@article{qwen3embedding,
  title={Qwen3 Embedding: Advancing Text Embedding and Reranking Through Foundation Models},
  author={Zhang, Yanzhao and Li, Mingxin and Long, Dingkun and Zhang, Xin and Lin, Huan and Yang, Baosong and Xie, Pengjun and Yang, An and Liu, Dayiheng and Lin, Junyang and Huang, Fei and Zhou, Jingren},
  journal={arXiv preprint arXiv:2506.05176},
  year={2025}
}
```
