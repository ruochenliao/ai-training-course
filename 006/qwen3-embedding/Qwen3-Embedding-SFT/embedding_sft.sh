#!/bin/bash

nproc_per_node=1 
NPROC_PER_NODE=$nproc_per_node \
swift sft \
    --model /root/autodl-tmp/models/Qwen3-Embedding-0.6B \
    --task_type embedding \
    --model_type qwen3_emb \
    --train_type full \
    --dataset sentence-transformers/stsb:positive  \
    --split_dataset_ratio 0.05 \
    --eval_strategy steps \
    --output_dir output \
    --eval_steps 200 \
    --num_train_epochs 5 \
    --save_steps 200 \
    --per_device_train_batch_size 8 \
    --per_device_eval_batch_size 4 \
    --gradient_accumulation_steps 2 \
    --learning_rate 6e-6 \
    --loss_type cosine_similarity  \
    --label_names labels \
    --dataloader_drop_last true 
