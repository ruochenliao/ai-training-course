

<p align="center">
    <img src="https://qianwen-res.oss-accelerate.aliyuncs.com/logo_qwen_embedding.png" width="400"/>
<p>

<p align="center">
   &nbsp&nbsp <a href="https://huggingface.co/collections/Qwen/qwen3-embedding-6841b2055b99c44d9a4c371f">Huggingface</a>&nbsp&nbsp | &nbsp&nbsp <a href="https://modelscope.cn/collections/Qwen3-Embedding-3edc3762d50f48">ModelScope</a>&nbsp&nbsp | &nbsp&nbsp <a href="https://qwenlm.github.io/blog/qwen3-embedding/">Blog</a> &nbsp&nbsp | &nbsp&nbsp <a href="https://arxiv.org/abs/2506.05176">Arxiv</a> &nbsp&nbsp | &nbsp&nbsp <a href="https://bailian.console.aliyun.com/?tab=model#/model-market/detail/text-embedding-v4">API</a> ｜ &nbsp&nbsp <a href="https://discord.gg/yPEP2vHTu4">Discord</a> 
</p>

# Qwen3 Embedding

## Highlights

The Qwen3 Embedding model series is the latest proprietary model of the Qwen family, specifically designed for text embedding and ranking tasks. Building upon the dense foundational models of the Qwen3 series, it provides a comprehensive range of text embeddings and reranking models in various sizes (0.6B, 4B, and 8B). This series inherits the exceptional multilingual capabilities, long-text understanding, and reasoning skills of its foundational model. The Qwen3 Embedding series represents significant advancements in multiple text embedding and ranking tasks, including text retrieval, code retrieval, text classification, text clustering, and bitext mining.

**Exceptional Versatility**: The embedding model has achieved state-of-the-art performance across a wide range of downstream application evaluations. The 8B size embedding model ranks **No.1** in the MTEB multilingual leaderboard (as of June 5, 2025, score **70.58**), while the reranking model excels in various text retrieval scenarios.

**Comprehensive Flexibility**: The Qwen3 Embedding series offers a full spectrum of sizes (from 0.6B to 8B) for both embedding and reranking models, catering to diverse use cases that prioritize efficiency and effectiveness. Developers can seamlessly combine these two modules. Additionally, the embedding model allows for flexible vector definitions across all dimensions, and both embedding and reranking models support user-defined instructions to enhance performance for specific tasks, languages, or scenarios.

**Multilingual Capability**: The Qwen3 Embedding series offer support for over 100 languages, thanks to the multilingual capabilites of Qwen3 models. This includes various programming languages, and provides robust multilingual, cross-lingual, and code retrieval capabilities.


## Qwen3 Embedding Series Model list

