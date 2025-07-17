import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple, Awaitable, Callable, Union, TypedDict
from dataclasses import dataclass, asdict

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import ModelClientStreamingChunkEvent, TextMessage, UserInputRequestedEvent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core import message_handler, RoutedAgent, SingleThreadedAgentRuntime, DefaultTopicId, TopicId, \
    type_subscription, AgentId, MessageContext, CancellationToken, ClosureContext
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core import ClosureAgent, TypeSubscription
from pydantic import BaseModel

from c_app.core.config import settings

from c_app.core.llms import model_client
from c_app.schemas.text2sql import (
    Text2SQLResponse, ResponseMessage, QueryMessage, SqlMessage,
    SqlExplanationMessage, SqlResultMessage, VisualizationMessage, AnalysisMessage
)
from c_app.db.dbaccess import DBAccess

# 定义主题类型
sql_generator_topic_type = "sql_generator"
sql_explainer_topic_type = "sql_explainer"
sql_executor_topic_type = "sql_executor"
visualization_recommender_topic_type = "visualization_recommender"
stream_output_topic_type = "stream_output"
query_analyzer_topic_type = "query_analyzer"

# 定义智能体名称常量
QUERY_ANALYZER_NAME = "query_analyzer"
SQL_GENERATOR_NAME = "sql_generator"
SQL_EXPLAINER_NAME = "sql_explainer"
SQL_EXECUTOR_NAME = "sql_executor"
VISUALIZATION_RECOMMENDER_NAME = "visualization_recommender"
USER_PROXY_NAME = "user_proxy"

# 定义数据库类型（可配置）
DB_TYPE = "MySQL"  # 可选值: "MySQL", "PostgreSQL", "SQLite", "Oracle", "SQL Server"

