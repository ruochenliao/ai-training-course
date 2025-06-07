import json
query = "周杰伦有哪些专辑"
db_type = "mysql"
db_schema = """
CREATE TABLE IF NOT EXISTS "Album" (
    "AlbumId" INTEGER PRIMARY KEY AUTOINCREMENT,
    "Title" NVARCHAR(160) NOT NULL,
    "ArtistId" INTEGER NOT NULL,
    FOREIGN KEY ("ArtistId") REFERENCES "Artist" ("ArtistId") 
        ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS "Artist" (
    "ArtistId" INTEGER PRIMARY KEY AUTOINCREMENT,
    "Name" NVARCHAR(120)
);
"""

mappings = {
    "AlbumId": "专辑ID",
    "Title": "专辑标题",
    "ArtistId": "艺术家ID",
    "Name": "艺术家姓名"
}

mapping_str = json.dumps(mappings, ensure_ascii=False, indent=4)


task_template = """请基于以下信息生成SQL命令分析报告：
**数据库环境：**
- 数据库类型：{db_type}
- 数据库结构：
```sql
{db_schema}
```

**值映射信息：**
```
{mappings_str}
```

**用户查询：**
{query}

**请按以下markdown格式输出详细的分析报告：**

## SQL 命令分析报告

### 1. 查询意图分析
[详细描述用户查询的核心意图和业务目标]

### 2. 涉及的数据实体
**主要表：**
- [表名1] - [用途说明]
- [表名2] - [用途说明]

**关键字段：**
- 表名1: [字段1], [字段2] - [用途说明]
- 表名2: [字段1], [字段2] - [用途说明]

### 3. 表关系与连接
[描述需要的表连接关系和连接条件]

### 4. 查询条件分析
**筛选条件：**
- [条件1] - [说明]
- [条件2] - [说明]

**分组要求：**
[是否需要分组及分组字段]

**排序要求：**
[是否需要排序及排序规则]

### 5. SQL结构框架
```sql
-- 基于分析的SQL查询结构
SELECT [字段列表]
FROM [主表]
[连接语句]
WHERE [筛选条件]
[GROUP BY 分组]
[ORDER BY 排序]
[LIMIT 限制]
```

### 6. 潜在问题与建议
[识别查询中的歧义或需要澄清的地方]
"""

task_template = task_template.format(
    db_type=db_type,
    db_schema=db_schema,
    mappings_str=mapping_str,
    query=query
)



from openai import OpenAI

client = OpenAI(api_key="sk-4b16db07796e4dce90d3b45c7c4160fe", base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ],
    stream=False
)

print(response.choices[0].message.content)