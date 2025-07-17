import os

from openai import OpenAI
from pymilvus import MilvusClient, model
from vanna.milvus import Milvus_VectorStore
from vanna.openai import OpenAI_Chat
# pip install pymilvus[model]
# pip install pymilvus

def pymilvus_bge_small_embedding_function(**kwargs):
    return model.dense.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-small-zh-v1.5",    # 'BAAI/bge-small-zh-v1.5'
        device='cpu', # Specify the device to use, e.g., 'cpu' or 'cuda:0'
    )
def openai_llm(**kwargs):
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"),
                  base_url=os.environ.get("OPENAI_API_BASE", "https://api.deepseek.com/v1"), **kwargs)

class DQuestionMilvus(Milvus_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        if config is None:
            milvus_client = MilvusClient(uri=os.environ.get("MILVUS_URI", "http://localhost:19530"))
            config = {'model': os.environ.get("LLM_MODEL", "deepseek-chat"),
                      "milvus_client": milvus_client,
                      "embedding_function": pymilvus_bge_small_embedding_function(),
                      "dialect": "SQLLite", # 数据库类型
                      "language": "Chinese",
                      "n_results": 15
                      }
        Milvus_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, client=openai_llm(), config=config)




# class SQLiteDatabase(DQuestionMilvus):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.kwargs = kwargs
#
#     async def train_init_data(self):
#         """
#         数据库表的结构化信息训练到向量数据库
#         :return:
#         """
#         existing_training_data = self.get_training_data()
#         if len(existing_training_data) > 0:
#             for _, training_data in existing_training_data.iterrows():
#                 self.remove_training_data(training_data['id'])
#         df_ddl = self.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")
#         # 数据训练进向量数据库
#         for ddl in df_ddl['sql'].to_list():
#             self.train(ddl=ddl)


# class MySQLDatabase(DQuestionMilvus):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.kwargs = kwargs
#         self.connect_to_mysql(host=settings.configuration.mysql_host,
#                               dbname=settings.configuration.mysql_db,
#                               user=settings.configuration.mysql_user,
#                               password=settings.configuration.mysql_password,
#                               port=int(settings.configuration.mysql_port))
#     async def train_init_data(self):
#         df_ddl = self.run_sql(f"SELECT * FROM INFORMATION_SCHEMA.COLUMNS where table_schema = '{settings.configuration.mysql_db}'")
#         plan = self.get_training_plan_mysql(df_ddl)
#         self.train(plan=plan)
#
# if __name__ == "__main__":
#     d = SQLiteDatabase()
#
#     d.train_init_data()
#     # d = MySQLDatabase()
#     # df_ddl = d.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS where table_schema = 'student_db'")
#     # plan = d.get_training_plan_mysql(df_ddl)
#     # d.train(plan=plan)