# 表结构及关系的描述
db_schema_definition = """
CREATE TABLE [Album]
(
    [AlbumId] INTEGER  NOT NULL,
    [Title] NVARCHAR(160)  NOT NULL,
    [ArtistId] INTEGER  NOT NULL,
    CONSTRAINT [PK_Album] PRIMARY KEY  ([AlbumId]),
    FOREIGN KEY ([ArtistId]) REFERENCES [Artist] ([ArtistId]) 
		ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE [Artist]
(
    [ArtistId] INTEGER  NOT NULL,
    [Name] NVARCHAR(120),
    CONSTRAINT [PK_Artist] PRIMARY KEY  ([ArtistId])
);

CREATE TABLE [Customer]
(
    [CustomerId] INTEGER  NOT NULL,
    [FirstName] NVARCHAR(40)  NOT NULL,
    [LastName] NVARCHAR(20)  NOT NULL,
    [Company] NVARCHAR(80),
    [Address] NVARCHAR(70),
    [City] NVARCHAR(40),
    [State] NVARCHAR(40),
    [Country] NVARCHAR(40),
    [PostalCode] NVARCHAR(10),
    [Phone] NVARCHAR(24),
    [Fax] NVARCHAR(24),
    [Email] NVARCHAR(60)  NOT NULL,
    [SupportRepId] INTEGER,
    CONSTRAINT [PK_Customer] PRIMARY KEY  ([CustomerId]),
    FOREIGN KEY ([SupportRepId]) REFERENCES [Employee] ([EmployeeId]) 
		ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE [Employee]
(
    [EmployeeId] INTEGER  NOT NULL,
    [LastName] NVARCHAR(20)  NOT NULL,
    [FirstName] NVARCHAR(20)  NOT NULL,
    [Title] NVARCHAR(30),
    [ReportsTo] INTEGER,
    [BirthDate] DATETIME,
    [HireDate] DATETIME,
    [Address] NVARCHAR(70),
    [City] NVARCHAR(40),
    [State] NVARCHAR(40),
    [Country] NVARCHAR(40),
    [PostalCode] NVARCHAR(10),
    [Phone] NVARCHAR(24),
    [Fax] NVARCHAR(24),
    [Email] NVARCHAR(60),
    CONSTRAINT [PK_Employee] PRIMARY KEY  ([EmployeeId]),
    FOREIGN KEY ([ReportsTo]) REFERENCES [Employee] ([EmployeeId]) 
		ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE [Genre]
(
    [GenreId] INTEGER  NOT NULL,
    [Name] NVARCHAR(120),
    CONSTRAINT [PK_Genre] PRIMARY KEY  ([GenreId])
);

CREATE TABLE [Invoice]
(
    [InvoiceId] INTEGER  NOT NULL,
    [CustomerId] INTEGER  NOT NULL,
    [InvoiceDate] DATETIME  NOT NULL,
    [BillingAddress] NVARCHAR(70),
    [BillingCity] NVARCHAR(40),
    [BillingState] NVARCHAR(40),
    [BillingCountry] NVARCHAR(40),
    [BillingPostalCode] NVARCHAR(10),
    [Total] NUMERIC(10,2)  NOT NULL,
    CONSTRAINT [PK_Invoice] PRIMARY KEY  ([InvoiceId]),
    FOREIGN KEY ([CustomerId]) REFERENCES [Customer] ([CustomerId]) 
		ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE [InvoiceLine]
(
    [InvoiceLineId] INTEGER  NOT NULL,
    [InvoiceId] INTEGER  NOT NULL,
    [TrackId] INTEGER  NOT NULL,
    [UnitPrice] NUMERIC(10,2)  NOT NULL,
    [Quantity] INTEGER  NOT NULL,
    CONSTRAINT [PK_InvoiceLine] PRIMARY KEY  ([InvoiceLineId]),
    FOREIGN KEY ([InvoiceId]) REFERENCES [Invoice] ([InvoiceId]) 
		ON DELETE NO ACTION ON UPDATE NO ACTION,
    FOREIGN KEY ([TrackId]) REFERENCES [Track] ([TrackId]) 
		ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE [MediaType]
(
    [MediaTypeId] INTEGER  NOT NULL,
    [Name] NVARCHAR(120),
    CONSTRAINT [PK_MediaType] PRIMARY KEY  ([MediaTypeId])
);

CREATE TABLE [Playlist]
(
    [PlaylistId] INTEGER  NOT NULL,
    [Name] NVARCHAR(120),
    CONSTRAINT [PK_Playlist] PRIMARY KEY  ([PlaylistId])
);

CREATE TABLE [PlaylistTrack]
(
    [PlaylistId] INTEGER  NOT NULL,
    [TrackId] INTEGER  NOT NULL,
    CONSTRAINT [PK_PlaylistTrack] PRIMARY KEY  ([PlaylistId], [TrackId]),
    FOREIGN KEY ([PlaylistId]) REFERENCES [Playlist] ([PlaylistId]) 
		ON DELETE NO ACTION ON UPDATE NO ACTION,
    FOREIGN KEY ([TrackId]) REFERENCES [Track] ([TrackId]) 
		ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE [Track]
(
    [TrackId] INTEGER  NOT NULL,
    [Name] NVARCHAR(200)  NOT NULL,
    [AlbumId] INTEGER,
    [MediaTypeId] INTEGER  NOT NULL,
    [GenreId] INTEGER,
    [Composer] NVARCHAR(220),
    [Milliseconds] INTEGER  NOT NULL,
    [Bytes] INTEGER,
    [UnitPrice] NUMERIC(10,2)  NOT NULL,
    CONSTRAINT [PK_Track] PRIMARY KEY  ([TrackId]),
    FOREIGN KEY ([AlbumId]) REFERENCES [Album] ([AlbumId]) 
		ON DELETE NO ACTION ON UPDATE NO ACTION,
    FOREIGN KEY ([GenreId]) REFERENCES [Genre] ([GenreId]) 
		ON DELETE NO ACTION ON UPDATE NO ACTION,
    FOREIGN KEY ([MediaTypeId]) REFERENCES [MediaType] ([MediaTypeId]) 
		ON DELETE NO ACTION ON UPDATE NO ACTION
);



/*******************************************************************************
   Create Primary Key Unique Indexes
********************************************************************************/

/*******************************************************************************
   Create Foreign Keys
********************************************************************************/
CREATE INDEX [IFK_AlbumArtistId] ON [Album] ([ArtistId]);

CREATE INDEX [IFK_CustomerSupportRepId] ON [Customer] ([SupportRepId]);

CREATE INDEX [IFK_EmployeeReportsTo] ON [Employee] ([ReportsTo]);

CREATE INDEX [IFK_InvoiceCustomerId] ON [Invoice] ([CustomerId]);

CREATE INDEX [IFK_InvoiceLineInvoiceId] ON [InvoiceLine] ([InvoiceId]);

CREATE INDEX [IFK_InvoiceLineTrackId] ON [InvoiceLine] ([TrackId]);

CREATE INDEX [IFK_PlaylistTrackPlaylistId] ON [PlaylistTrack] ([PlaylistId]);

CREATE INDEX [IFK_PlaylistTrackTrackId] ON [PlaylistTrack] ([TrackId]);

CREATE INDEX [IFK_TrackAlbumId] ON [Track] ([AlbumId]);

CREATE INDEX [IFK_TrackGenreId] ON [Track] ([GenreId]);

CREATE INDEX [IFK_TrackMediaTypeId] ON [Track] ([MediaTypeId]);

"""
db_schema_definition2 = """
-- ----------------------------
-- Table structure for balancetable_copy1
-- ----------------------------
CREATE TABLE `balancetable_copy1`  (
  `COL_1` double NULL DEFAULT NULL COMMENT '序号',
  `COL_2` datetime NULL DEFAULT NULL COMMENT '所属月份',
  `COL_3` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '一级分类',
  `COL_4` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '二级分类',
  `COL_5` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '三级分类',
  `COL_6` double NULL DEFAULT NULL COMMENT '期末余额',
  `PT` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'PT'
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;
-- 样本数据 --
INSERT INTO `balancetable_copy1` VALUES (1, '2023-01-01 00:00:00', '资产', '流动资产', '货币资金', 33901.94, '20250313141929');
INSERT INTO `balancetable_copy1` VALUES (2, '2023-01-01 00:00:00', '资产', '流动资产', '应收资金集中管理款（内部存款）', 44753471.305, '20250313141929');
INSERT INTO `balancetable_copy1` VALUES (3, '2023-01-01 00:00:00', '资产', '流动资产', '交易性金融资产', 0, '20250313141929');

-- ----------------------------
-- Table structure for companyawards_final_copy1
-- ----------------------------
CREATE TABLE `companyawards_final_copy1`  (
  `COL_1` double NULL DEFAULT NULL COMMENT '序号',
  `COL_3` double NULL DEFAULT NULL COMMENT '获奖年度',
  `COL_4` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '所属公司',
  `COL_5` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '子公司',
  `COL_6` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '部门',
  `COL_7` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '奖项名称',
  `COL_9` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '级别',
  `COL_10` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '项目名称_研究题目',
  `COL_11` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '获奖人_获奖机构',
  `COL_12` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '获奖人类型',
  `PT` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'PT'
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;
-- 样本数据 --
INSERT INTO `companyawards_final_copy1` VALUES (10, 2023, '共享服务公司', NULL, NULL, '风控内控竞赛资本金融支持及其他板块团体第三名', '公司级', NULL, '共*司', '单位', '20250325095022');
INSERT INTO `companyawards_final_copy1` VALUES (11, 2023, '共享服务公司', NULL, NULL, '集团公司“十二五”信息化先进基层单位', '省部级', NULL, '共*司', '单位', '20250325095022');
INSERT INTO `companyawards_final_copy1` VALUES (12, 2018, '共享服务公司', NULL, NULL, '财务管理先进单位', '省部级', NULL, '共*司', '单位', '20250325095022');
INSERT INTO `companyawards_final_copy1` VALUES (1, 2020, '共享服务公司', '共享本部', NULL, '优秀工会干部', '公司级', NULL, '代*嵩', '个人', '20250325095022');
INSERT INTO `companyawards_final_copy1` VALUES (14, 2020, '共享服务公司', '共享本部', NULL, '优秀工会会员', '公司级', NULL, '陈*宁', '个人', '20250325095022');
INSERT INTO `companyawards_final_copy1` VALUES (15, 2020, '共享服务公司', '共享本部', NULL, '优秀工会会员', '公司级', NULL, '牟*良', '个人', '20250325095022');
INSERT INTO `companyawards_final_copy1` VALUES (16, 2020, '共享服务公司', '共享本部', NULL, '优秀职工之友', '公司级', NULL, '江*鑫', '个人', '20250325095022');
I

"""
dbAccess = DBAccess(dialect="sqlite")
# dbAccess.connect_to_mysql(host="114.55.110.60", dbname="dongying", user="root", password="twf65132090TWF", port=3306)
dbAccess.connect_to_sqlite("https://vanna.ai/Chinook.sqlite")
# df_ddl = dbAccess.run_sql("SELECT type,sql FROM sqlite_master WHERE sql is not null")
# db_schema_definition = df_ddl['sql'].to_list()

