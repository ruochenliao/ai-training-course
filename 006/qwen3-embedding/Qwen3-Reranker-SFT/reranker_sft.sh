#!/bin/bash

# 数据和训练参数
train_data="/root/autodl-tmp/Qwen3-Reranker-SFT/danwen_dataset.jsonl"
# 训练轮数
num_train_epochs=3
per_device_train_batch_size=4
# 梯度累积步数
gradient_accumulation_steps=1
 # 训练组大小
train_group_size=6
# GPU数量
num_gpus=1


# 模型参数（使用LoRA进行参数高效微调）
model_args="\
    --model_name_or_path /root/autodl-tmp/models/Qwen3-Reranker-0.6B \
    --use_lora True \
    --lora_rank 8 \
    --lora_alpha 16 \
    --use_flash_attn True \
    --target_modules q_proj k_proj v_proj o_proj \
    --save_merged_lora_model True \
    --model_type decoder \
"


# 数据参数（包含指令格式设置）
data_args="\
    --train_data $train_data \
    --cache_path ~/.cache \
    --train_group_size $train_group_size \
    --query_max_len 512 \
    --passage_max_len 512 \
    --pad_to_multiple_of 8
"


# 训练参数
training_args="\
    --output_dir /root/autodl-tmp/models/finetuned-qwen3-reranker \
    --overwrite_output_dir \
    --learning_rate 2e-4 \
    --bf16 \
    --num_train_epochs $num_train_epochs \
    --per_device_train_batch_size $per_device_train_batch_size \
    --gradient_accumulation_steps $gradient_accumulation_steps \
    --dataloader_drop_last True \
    --warmup_ratio 0.1 \
    --gradient_checkpointing \
    --weight_decay 0.01 \
    --deepspeed /root/autodl-tmp/Qwen3-Reranker-SFT/ds_stage0.json \
    --logging_steps 1 \
    --save_steps 1000 \
"

# 执行训练
torchrun --nproc_per_node $num_gpus \
    -m FlagEmbedding.finetune.reranker.decoder_only.base \
    $model_args \
    $data_args \
    $training_args