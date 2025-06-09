# text2sql的原理
核心原理，大模型对用户问题理解、Schema 的理解，语义解析、SQL 生成等关键步骤

# 安装 vanna 
创建一个向量数据库 Milvus，ChromaDB

# 学习 vanna 
Milvus 三个集合
    DDL: 数据定义语言（表结构、字段、约束信息等）
    SQL: 问答对（用户问题：正确的SQL）
    DOC: 文字描述（小样本）

# vanna 原理
用户的问题 -> 向量转换 -> 分别到以上三个集合中查找相关数据 -> 汇集一起发给LLM
    生成SQL
    执行SQL
    输出报表

# 初始化 schema 
    
# 测试数据
    
# 训练问题
    
# 准确率测试

# text2sql 的问题所在