class StreamResponseCollector:
    """流式响应收集器，用于收集智能体产生的流式输出"""

    def __init__(self):
        """初始化流式响应收集器"""
        self.callback: Optional[Callable[[ClosureContext, ResponseMessage, MessageContext], Awaitable[None]]] = None
        self.user_input: Optional[Callable[[str, CancellationToken], Awaitable[str]]] = None

    def set_callback(self, callback: Callable[[ClosureContext, ResponseMessage, MessageContext], Awaitable[None]]) -> None:
        """设置回调函数

        Args:
            callback: 用于处理响应消息的异步回调函数
        """
        self.callback = callback

    def set_user_input(self, user_input: Callable[[str, CancellationToken], Awaitable[str]]) -> None:
        """设置用户输入函数"""
        self.user_input = user_input

# 查询分析智能体，负责分析用户查询和表结构的关系
@type_subscription(topic_type=query_analyzer_topic_type)
class QueryAnalyzerAgent(RoutedAgent):
    def __init__(self, db_schema=None, db_type=DB_TYPE, input_func=None):
        super().__init__("query_analyzer_agent")
        self.model_client = model_client
        # 数据训练进向量数据库
        self.db_schema = db_schema or db_schema_definition
        self.db_type = db_type
        self.input_func = input_func
        self._prompt = f"""
            你是一名专业的数据库分析与生成SQL命令的分析专家。你的任务是深入分析用户的自然语言查询，并结合给定的数据库表结构信息，生成一份完整详细的关于生成SQL命令的分析报告。这份报告将作为后续指导另一个大模型生成精确SQL命令的关键依据。
            **核心目标：**
            
            基于用户查询和数据库结构，输出一份结构化的报告，详细描述如何将用户意图转化为SQL查询的关键步骤和考虑因素。
            
            **你需要处理以下信息：**
            
            * **数据库类型：** {self.db_type}
            * **数据库结构：**
                ```sql
                {self.db_schema}
                ```
            * **用户原始问题：** [query]
            
            **请按照以下步骤进行分析并生成报告：**
            
            1.  **查询意图深度分析：**
                * 详细描述用户提出的自然语言查询的核心意图。用户希望从数据库中检索或操作哪些数据？他们的最终目标是什么？
                * 识别查询中涉及的关键概念和实体。
            
            2.  **主要实体与关系识别：**
                * 根据用户查询和数据库结构，识别出查询所涉及的主要实体（对应数据库中的表）。
                * 分析这些实体之间的关系（例如，一对一、一对多、多对多），并确定可能需要进行的表连接。
            
            3.  **所需表与字段精确确定：**
                * 列出用户查询明确或暗示需要使用的所有表名。
                * 列出需要从这些表中检索的所有字段名。如果需要进行计算或聚合操作，也请在此处说明。
            
            4.  **潜在歧义与缺失信息识别：**
                * 分析用户查询中可能存在的歧义或不明确之处。例如，用户是否使用了模糊的术语、未指定具体的条件、或者查询范围不清晰？
                * 指出生成完整且准确SQL语句所需的任何缺失信息。
            
            5.  **SQL操作类型与结构初步构思：**
                * 基于对用户意图的理解，确定需要执行的SQL操作类型（例如：SELECT, INSERT, UPDATE, DELETE）。对于查询操作，需要进一步考虑是否需要聚合函数（SUM, AVG, COUNT, MAX, MIN）、分组（GROUP BY）、排序（ORDER BY）、限制结果数量（LIMIT）等。
                * 初步构思SQL查询语句的基本结构框架，包括涉及的表、大致的连接方式和主要的条件逻辑。
            
            6.  **报告输出 - 请严格按照以下格式：**

            ### SQL 命令生成报告
        
            #### 1. 用户原始问题：
            [在此处填写用户的自然语言查询]
        
            #### 2. 数据库类型：
            {self.db_type}
        
            #### 3. 数据库结构：
            ```sql
            {self.db_schema}
            ```
        
            #### 4. 查询意图描述：
            [对用户查询意图进行详细描述]
        
            #### 5. 需要使用的表名列表：
            - [表名1]
            - [表名2]
            - ...
        
            #### 6. 需要使用的字段列表：
            - 表名1: [字段1], [字段2], ...
            - 表名2: [字段1], [字段2], ...
            - ...
            （请注明是否需要使用聚合函数，例如：`SUM(sales_amount)`）
        
            #### 7. 需要的表连接描述：
            - [如果需要连接，描述连接的表以及连接条件（例如：`orders` 表通过 `user_id` 连接到 `users` 表）]
            - [如果不需要连接，说明原因]
        
            #### 8. 筛选条件描述：
            - [描述用户查询中隐含或明确要求的筛选条件 (例如：`WHERE status = '已发货'`)]
            - [如果存在多个筛选条件，请说明它们之间的逻辑关系 (例如：AND, OR)]
        
            #### 9. 分组描述：
            - [描述是否需要对结果进行分组 (GROUP BY)，以及分组的字段是什么]
            - [说明分组后是否需要进行聚合操作]
        
            #### 10. 排序描述：
            - [描述是否需要对结果进行排序 (ORDER BY)，以及排序的字段和排序方式 (ASC/DESC)]
        
            #### 11. 潜在歧义与缺失信息：
            - [列出用户查询中存在的任何潜在歧义，并说明可能导致不同SQL解释的情况]
            - [指出生成完整SQL语句所需的缺失信息，并说明需要用户提供哪些额外细节]
        
            #### 12. 初步的SQL查询结构草案：
            ```sql
            -- 基于以上分析的初步 SQL 查询结构
            SELECT [在此处填写需要选择的字段]
            FROM [在此处填写需要使用的表名]
            [在此处填写需要的连接 (例如：INNER JOIN table2 ON ...)]
            WHERE [在此处填写筛选条件]
            [在此处填写分组 (例如：GROUP BY ...)]
            [在此处填写排序 (例如：ORDER BY ...)]
            [在此处填写限制结果数量 (例如：LIMIT ...)]
            ;
            ```
        请确保你的报告内容详尽、准确，能够清晰地反映用户查询的意图以及如何将其转化为可执行的SQL命令。这份报告的质量将直接影响后续SQL语句生成的准确性。
        注意：如果用户提出修改建议，只需要输出修改部分内容即可，不需要将整篇报告输出。
        """

    @message_handler
    async def handle_message(self, message: QueryMessage, ctx: MessageContext) -> None:
        """处理接收到的消息，分析查询意图和所需表结构"""
        # 创建agent并执行任务
        self._prompt = self._prompt.replace("[query]", message.query)
        agent = AssistantAgent(
            name="query_analyzer",
            model_client=self.model_client,
            system_message=self._prompt,
            model_client_stream=True,
        )
        memory = ListMemory()
        analysis_content = ""
        # 如果需要用户对分析报告进行反馈
        if self.input_func:
            user_proxy = UserProxyAgent(
                name="user_proxy",
                input_func=self.input_func
            )
            termination_en = TextMentionTermination("APPROVE")
            termination_zh = TextMentionTermination("同意")
            # 支持用户对分析报告进行多次修改
            team = RoundRobinGroupChat([agent, user_proxy], termination_condition=termination_en | termination_zh, )
            stream = team.run_stream(task=message.query)
            async for msg in stream:
                # 模拟流式输出
                if isinstance(msg, ModelClientStreamingChunkEvent):
                    await self.publish_message(ResponseMessage(source=QUERY_ANALYZER_NAME, content=msg.content),
                                               topic_id=TopicId(type=stream_output_topic_type, source=self.id.key))
                    continue
                # 记录每次对话历史记录
                if isinstance(msg, TextMessage):
                    # 保存历史记忆
                    await memory.add(MemoryContent(content=msg.model_dump_json(), mime_type=MemoryMimeType.JSON.value))
                    continue
                # 等待用户输入对分析报告的修改建议
                if isinstance(msg, UserInputRequestedEvent) and msg.source == "user_proxy":
                    await self.publish_message(ResponseMessage(source=msg.source, content="请输入修改建议或者直接点击同意"),
                                               topic_id=TopicId(type=stream_output_topic_type, source=self.id.key))
                    continue
        else:
            # 如果用户没有参与修改，则直接生成分析报告
            stream = agent.run_stream(task=message.query)
            async for event in stream:
                if isinstance(event, ModelClientStreamingChunkEvent):
                    # 确保内容以Markdown格式正确渲染
                    await self.publish_message(
                        ResponseMessage(source=QUERY_ANALYZER_NAME, content=event.content),
                        topic_id=TopicId(type=stream_output_topic_type, source=self.id.key)
                    )
                    continue
                if isinstance(event, TextMessage):
                    await memory.add(MemoryContent(content=event.model_dump_json(), mime_type=MemoryMimeType.JSON.value))

        await self.publish_message(
            ResponseMessage(
                source=QUERY_ANALYZER_NAME,
                content="\n\n分析已完成",
                is_final=True,  # 关键标记
            ),
            topic_id=TopicId(type=stream_output_topic_type, source=self.id.key)
        )

        # 将 ListMemory 转换为可序列化的格式
        memory_content = []
        for content in memory.content:  # 使用.content属性而不是.contents
            memory_content.append({
                "content": content.content,
                "mime_type": content.mime_type,  # 将MemoryMimeType转换为字符串
                "metadata": content.metadata  # 加入metadata字段以保存完整信息
            })

        analysis_message = AnalysisMessage(
            query=message.query,
            memory_content=memory_content,  # 使用转换后的内容
            analysis=analysis_content,
            role="assistant"
        )

        await self.publish_message(
            analysis_message,
            topic_id=TopicId(type=sql_generator_topic_type, source=self.id.key)
        )

