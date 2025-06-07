import json

task_template = """你是一名{db_type} 专家，需要根据用户问题回答SQL语句：
- 数据库结构：
```sql
{db_schema}
```
**值映射信息：**
```
{mappings_str}
"""

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

task_template = task_template.format(
    db_type=db_type,
    db_schema=db_schema,
    mappings_str=mapping_str
)


## 调用API 生成SQL语句
from openai import OpenAI

client = OpenAI(api_key="sk-4b16db07796e4dce90d3b45c7c4160fe", base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": task_template},
        {"role": "user", "content" : query}
    ],
    stream=False
)

print(response.choices[0].message.content)


