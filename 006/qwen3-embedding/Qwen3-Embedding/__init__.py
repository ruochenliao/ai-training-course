"""
Qwen3-Embedding 项目
提供Qwen3嵌入模型和重排序模型的实现
"""

__version__ = "1.0.0"
__author__ = "Qwen Team"

# 导入主要模块
try:
    from examples import *
except ImportError:
    # 如果examples模块不可用，静默处理
    pass 