| Model Type       | Models               | Size | Layers | Sequence Length | Embedding Dimension | MRL Support | Instruction Aware |
|------------------|----------------------|------|--------|-----------------|---------------------|-------------|----------------|
| Text Embedding   | [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) | 0.6B | 28     | 32K             | 1024                | Yes         | Yes            |
| Text Embedding   | [Qwen3-Embedding-4B](https://huggingface.co/Qwen/Qwen3-Embedding-4B)   | 4B   | 36     | 32K             | 2560                | Yes         | Yes            |
| Text Embedding   | [Qwen3-Embedding-8B](https://huggingface.co/Qwen/Qwen3-Embedding-8B)   | 8B   | 36     | 32K             | 4096                | Yes         | Yes            |
| Text Reranking   | [Qwen3-Reranker-0.6B](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B) | 0.6B | 28     | 32K             | -                   | -           | Yes            |
| Text Reranking   | [Qwen3-Reranker-4B](https://huggingface.co/Qwen/Qwen3-Reranker-4B)   | 4B   | 36     | 32K             | -                   | -           | Yes            |
| Text Reranking   | [Qwen3-Reranker-8B](https://huggingface.co/Qwen/Qwen3-Reranker-8B)   | 8B   | 36     | 32K             | -                   | -           | Yes            |

> **Note**:
> - `MRL (Matryoshka Representation Learning) Support` indicates whether the embedding model supports custom dimensions for the final embedding. 
> - `Instruction Aware` notes whether the embedding or reranking model supports customizing the input instruction according to different tasks.
> - Our evaluation indicates that, for most downstream tasks, using instructions (instruct) typically yields an improvement of 1% to 5% compared to not using them. Therefore, we recommend that developers create tailored instructions specific to their tasks and scenarios. In multilingual contexts, we also advise users to write their instructions in English, as most instructions utilized during the model training process were originally written in English.

### Multilingual Support

Qwen3-Embedding model series shares the multilingual support capabilities of the Qwen3 base model. 

<details>
<summary>Click to expand the list of supported languages</summary>

| Language Family | Languages & Dialects |
|---|---|
| Indo-European | English, French, Portuguese, German, Romanian, Swedish, Danish, Bulgarian, Russian, Czech, Greek, Ukrainian, Spanish, Dutch, Slovak, Croatian, Polish, Lithuanian, Norwegian Bokmål, Norwegian Nynorsk, Persian, Slovenian, Gujarati, Latvian, Italian, Occitan, Nepali, Marathi, Belarusian, Serbian, Luxembourgish, Venetian, Assamese, Welsh, Silesian, Asturian, Chhattisgarhi, Awadhi, Maithili, Bhojpuri, Sindhi, Irish, Faroese, Hindi, Punjabi, Bengali, Oriya, Tajik, Eastern Yiddish, Lombard, Ligurian, Sicilian, Friulian, Sardinian, Galician, Catalan, Icelandic, Tosk Albanian, Limburgish, Dari, Afrikaans, Macedonian, Sinhala, Urdu, Magahi, Bosnian, Armenian |
| Sino-Tibetan | Chinese (Simplified Chinese, Traditional Chinese, Cantonese), Burmese |
| Afro-Asiatic | Arabic (Standard, Najdi, Levantine, Egyptian, Moroccan, Mesopotamian, Ta'izzi-Adeni, Tunisian), Hebrew, Maltese |
| Austronesian | Indonesian, Malay, Tagalog, Cebuano, Javanese, Sundanese, Minangkabau, Balinese, Banjar, Pangasinan, Iloko, Waray (Philippines)  |
| Dravidian | Tamil, Telugu, Kannada, Malayalam |
| Turkic | Turkish, North Azerbaijani, Northern Uzbek, Kazakh, Bashkir, Tatar |
| Tai-Kadai | Thai, Lao |
| Uralic | Finnish, Estonian, Hungarian |
| Austroasiatic | Vietnamese, Khmer |
| Other | Japanese, Korean, Georgian, Basque, Haitian, Papiamento, Kabuverdianu, Tok Pisin, Swahili | 

</details>

## Usage

With Transformers versions earlier than 4.51.0, you may encounter the following error:
```
KeyError: 'qwen3'
```
### Embedding Model

#### Transformers Usage

```python
# Requires transformers>=4.51.0

import torch
import torch.nn.functional as F

from torch import Tensor
from transformers import AutoTokenizer, AutoModel


def last_token_pool(last_hidden_states: Tensor,
                 attention_mask: Tensor) -> Tensor:
    left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
    if left_padding:
        return last_hidden_states[:, -1]
    else:
        sequence_lengths = attention_mask.sum(dim=1) - 1
        batch_size = last_hidden_states.shape[0]
        return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]


def get_detailed_instruct(task_description: str, query: str) -> str:
    return f'Instruct: {task_description}\nQuery:{query}'

# Each query must come with a one-sentence instruction that describes the task
task = 'Given a web search query, retrieve relevant passages that answer the query'

queries = [
    get_detailed_instruct(task, 'What is the capital of China?'),
    get_detailed_instruct(task, 'Explain gravity')
]
# No need to add instruction for retrieval documents
documents = [
    "The capital of China is Beijing.",
    "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun."
]
input_texts = queries + documents

tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3-Embedding-0.6B', padding_side='left')
model = AutoModel.from_pretrained('Qwen/Qwen3-Embedding-0.6B')

# We recommend enabling flash_attention_2 for better acceleration and memory saving.
# model = AutoModel.from_pretrained('Qwen/Qwen3-Embedding-0.6B', attn_implementation="flash_attention_2", torch_dtype=torch.float16).cuda()

max_length = 8192

# Tokenize the input texts
batch_dict = tokenizer(
    input_texts,
    padding=True,
    truncation=True,
    max_length=max_length,
    return_tensors="pt",
)
batch_dict.to(model.device)
outputs = model(**batch_dict)
embeddings = last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])

# normalize embeddings
embeddings = F.normalize(embeddings, p=2, dim=1)
scores = (embeddings[:2] @ embeddings[2:].T)
print(scores.tolist())
# [[0.7645568251609802, 0.14142508804798126], [0.13549736142158508, 0.5999549627304077]]
```

#### vLLM Usage 
```python
# Requires vllm>=0.8.5
import torch
import vllm
from vllm import LLM

def get_detailed_instruct(task_description: str, query: str) -> str:
    return f'Instruct: {task_description}\nQuery:{query}'

# Each query must come with a one-sentence instruction that describes the task
task = 'Given a web search query, retrieve relevant passages that answer the query'

queries = [
    get_detailed_instruct(task, 'What is the capital of China?'),
    get_detailed_instruct(task, 'Explain gravity')
]
# No need to add instruction for retrieval documents
documents = [
    "The capital of China is Beijing.",
    "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun."
]
input_texts = queries + documents

model = LLM(model="Qwen/Qwen3-Embedding-0.6B", task="embed")

outputs = model.embed(input_texts)
embeddings = torch.tensor([o.outputs.embedding for o in outputs])
scores = (embeddings[:2] @ embeddings[2:].T)
print(scores.tolist())
# [[0.7620252966880798, 0.14078938961029053], [0.1358368694782257, 0.6013815999031067]]
```

#### Sentence Transformers Usage
```python
# Requires transformers>=4.51.0
# Requires sentence-transformers>=2.7.0

from sentence_transformers import SentenceTransformer

# Load the model
model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")

# We recommend enabling flash_attention_2 for better acceleration and memory saving,
# together with setting `padding_side` to "left":
# model = SentenceTransformer(
#     "Qwen/Qwen3-Embedding-0.6B",
#     model_kwargs={"attn_implementation": "flash_attention_2", "device_map": "auto"},
#     tokenizer_kwargs={"padding_side": "left"},
# )

# The queries and documents to embed
queries = [
    "What is the capital of China?",
    "Explain gravity",
]
documents = [
    "The capital of China is Beijing.",
    "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun.",
]

# Encode the queries and documents. Note that queries benefit from using a prompt
# Here we use the prompt called "query" stored under `model.prompts`, but you can
# also pass your own prompt via the `prompt` argument
query_embeddings = model.encode(queries, prompt_name="query")
document_embeddings = model.encode(documents)

# Compute the (cosine) similarity between the query and document embeddings
similarity = model.similarity(query_embeddings, document_embeddings)
print(similarity)
# tensor([[0.7646, 0.1414], [0.1355, 0.6000]])
```
### Reranker Model

#### Transformers Usage

```python
# Requires transformers>=4.51.0
import torch
from transformers import AutoModel, AutoTokenizer, AutoModelForCausalLM

def format_instruction(instruction, query, doc):
    if instruction is None:
        instruction = 'Given a web search query, retrieve relevant passages that answer the query'
    output = "<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}".format(instruction=instruction,query=query, doc=doc)
    return output

def process_inputs(pairs):
    inputs = tokenizer(
        pairs, padding=False, truncation='longest_first',
        return_attention_mask=False, max_length=max_length - len(prefix_tokens) - len(suffix_tokens)
    )
    for i, ele in enumerate(inputs['input_ids']):
        inputs['input_ids'][i] = prefix_tokens + ele + suffix_tokens
    inputs = tokenizer.pad(inputs, padding=True, return_tensors="pt", max_length=max_length)
    for key in inputs:
        inputs[key] = inputs[key].to(model.device)
    return inputs

@torch.no_grad()
def compute_logits(inputs, **kwargs):
    batch_scores = model(**inputs).logits[:, -1, :]
    true_vector = batch_scores[:, token_true_id]
    false_vector = batch_scores[:, token_false_id]
    batch_scores = torch.stack([false_vector, true_vector], dim=1)
    batch_scores = torch.nn.functional.log_softmax(batch_scores, dim=1)
    scores = batch_scores[:, 1].exp().tolist()
    return scores

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-Reranker-0.6B", padding_side='left')
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-Reranker-0.6B").eval()

# We recommend enabling flash_attention_2 for better acceleration and memory saving.
# model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-Reranker-0.6B", torch_dtype=torch.float16, attn_implementation="flash_attention_2").cuda().eval()

token_false_id = tokenizer.convert_tokens_to_ids("no")
token_true_id = tokenizer.convert_tokens_to_ids("yes")
max_length = 8192

prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
prefix_tokens = tokenizer.encode(prefix, add_special_tokens=False)
suffix_tokens = tokenizer.encode(suffix, add_special_tokens=False)
        
task = 'Given a web search query, retrieve relevant passages that answer the query'

queries = ["What is the capital of China?",
    "Explain gravity",
]

documents = [
    "The capital of China is Beijing.",
    "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun.",
]

pairs = [format_instruction(task, query, doc) for query, doc in zip(queries, documents)]

# Tokenize the input texts
inputs = process_inputs(pairs)
scores = compute_logits(inputs)

print("scores: ", scores)
```

#### vLLM Usage 

```python
# Requires vllm>=0.8.5
import logging
from typing import Dict, Optional, List

import json
import logging

import torch

from transformers import AutoTokenizer, is_torch_npu_available
from vllm import LLM, SamplingParams
from vllm.distributed.parallel_state import destroy_model_parallel
import gc
import math
from vllm.inputs.data import TokensPrompt

def format_instruction(instruction, query, doc):
    text = [
        {"role": "system", "content": "Judge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\"."},
        {"role": "user", "content": f"<Instruct>: {instruction}\n\n<Query>: {query}\n\n<Document>: {doc}"}
    ]
    return text

def process_inputs(pairs, instruction, max_length, suffix_tokens):
    messages = [format_instruction(instruction, query, doc) for query, doc in pairs]
    messages =  tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=False, enable_thinking=False
    )
    messages = [ele[:max_length] + suffix_tokens for ele in messages]
    messages = [TokensPrompt(prompt_token_ids=ele) for ele in messages]
    return messages

def compute_logits(model, messages, sampling_params, true_token, false_token):
    outputs = model.generate(messages, sampling_params, use_tqdm=False)
    scores = []
    for i in range(len(outputs)):
        final_logits = outputs[i].outputs[0].logprobs[-1]
        token_count = len(outputs[i].outputs[0].token_ids)
        if true_token not in final_logits:
            true_logit = -10
        else:
            true_logit = final_logits[true_token].logprob
        if false_token not in final_logits:
            false_logit = -10
        else:
            false_logit = final_logits[false_token].logprob
        true_score = math.exp(true_logit)
        false_score = math.exp(false_logit)
        score = true_score / (true_score + false_score)
        scores.append(score)
    return scores

number_of_gpu = torch.cuda.device_count()
tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3-Reranking-4B')
model = LLM(model='Qwen/Qwen3-Reranking-0.6B', tensor_parallel_size=number_of_gpu, max_model_len=10000, enable_prefix_caching=True, gpu_memory_utilization=0.8)
tokenizer.padding_side = "left"
tokenizer.pad_token = tokenizer.eos_token
suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
max_length=8192
suffix_tokens = tokenizer.encode(suffix, add_special_tokens=False)
true_token = tokenizer("yes", add_special_tokens=False).input_ids[0]
false_token = tokenizer("no", add_special_tokens=False).input_ids[0]
sampling_params = SamplingParams(temperature=0, 
    max_tokens=1,
    logprobs=20, 
    allowed_token_ids=[true_token, false_token],
)

        
task = 'Given a web search query, retrieve relevant passages that answer the query'
queries = ["What is the capital of China?",
    "Explain gravity",
]
documents = [
    "The capital of China is Beijing.",
    "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun.",
]

pairs = list(zip(queries, documents))
inputs = process_inputs(pairs, task, max_length-len(suffix_tokens), suffix_tokens)
scores = compute_logits(model, inputs, sampling_params, true_token, false_token)
print('scores', scores)

destroy_model_parallel()
```


📌 **Tip**: We recommend that developers customize the `instruct` according to their specific scenarios, tasks, and languages. Our tests have shown that in most retrieval scenarios, not using an `instruct` on the query side can lead to a drop in retrieval performance by approximately 1% to 5%.

For more usage examples, see the code in the [examples]() sections.

## Evaluation

The code for reproducing the following results is available in the [evaluation]() section.

### MTEB (Multilingual)

| Model                            |  Size   |  Mean (Task)  | Mean (Type) | Bitxt Mining | Class. | Clust. | Inst. Retri. | Multi. Class. | Pair. Class. | Rerank | Retri. | STS  |
|----------------------------------|:-------:|:-------------:|:-------------:|:--------------:|:--------:|:--------:|:--------------:|:---------------:|:--------------:|:--------:|:--------:|:------:|
| NV-Embed-v2                      |   7B    |     56.29     | 49.58       | 57.84        | 57.29  | 40.80  | 1.04         | 18.63         | 78.94        | 63.82  | 56.72  | 71.10|
| GritLM-7B                        |   7B    |     60.92     | 53.74       | 70.53        | 61.83  | 49.75  | 3.45         | 22.77         | 79.94        | 63.78  | 58.31  | 73.33|
| BGE-M3                           |  0.6B   |     59.56     | 52.18       | 79.11        | 60.35  | 40.88  | -3.11        | 20.1          | 80.76        | 62.79  | 54.60  | 74.12|
| multilingual-e5-large-instruct   |  0.6B   |     63.22     | 55.08       | 80.13        | 64.94  | 50.75  | -0.40        | 22.91         | 80.86        | 62.61  | 57.12  | 76.81|
| gte-Qwen2-1.5B-instruct          |  1.5B   |     59.45     | 52.69       | 62.51        | 58.32  | 52.05  | 0.74         | 24.02         | 81.58        | 62.58  | 60.78  | 71.61|
| gte-Qwen2-7b-Instruct            |   7B    |     62.51     | 55.93       | 73.92        | 61.55  | 52.77  | 4.94         | 25.48         | 85.13        | 65.55  | 60.08  | 73.98|
| text-embedding-3-large           |    -    |     58.93     | 51.41       | 62.17        | 60.27  | 46.89  | -2.68        | 22.03         | 79.17        | 63.89  | 59.27  | 71.68|
| Cohere-embed-multilingual-v3.0   |    -    |     61.12     | 53.23       | 70.50        | 62.95  | 46.89  | -1.89        | 22.74         | 79.88        | 64.07  | 59.16  | 74.80|
| gemini-embedding-exp-03-07       |    -    |     68.37     | 59.59       | 79.28        | 71.82  | 54.59  | 5.18         | **29.16**     | 83.63        | 65.58  | 67.71  | 79.40|
| **Qwen3-Embedding-0.6B**         |  0.6B   |     64.33     | 56.00       | 72.22        | 66.83  | 52.33  | 5.09         | 24.59         | 80.83        | 61.41  | 64.64  | 76.17|
| **Qwen3-Embedding-4B**           |   4B    |     69.45     | 60.86       | 79.36        | 72.33  | 57.15  | **11.56**    | 26.77         | 85.05        | 65.08  | 69.60  | 80.86|
| **Qwen3-Embedding-8B**           |   8B    |   **70.58**   | **61.69**   | **80.89**    | **74.00** | **57.65** | 10.06      | 28.66         | **86.40**    | **65.63** | **70.88** | **81.08** |

> **Note**: For compared models, the scores are retrieved from MTEB online [leaderboard](https://huggingface.co/spaces/mteb/leaderboard) on June 6th, 2025.

### MTEB (Eng v2)

| MTEB English / Models          |  Param.  | Mean(Task) | Mean(Type) | Class. | Clust. | Pair Class. | Rerank. | Retri. | STS   | Summ. |
|--------------------------------|:--------:|:------------:|:------------:|:--------:|:--------:|:-------------:|:---------:|:--------:|:-------:|:-------:|
| multilingual-e5-large-instruct |   0.6B   | 65.53      | 61.21      | 75.54  | 49.89  | 86.24       | 48.74   | 53.47  | 84.72 | 29.89 |
| NV-Embed-v2                    |   7.8B   | 69.81      | 65.00      | 87.19  | 47.66  | 88.69       | 49.61   | 62.84  | 83.82 | 35.21 |
| GritLM-7B                      |   7.2B   | 67.07      | 63.22      | 81.25  | 50.82  | 87.29       | 49.59   | 54.95  | 83.03 | 35.65 |
| gte-Qwen2-1.5B-instruct        |   1.5B   | 67.20      | 63.26      | 85.84  | 53.54  | 87.52       | 49.25   | 50.25  | 82.51 | 33.94 |
| stella_en_1.5B_v5              |   1.5B   | 69.43      | 65.32      | 89.38  | 57.06  | 88.02       | 50.19   | 52.42  | 83.27 | 36.91 |
| gte-Qwen2-7B-instruct          |   7.6B   | 70.72      | 65.77      | 88.52  | 58.97  | 85.9        | 50.47   | 58.09  | 82.69 | 35.74 |
| gemini-embedding-exp-03-07     |    -     | 73.3       | 67.67      | 90.05  | **59.39**  | **87.7**   | 48.59   | 64.35  | 85.29 | **38.28** |
| **Qwen3-Embedding-0.6B**       |   0.6B   | 70.70      | 64.88      | 85.76  | 54.05  | 84.37       | 48.18   | 61.83  | 86.57 | 33.43 |
| **Qwen3-Embedding-4B**         |    4B    | 74.60      | 68.10      | 89.84  | 57.51  | 87.01       | 50.76   | 68.46  | **88.72** | 34.39 |
| **Qwen3-Embedding-8B**         |    8B    | **75.22**  | **68.71**  | **90.43** | 58.57  | 87.52       | **51.56**   | **69.44**  | 88.58 | 34.83 |

### C-MTEB (MTEB Chinese)

| C-MTEB           | Param. | Mean(Task) | Mean(Type) | Class. | Clust. | Pair Class. | Rerank. | Retr. | STS   |
|------------------|--------|------------|------------|--------|--------|-------------|---------|-------|-------|
| multilingual-e5-large-instruct | 0.6B   | 58.08      | 58.24      | 69.80  | 48.23  | 64.52       | 57.45   | 63.65 | 45.81 |
| bge-multilingual-gemma2 | 9B     | 67.64      |68.52   | 75.31      | 59.30  | 86.67  | 68.28       | 73.73   | 55.19 | 
| gte-Qwen2-1.5B-instruct  | 1.5B   | 67.12      | 67.79      | 72.53  | 54.61  | 79.5        | 68.21   | 71.86 | 60.05 |
| gte-Qwen2-7B-instruct    | 7.6B   | 71.62      | 72.19      | 75.77  | 66.06  | 81.16       | 69.24   | 75.70 | 65.20 |
| ritrieve_zh_v1          | 0.3B   | 72.71      | 73.85      | 76.88  | 66.5   | **85.98**       | **72.86**   | 76.97 | **63.92** |
| **Qwen3-Embedding-0.6B** | 0.6B   | 66.33      | 67.45      | 71.40  | 68.74  | 76.42       | 62.58   | 71.03 | 54.52 |
| **Qwen3-Embedding-4B**   | 4B     | 72.27      | 73.51      | 75.46  | 77.89  | 83.34       | 66.05   | 77.03 | 61.26 |
| **Qwen3-Embedding-8B**   | 8B     | **73.84**  | **75.00**  | **76.97**  | **80.08**  | 84.23       | 66.99   | **78.21** | 63.53 |

### Reranker
| Model                              | Param  | MTEB-R  | CMTEB-R | MMTEB-R | MLDR   | MTEB-Code | FollowIR |
|------------------------------------|--------|---------|---------|---------|--------|-----------|----------|
| **Qwen3-Embedding-0.6B**               | 0.6B   | 61.82   | 71.02   | 64.64   | 50.26  | 75.41     | 5.09     |
| Jina-multilingual-reranker-v2-base | 0.3B   | 58.22   | 63.37   | 63.73   | 39.66  | 58.98     | -0.68    |
| gte-multilingual-reranker-base                      | 0.3B   | 59.51   | 74.08   | 59.44   | 66.33  | 54.18     | -1.64    |
| BGE-reranker-v2-m3                 | 0.6B   | 57.03   | 72.16   | 58.36   | 59.51  | 41.38     | -0.01    |
| **Qwen3-Reranker-0.6B**                | 0.6B   | 65.80   | 71.31   | 66.36   | 67.28  | 73.42     | 5.41     |
| **Qwen3-Reranker-4B**                  | 4B   | **69.76** | 75.94   | 72.74   | 69.97  | 81.20     | **14.84** |
| **Qwen3-Reranker-8B**                  | 8B     | 69.02   | **77.45** | **72.94** | **70.19** | **81.22** | 8.05     |

> **Note**:  
> - Evaluation results for reranking models. We use the retrieval subsets of MTEB(eng, v2), MTEB(cmn, v1), MMTEB and MTEB (Code), which are MTEB-R, CMTEB-R, MMTEB-R and MTEB-Code.
> - All scores are our runs based on the top-100 candidates retrieved by dense embedding model [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B).


## Citation
If you find our work helpful, feel free to give us a cite.

```
@article{qwen3embedding,
  title={Qwen3 Embedding: Advancing Text Embedding and Reranking Through Foundation Models},
  author={Zhang, Yanzhao and Li, Mingxin and Long, Dingkun and Zhang, Xin and Lin, Huan and Yang, Baosong and Xie, Pengjun and Yang, An and Liu, Dayiheng and Lin, Junyang and Huang, Fei and Zhou, Jingren},
  journal={arXiv preprint arXiv:2506.05176},
  year={2025}
}
```