# SQL生成智能体，负责将自然语言转换为SQL
@type_subscription(topic_type=sql_generator_topic_type)
class SqlGeneratorAgent(RoutedAgent):
    def __init__(self, db_schema=None, db_type=DB_TYPE):
        super().__init__("sql_generator_agent")
        self.model_client = model_client
        self.db_schema = db_schema or db_schema_definition
        self.db_type = db_type
        self._prompt = f"""
        你是一名专业的SQL转换专家。你的任务是基于上下文信息及SQL命令生成报告，将用户的自然语言查询转换为精确的SQL语句。
        
        ## 生成SQL的指导原则：
        
        1.  **严格遵循报告中的分析：** 仔细阅读并理解上述的SQL命令生成报告，包括查询意图、需要使用的表和字段、连接方式、筛选条件、分组和排序要求。
        2.  **生成有效的SQL语句：** 仅输出符合 {self.db_type} 数据库语法的有效SQL语句，不要添加任何额外的解释或说明。
        3.  **准确表达筛选条件：** 报告中如有筛选条件描述，务必在生成的SQL语句中准确实现。
        4.  **正确使用表连接：** 按照报告中"需要的表连接描述"进行表连接，并确保连接条件正确。
        5.  **实现分组和聚合：** 如果报告中指示需要进行分组（GROUP BY）或聚合操作（例如 SUM, COUNT, AVG），请在SQL语句中正确实现。
        6.  **实现排序：** 按照报告中"排序描述"的要求，使用 ORDER BY 子句对结果进行排序。
        7.  **考虑数据库特性：** 生成的SQL语句应符合 {self.db_type} 数据库的特定语法和函数。
        8.  **SQL格式规范：** 使用清晰可读的SQL格式，适当添加换行和缩进，以提高可读性。
        9.  **避免使用不支持的语法：** 不要使用 {self.db_type} 数据库不支持的特殊语法或函数。
        10. **仅生成SQL：** 最终输出结果必须是纯粹的SQL查询语句，没有任何额外的文本。
        
        特别注意：最终只生成一条您认为最符合用户查询需求的SQL语句。
        """

    @message_handler
    async def handle_analysis_message(self, message: AnalysisMessage, ctx: MessageContext) -> None:
        """处理AnalysisMessage类型的消息"""
        # 从memory_content重建ListMemory对象
        memory = ListMemory()
        # 直接设置内容属性，效率更高
        memory_contents = []
        for item in message.memory_content:
            memory_contents.append(MemoryContent(
                content=item["content"],
                mime_type=item["mime_type"],
                metadata=item.get("metadata", None)  # 读取可能存在的metadata
            ))
        memory.content = memory_contents  # 利用ListMemory的content属性直接设置内容

        agent = AssistantAgent(
            name="sql_generator",
            model_client=self.model_client,
            system_message=self._prompt,
            memory=[memory],  # 使用重建的memory
            model_client_stream=True,
        )

        result = await agent.run(task=message.query)
        sql_content = result.messages[-1].content

        # 首先将SQL内容发送为流式消息，供前端实时更新
        await self.publish_message(
            ResponseMessage(source=SQL_GENERATOR_NAME, content=sql_content),
            topic_id=TopicId(type=stream_output_topic_type, source=self.id.key)
        )

        # 发送SQL内容为final_sql类型，触发前端SQL语句区域显示
        await self.publish_message(
            ResponseMessage(
                source=SQL_GENERATOR_NAME,
                content="SQL语句已生成",
                is_final=True,
                result={"sql": sql_content}  # 使用正确的格式包含SQL语句
            ),
            topic_id=TopicId(type=stream_output_topic_type, source=self.id.key)
        )

        await self.publish_message(
            SqlMessage(query=message.query, sql=sql_content),
            topic_id=TopicId(type=sql_explainer_topic_type, source=self.id.key)
        )


