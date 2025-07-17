"""
AutoGen智能体配置
整合到统一配置系统中
"""
from typing import Dict, List, Any
from .base import settings

# 智能体配置
AGENT_CONFIGS = {
    "writer": {
        "name": "WriterAgent",
        "system_message": """你是一位专业的写作助手。你擅长：
1. 创作各种类型的文章和内容
2. 根据用户需求调整写作风格和语调
3. 提供创意和灵感
4. 确保内容的逻辑性和可读性

请根据用户的要求，创作高质量、原创的内容。保持专业、准确、有吸引力的写作风格。""",
        "max_consecutive_auto_reply": 3,
        "temperature": 0.7
    },
    
    "polisher": {
        "name": "PolisherAgent",
        "system_message": """你是一位专业的文本润色专家。你的专长包括：
1. 改进文本的流畅性和可读性
2. 优化句式结构和用词选择
3. 保持原文的核心意思和风格
4. 纠正语法和表达错误
5. 提升文本的专业性和吸引力

请对用户提供的文本进行专业的润色和改进，确保改进后的文本更加优雅、准确、易读。""",
        "max_consecutive_auto_reply": 2,
        "temperature": 0.5
    },
    
    "outliner": {
        "name": "OutlinerAgent",
        "system_message": """你是一位专业的大纲生成专家。你擅长：
1. 分析主题和创建逻辑清晰的大纲
2. 组织内容结构和层次
3. 确保大纲的完整性和实用性
4. 提供详细的章节规划
5. 考虑目标受众和内容目的

请根据用户的主题，生成结构清晰、逻辑合理、实用性强的文章大纲。""",
        "max_consecutive_auto_reply": 2,
        "temperature": 0.6
    },
    
    "researcher": {
        "name": "ResearcherAgent",
        "system_message": """你是一位专业的研究助手。你的能力包括：
1. 深入分析和研究各种主题
2. 提供准确、全面的信息
3. 整理和总结复杂的概念
4. 提供多角度的观点和见解
5. 基于事实进行逻辑推理

请根据用户的问题，提供专业、准确、深入的研究和分析。确保信息的可靠性和完整性。""",
        "max_consecutive_auto_reply": 3,
        "temperature": 0.4
    },
    
    "reviewer": {
        "name": "ReviewerAgent",
        "system_message": """你是一位专业的内容评审专家。你的职责是：
1. 评估内容的质量和准确性
2. 检查逻辑性和连贯性
3. 提供具体的改进建议
4. 确保内容符合要求和标准
5. 从多个维度进行全面评估

请对提供的内容进行专业、客观、建设性的评审和反馈。""",
        "max_consecutive_auto_reply": 2,
        "temperature": 0.3
    },
    
    "creative": {
        "name": "CreativeAgent",
        "system_message": """你是一位富有创意的内容创作专家。你的特长是：
1. 提供独特的创意和想法
2. 创作引人入胜的故事和内容
3. 运用各种修辞手法和表达技巧
4. 激发读者的兴趣和情感共鸣
5. 在创意和实用性之间找到平衡

请发挥你的创造力，为用户提供富有想象力和吸引力的内容。""",
        "max_consecutive_auto_reply": 3,
        "temperature": 0.8
    },

    "document_writer": {
        "name": "DocumentWriterAgent",
        "system_message": """你是一位专业的公文写作专家。你擅长：
1. 撰写各类公文、通报、表彰等正式文档
2. 掌握公文写作的格式规范和语言要求
3. 根据不同文档类型调整写作风格和结构
4. 确保文档的严谨性、准确性和权威性
5. 遵循公文写作的标准格式和用词规范

请根据用户提供的信息，生成符合公文写作规范的专业文档。注意格式规范、语言严谨、结构完整。""",
        "max_consecutive_auto_reply": 2,
        "temperature": 0.5
    }
}

# 协作模式配置
COLLABORATION_MODES = {
    "writing": {
        "agents": ["writer", "reviewer"],
        "description": "写作与评审协作",
        "max_rounds": 3
    },
    
    "creative_writing": {
        "agents": ["creative", "writer", "reviewer"],
        "description": "创意写作协作",
        "max_rounds": 4
    },
    
    "research_writing": {
        "agents": ["researcher", "writer", "reviewer"],
        "description": "研究型写作协作",
        "max_rounds": 4
    },
    
    "polish_review": {
        "agents": ["polisher", "reviewer"],
        "description": "润色与评审协作",
        "max_rounds": 2
    },
    
    "full_collaboration": {
        "agents": ["researcher", "writer", "polisher", "reviewer"],
        "description": "全流程协作",
        "max_rounds": 5
    }
}

# 任务类型映射
TASK_AGENT_MAPPING = {
    "ai_writer": "writer",
    "ai_polish": "polisher",
    "ai_outline": "outliner",
    "deepseek": "researcher",
    "ai_review": "reviewer",
    "ai_creative": "creative",
    "writing_wizard": "document_writer"  # 写作向导使用专门的公文写作智能体
}

# 协作任务映射
COLLABORATIVE_TASK_MAPPING = {
    "ai_collaborative": "writing",
    "creative_collaboration": "creative_writing",
    "research_collaboration": "research_writing",
    "polish_collaboration": "polish_review",
    "full_collaboration": "full_collaboration",
    "writing_wizard_collaborative": "writing"  # 写作向导协作模式
}

# 模型配置
MODEL_CONFIG = {
    "model": "gpt-3.5-turbo",
    "max_tokens": 2000,
    "temperature": 0.7,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
}

# 流式输出配置
STREAMING_CONFIG = {
    "chunk_delay": 0.05,  # 每个chunk之间的延迟（秒）
    "word_delay": 0.03,   # 每个词之间的延迟（秒）
    "enable_typing_effect": True  # 是否启用打字机效果
}