# SQL解释智能体，负责解释SQL语句的含义
@type_subscription(topic_type=sql_explainer_topic_type)
class SqlExplainerAgent(RoutedAgent):
    def __init__(self, db_schema=None, db_type=DB_TYPE):
        super().__init__("sql_explainer_agent")
        self.model_client = model_client
        self.db_schema = db_schema or db_schema_definition
        self.db_type = db_type
        self._prompt = f"""
        你是一名专业的SQL解释专家，你的任务是以准确、易懂的方式向非技术人员解释给定的SQL语句的含义和作用。
        
        ## 数据库类型
        {self.db_type}
        
        ## 数据库结构
        ```sql
        {self.db_schema}
        ```
        
        ## 用户问题
        [query]
        
        ## 需要解释的SQL语句
        [sql]
        
        ## 规则
        
        1.  **使用通俗易懂的语言：** 解释应该避免使用过于专业或技术性的术语。目标是让没有任何编程或数据库知识的人也能理解。
        2.  **准确且全面地解释：** 确保解释的准确性，并覆盖SQL语句的主要功能和逻辑。
        3.  **解释关键子句：** 针对SQL语句中的每个主要子句（例如 `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `ORDER BY`, `JOIN` 等）解释其作用和目的。
        4.  **说明查询结果：** 清晰地描述执行这条SQL语句后，预计会从数据库中返回什么类型的数据和结果。
        5.  **解释复杂特性：**
            * **聚合函数：** 如果SQL语句中使用了聚合函数（如 `SUM`, `AVG`, `COUNT`, `MAX`, `MIN`），解释这些函数的作用以及它们是如何计算结果的。
            * **表连接：** 如果使用了表连接（如 `JOIN`），解释为什么要进行连接，以及连接是如何根据相关字段将不同表中的数据关联起来的。可以结合数据库结构进行解释。
            * **子查询：** 如果使用了子查询（嵌套查询），解释子查询的目的以及它是如何帮助主查询获取所需数据的。
        6.  **结合数据库结构：** 在解释过程中，可以适当引用提供的数据库表结构，帮助理解表名、字段名的含义以及表之间的关系。例如，解释 `users.name` 时，可以说明 `name` 是 `users` 表中的一个字段，用于存储用户的姓名。
        7.  **保持简洁明了：** 尽量用简短的句子表达清楚意思，避免冗长的描述。解释的长度一般不超过200字。
        8.  **直接解释提供的SQL：** 你的解释应该直接针对用户问题 `[query]` 和 `[sql]` 部分提供的具体SQL代码。
        
        **示例解释框架：**
        
        "这条SQL语句的作用是[整体功能描述]。它首先从 `[表名]` 表中[FROM子句的解释]。然后，它会筛选出满足[WHERE子句的解释]的记录。如果使用了 `GROUP BY`，则会按照[GROUP BY子句的解释]进行分组，并且可能会使用[聚合函数]计算每个组的结果。最后，结果可能会按照[ORDER BY子句的解释]进行排序。总的来说，这条语句会返回[对查询结果的总结性描述]。"
        """

    @message_handler
    async def handle_message(self, message: SqlMessage, ctx: MessageContext) -> None:
        """处理接收到的消息，解释SQL语句"""
        self._prompt = self._prompt.replace("[sql]", message.sql).replace("[query]", message.query)
        agent = AssistantAgent(
            name="sql_explainer",
            model_client=self.model_client,
            system_message=self._prompt,
            model_client_stream=True,
        )

        stream = agent.run_stream(task=f"解释以下SQL语句：\n{message.sql}")
        explanation_content = ""

        async for event in stream:
            if isinstance(event, ModelClientStreamingChunkEvent):
                await self.publish_message(
                    ResponseMessage(source=SQL_EXPLAINER_NAME, content=event.content),
                    topic_id=TopicId(type=stream_output_topic_type, source=self.id.key)
                )
            elif isinstance(event, TaskResult):
                explanation_content = event.messages[-1].content.strip()

        await self.publish_message(
            ResponseMessage(source=SQL_EXPLAINER_NAME, content="\n\n解释完成", is_final=True,),
            topic_id=TopicId(type=stream_output_topic_type, source=self.id.key)
        )

        await self.publish_message(
            SqlExplanationMessage(
                query=message.query,
                sql=message.sql,
                explanation=explanation_content
            ),
            topic_id=TopicId(type=sql_executor_topic_type, source=self.id.key)
        )


# SQL执行智能体，负责模拟执行SQL并返回结果
@type_subscription(topic_type=sql_executor_topic_type)
class SqlExecutorAgent(RoutedAgent):
    def __init__(self):
        super().__init__("sql_executor_agent")
    @message_handler
    async def handle_message(self, message: SqlExplanationMessage, ctx: MessageContext) -> None:
        """处理接收到的消息，根据SQL生成模拟数据"""

        sql = message.sql.replace("```sql", "").replace("```", "")
        results = dbAccess.run_sql(sql)
        # 发送执行完成的消息
        await self.publish_message(
            ResponseMessage(source=SQL_EXECUTOR_NAME, content=f"SQL执行完成，获取到{len(results)}条结果"),
            topic_id=TopicId(type=stream_output_topic_type, source=self.id.key)
        )

        results = results.to_dict("records")
        # 然后立即发送数据结果，这样前端会显示数据表格
        await self.publish_message(
            ResponseMessage(
                source=SQL_EXECUTOR_NAME,
                content="查询结果数据",
                is_final=True,
                result={
                    "results": results,  # 只包含结果数据
                }
            ),
            topic_id=TopicId(type=stream_output_topic_type, source=self.id.key)
        )

        # 继续正常的智能体流程，将结果传递给可视化推荐智能体
        await self.publish_message(
            SqlResultMessage(
                query=message.query,
                sql=message.sql,
                explanation=message.explanation,
                results=results
            ),
            topic_id=TopicId(type=visualization_recommender_topic_type, source=self.id.key)
        )


# 数据可视化推荐智能体，负责建议合适的可视化方式
@type_subscription(topic_type=visualization_recommender_topic_type)
class VisualizationRecommenderAgent(RoutedAgent):
    def __init__(self):
        super().__init__("visualization_recommender_agent")
        self.model_client = model_client
        self._prompt = """```
        你是一名专业的数据可视化专家，负责根据提供的用户指令、SQL查询及其结果数据，推荐最合适的数据可视化方式，并给出详细的配置建议。
        
        ## 规则
        
        1.  **分析SQL查询：** 理解SQL查询的目标，例如是进行趋势分析、比较不同类别的数据、展示数据分布还是显示详细数据。
        2.  **分析查询结果数据结构：** 检查返回的数据包含哪些字段，它们的数据类型（数值型、分类型等），以及数据的组织方式（例如，是否包含时间序列、类别标签、数值指标等）。
        3.  **基于数据结构和查询目标推荐可视化类型：**
            * 如果数据涉及**时间序列**且需要展示**趋势**，推荐 `"line"` (折线图)。
            * 如果需要**比较不同类别**的**数值大小**，推荐 `"bar"` (柱状图)。
            * 如果需要展示**各部分占总体的比例**，且类别数量不多，推荐 `"pie"` (饼图)。需要确保数值型字段是总量的一部分。
            * 如果需要展示**两个数值变量之间的关系**或**数据点的分布**，推荐 `"scatter"` (散点图)。
            * 如果数据结构复杂、细节重要，或者无法找到合适的图表类型清晰表达，推荐 `"table"` (表格)。
        4.  **提供详细的可视化配置建议：** 根据选择的可视化类型，提供具体的配置参数。
            * **通用配置：** `"title"` (图表标题，应简洁明了地概括图表内容)。
            * **柱状图 (`"bar"`):**
                * `"xAxis"` (X轴字段名，通常是分类型字段)。
                * `"yAxis"` (Y轴字段名，通常是数值型字段)。
                * `"seriesName"` (系列名称，如果只有一个系列可以省略)。
            * **折线图 (`"line"`):**
                * `"xAxis"` (X轴字段名，通常是时间或有序的分类型字段)。
                * `"yAxis"` (Y轴字段名，通常是数值型字段)。
                * `"seriesName"` (系列名称，如果只有一个系列可以省略)。
            * **饼图 (`"pie"`):**
                * `"nameField"` (名称字段名，通常是分类型字段，用于显示饼图的标签)。
                * `"valueField"` (数值字段名，用于计算每个扇区的大小)。
                * `"seriesName"` (系列名称，如果只有一个系列可以省略)。
            * **散点图 (`"scatter"`):**
                * `"xAxis"` (X轴字段名，通常是数值型字段)。
                * `"yAxis"` (Y轴字段名，通常是数值型字段)。
                * `"seriesName"` (系列名称，如果只有一个系列可以省略)。
            * **表格 (`"table"`):** 不需要特定的坐标轴或系列配置，可以考虑添加 `"columns"` 字段，列出需要在表格中显示的字段名。
        5.  **输出格式必须符合如下JSON格式:**
        
            ```json
            {
                "type": "可视化类型",
                "config": {
                    "title": "图表标题",
                    "xAxis": "X轴字段名",
                    "yAxis": "Y轴字段名",
                    "seriesName": "系列名称"
                    // 其他配置参数根据可视化类型添加
                }
            }
            ```
        
            对于饼图：
        
            ```json
            {
                "type": "pie",
                "config": {
                    "title": "图表标题",
                    "nameField": "名称字段名",
                    "valueField": "数值字段名",
                    "seriesName": "系列名称"
                }
            }
            ```
        
            对于表格：
        
            ```json
            {
                "type": "table",
                "config": {
                    "title": "数据表格",
                    "columns": ["字段名1", "字段名2", ...]
                }
            }
            ```
        
        ## 支持的可视化类型
        
        - `"bar"`: 柱状图
        - `"line"`: 折线图
        - `"pie"`: 饼图
        - `"scatter"`: 散点图
        - `"table"`: 表格(对于不适合图表的数据)
        特别注意：如果用户有对生成的图表有明确的特定要求，一定要严格遵守用户的指令。例如用户明确要求生成饼状图，就不能生成柱状图。
        """

    @message_handler
    async def handle_message(self, message: SqlResultMessage, ctx: MessageContext) -> None:
        """处理接收到的消息，推荐可视化方式"""
        # 发送处理中消息
        await self.publish_message(
            ResponseMessage(source=VISUALIZATION_RECOMMENDER_NAME, content="正在分析数据，生成可视化建议..."),
            topic_id=TopicId(type=stream_output_topic_type, source=self.id.key)
        )
        results_json = json.dumps(message.results, ensure_ascii=False)
        self._prompt = self._prompt.replace("[sql]", message.sql).replace("[results]", results_json)
        agent = AssistantAgent(
            name="visualization_recommender",
            model_client=self.model_client,
            system_message=self._prompt,
            model_client_stream=True,
        )
        task = f"""
        ## 用户指令
         {message.query}
         
        ## 待分析的SQL查询
        {message.sql}
        
        ## SQL查询结果数据
        ```json
        {results_json}
        ```
        
        请根据提供的上述信息，分析并输出最合适的可视化类型和配置，输出必须是有效的JSON
        """
        
        result = await agent.run(task=task)
        visualization_json = result.messages[-1].content
        
        try:
            visualization = json.loads(visualization_json.replace("```json", "").replace("```", ""))
        except json.JSONDecodeError:
            visualization = {
                "type": "bar",
                "config": {
                    "title": "数据可视化",
                    "xAxis": list(message.results[0].keys())[0] if message.results else "x",
                    "yAxis": list(message.results[0].keys())[1] if message.results and len(message.results[0].keys()) > 1 else "y"
                }
            }

        # 如果是表格，则直接返回，因为表格已经在上个智能体中已经呈现
        if visualization.get("type") == "table":
            await self.publish_message(
                ResponseMessage(source=VISUALIZATION_RECOMMENDER_NAME, content="可视化分析已完成", is_final=True,),
                topic_id=TopicId(type=stream_output_topic_type, source=self.id.key)
            )
            return
        # 构建最终结果
        final_result = Text2SQLResponse(
            sql=message.sql,
            explanation=message.explanation,
            results=message.results,
            visualization_type=visualization.get("type", "bar"),
            visualization_config=visualization.get("config", {})
        )
        
        await self.publish_message(
            ResponseMessage(
                source=VISUALIZATION_RECOMMENDER_NAME,
                content="处理完成，返回最终结果",
                is_final=True,
                result=final_result.model_dump()
            ),
            topic_id=TopicId(type=stream_output_topic_type, source=self.id.key)
        )
        

class Text2SQLService:
    """Text2SQL服务类，处理自然语言到SQL转换的全流程"""
    
    def __init__(self, db_type: str = DB_TYPE):
        """初始化Text2SQL服务
        
        Args:
            db_type: 数据库类型，默认为DB_TYPE常量
        """
        self.db_type = db_type
    
    async def process_query(self, query: str, collector: StreamResponseCollector = None):
        """处理自然语言查询，返回SQL和结果"""
        # 创建运行时
        runtime = SingleThreadedAgentRuntime()

        # 使用register方法注册所有智能体
        await QueryAnalyzerAgent.register(runtime, query_analyzer_topic_type, 
                                         lambda: QueryAnalyzerAgent(db_type=self.db_type, input_func=collector.user_input))
        await SqlGeneratorAgent.register(runtime, sql_generator_topic_type, 
                                        lambda: SqlGeneratorAgent(db_type=self.db_type))
        await SqlExplainerAgent.register(runtime, sql_explainer_topic_type, 
                                        lambda: SqlExplainerAgent(db_type=self.db_type))
        await SqlExecutorAgent.register(runtime, sql_executor_topic_type, 
                                       lambda: SqlExecutorAgent())
        await VisualizationRecommenderAgent.register(runtime, visualization_recommender_topic_type, 
                                                   lambda: VisualizationRecommenderAgent())
        
        # 注册收集器
        await ClosureAgent.register_closure(
            runtime,
            "stream_collector_agent",
            collector.callback,
            subscriptions=lambda: [
                TypeSubscription(
                    topic_type=stream_output_topic_type, 
                    agent_type="stream_collector_agent"
                )
            ],
        )
        
        # 启动运行时
        runtime.start()
        
        # 发送初始消息
        await runtime.publish_message(
            QueryMessage(query=query), 
            topic_id=DefaultTopicId(type=query_analyzer_topic_type)
        )
        # 等待处理完成
        await runtime.stop_when_idle()
        
        # 关闭运行时
        await runtime.close()
        
