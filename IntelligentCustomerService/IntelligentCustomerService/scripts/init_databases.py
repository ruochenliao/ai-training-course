#!/usr/bin/env python3
"""
数据库初始化脚本
初始化MySQL、Milvus、Neo4j等数据库
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化数据库初始化器
        
        Args:
            config_file: 配置文件路径
        """
        self.config = self._load_config(config_file)
        self.mysql_initialized = False
        self.milvus_initialized = False
        self.neo4j_initialized = False
        self.redis_initialized = False
    
    def _load_config(self, config_file: Optional[str] = None) -> Dict:
        """加载配置"""
        default_config = {
            "mysql": {
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "root_password",
                "database": "intelligent_customer_service",
                "charset": "utf8mb4"
            },
            "milvus": {
                "host": "localhost",
                "port": 19530,
                "user": "",
                "password": "",
                "db_name": "default"
            },
            "neo4j": {
                "uri": "bolt://localhost:7687",
                "user": "neo4j",
                "password": "neo4j_password"
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "password": "",
                "db": 0
            }
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # 合并配置
                    for key, value in file_config.items():
                        if key in default_config:
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                logger.warning(f"加载配置文件失败: {str(e)}, 使用默认配置")
        
        return default_config
    
    async def check_dependencies(self) -> bool:
        """检查依赖包"""
        logger.info("检查数据库依赖包...")
        
        required_packages = {
            "aiomysql": "MySQL连接",
            "pymilvus": "Milvus向量数据库",
            "neo4j": "Neo4j图数据库",
            "redis": "Redis缓存"
        }
        
        missing_packages = []
        
        for package, description in required_packages.items():
            try:
                __import__(package)
                logger.info(f"✅ {description}: {package}")
            except ImportError:
                logger.error(f"❌ {description}: {package} 未安装")
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"缺少依赖包: {', '.join(missing_packages)}")
            logger.info("请运行: pip install " + " ".join(missing_packages))
            return False
        
        return True
    
    async def init_mysql(self) -> bool:
        """初始化MySQL数据库"""
        try:
            logger.info("初始化MySQL数据库...")
            
            import aiomysql
            
            mysql_config = self.config["mysql"]
            
            # 连接到MySQL服务器（不指定数据库）
            connection = await aiomysql.connect(
                host=mysql_config["host"],
                port=mysql_config["port"],
                user=mysql_config["user"],
                password=mysql_config["password"],
                charset=mysql_config["charset"]
            )
            
            try:
                cursor = await connection.cursor()
                
                # 创建数据库
                database_name = mysql_config["database"]
                await cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                logger.info(f"数据库 {database_name} 创建成功")
                
                # 创建用户（如果需要）
                if mysql_config.get("create_user"):
                    user_name = mysql_config.get("app_user", "ics_user")
                    user_password = mysql_config.get("app_password", "ics_password")
                    
                    await cursor.execute(f"CREATE USER IF NOT EXISTS '{user_name}'@'%' IDENTIFIED BY '{user_password}'")
                    await cursor.execute(f"GRANT ALL PRIVILEGES ON `{database_name}`.* TO '{user_name}'@'%'")
                    await cursor.execute("FLUSH PRIVILEGES")
                    logger.info(f"用户 {user_name} 创建成功")
                
                await connection.commit()
                
            finally:
                await cursor.close()
                await connection.ensure_closed()
            
            # 测试连接到新数据库
            test_connection = await aiomysql.connect(
                host=mysql_config["host"],
                port=mysql_config["port"],
                user=mysql_config["user"],
                password=mysql_config["password"],
                db=mysql_config["database"],
                charset=mysql_config["charset"]
            )
            
            await test_connection.ensure_closed()
            
            self.mysql_initialized = True
            logger.info("✅ MySQL数据库初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ MySQL数据库初始化失败: {str(e)}")
            return False
    
    async def init_milvus(self) -> bool:
        """初始化Milvus向量数据库"""
        try:
            logger.info("初始化Milvus向量数据库...")
            
            from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType
            
            milvus_config = self.config["milvus"]
            
            # 连接到Milvus
            connections.connect(
                alias="default",
                host=milvus_config["host"],
                port=milvus_config["port"],
                user=milvus_config.get("user", ""),
                password=milvus_config.get("password", "")
            )
            
            logger.info("Milvus连接成功")
            
            # 创建集合
            collections_to_create = [
                {
                    "name": "documents",
                    "description": "文档向量集合",
                    "dimension": 1536
                },
                {
                    "name": "conversations",
                    "description": "对话向量集合", 
                    "dimension": 1536
                },
                {
                    "name": "knowledge",
                    "description": "知识库向量集合",
                    "dimension": 1536
                }
            ]
            
            for collection_info in collections_to_create:
                collection_name = collection_info["name"]
                
                # 检查集合是否已存在
                if utility.has_collection(collection_name):
                    logger.info(f"集合 {collection_name} 已存在，跳过创建")
                    continue
                
                # 创建集合Schema
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=collection_info["dimension"]),
                    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="metadata", dtype=DataType.JSON),
                    FieldSchema(name="timestamp", dtype=DataType.INT64),
                    FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
                    FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=256)
                ]
                
                schema = CollectionSchema(
                    fields=fields,
                    description=collection_info["description"]
                )
                
                # 创建集合
                collection = Collection(
                    name=collection_name,
                    schema=schema
                )
                
                # 创建索引
                index_params = {
                    "index_type": "HNSW",
                    "metric_type": "COSINE",
                    "params": {"M": 16, "efConstruction": 200}
                }
                
                collection.create_index(
                    field_name="vector",
                    index_params=index_params
                )
                
                logger.info(f"集合 {collection_name} 创建成功")
            
            # 断开连接
            connections.disconnect("default")
            
            self.milvus_initialized = True
            logger.info("✅ Milvus向量数据库初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ Milvus向量数据库初始化失败: {str(e)}")
            return False
    
    async def init_neo4j(self) -> bool:
        """初始化Neo4j图数据库"""
        try:
            logger.info("初始化Neo4j图数据库...")
            
            from neo4j import AsyncGraphDatabase
            
            neo4j_config = self.config["neo4j"]
            
            # 连接到Neo4j
            driver = AsyncGraphDatabase.driver(
                neo4j_config["uri"],
                auth=(neo4j_config["user"], neo4j_config["password"])
            )
            
            async with driver.session() as session:
                # 测试连接
                result = await session.run("RETURN 1 as test")
                await result.single()
                
                # 创建约束和索引
                constraints_and_indexes = [
                    # 实体节点约束
                    "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                    
                    # 用户节点约束
                    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
                    
                    # 知识库节点约束
                    "CREATE CONSTRAINT kb_id IF NOT EXISTS FOR (kb:KnowledgeBase) REQUIRE kb.id IS UNIQUE",
                    
                    # 文档节点约束
                    "CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                    
                    # 创建索引
                    "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                    "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
                    "CREATE INDEX user_name IF NOT EXISTS FOR (u:User) ON (u.name)",
                    "CREATE INDEX doc_title IF NOT EXISTS FOR (d:Document) ON (d.title)"
                ]
                
                for query in constraints_and_indexes:
                    try:
                        await session.run(query)
                        logger.debug(f"执行成功: {query}")
                    except Exception as e:
                        logger.warning(f"执行失败: {query}, 错误: {str(e)}")
                
                # 创建一些示例节点
                sample_data = [
                    "MERGE (kb:KnowledgeBase {id: 'default', name: '默认知识库', type: 'public'})",
                    "MERGE (kb:KnowledgeBase {id: 'private', name: '私有知识库', type: 'private'})"
                ]
                
                for query in sample_data:
                    await session.run(query)
                
                logger.info("Neo4j约束和索引创建成功")
            
            await driver.close()
            
            self.neo4j_initialized = True
            logger.info("✅ Neo4j图数据库初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ Neo4j图数据库初始化失败: {str(e)}")
            return False
    
    async def init_redis(self) -> bool:
        """初始化Redis缓存"""
        try:
            logger.info("初始化Redis缓存...")
            
            import redis.asyncio as redis
            
            redis_config = self.config["redis"]
            
            # 连接到Redis
            redis_client = redis.Redis(
                host=redis_config["host"],
                port=redis_config["port"],
                password=redis_config.get("password") or None,
                db=redis_config["db"],
                decode_responses=True
            )
            
            # 测试连接
            await redis_client.ping()
            
            # 设置一些初始配置
            await redis_client.set("system:initialized", "true")
            await redis_client.set("system:init_time", str(int(asyncio.get_event_loop().time())))
            
            # 创建一些默认的键空间
            namespaces = [
                "session:",     # 会话缓存
                "model:",       # 模型缓存
                "search:",      # 搜索缓存
                "user:",        # 用户缓存
                "config:"       # 配置缓存
            ]
            
            for namespace in namespaces:
                await redis_client.set(f"{namespace}initialized", "true", ex=86400)  # 24小时过期
            
            await redis_client.close()
            
            self.redis_initialized = True
            logger.info("✅ Redis缓存初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ Redis缓存初始化失败: {str(e)}")
            return False
    
    async def init_all_databases(self) -> Dict[str, bool]:
        """初始化所有数据库"""
        logger.info("开始初始化所有数据库...")
        
        results = {}
        
        # 检查依赖
        if not await self.check_dependencies():
            return {"dependencies": False}
        
        # 初始化MySQL
        results["mysql"] = await self.init_mysql()
        
        # 初始化Milvus
        results["milvus"] = await self.init_milvus()
        
        # 初始化Neo4j
        results["neo4j"] = await self.init_neo4j()
        
        # 初始化Redis
        results["redis"] = await self.init_redis()
        
        return results
    
    async def verify_databases(self) -> Dict[str, bool]:
        """验证数据库连接"""
        logger.info("验证数据库连接...")
        
        results = {}
        
        # 验证MySQL
        try:
            import aiomysql
            mysql_config = self.config["mysql"]
            connection = await aiomysql.connect(
                host=mysql_config["host"],
                port=mysql_config["port"],
                user=mysql_config["user"],
                password=mysql_config["password"],
                db=mysql_config["database"]
            )
            await connection.ensure_closed()
            results["mysql"] = True
            logger.info("✅ MySQL连接验证成功")
        except Exception as e:
            results["mysql"] = False
            logger.error(f"❌ MySQL连接验证失败: {str(e)}")
        
        # 验证Milvus
        try:
            from pymilvus import connections, utility
            milvus_config = self.config["milvus"]
            connections.connect(
                alias="verify",
                host=milvus_config["host"],
                port=milvus_config["port"]
            )
            # 列出集合
            collections = utility.list_collections()
            connections.disconnect("verify")
            results["milvus"] = True
            logger.info(f"✅ Milvus连接验证成功，集合数量: {len(collections)}")
        except Exception as e:
            results["milvus"] = False
            logger.error(f"❌ Milvus连接验证失败: {str(e)}")
        
        # 验证Neo4j
        try:
            from neo4j import AsyncGraphDatabase
            neo4j_config = self.config["neo4j"]
            driver = AsyncGraphDatabase.driver(
                neo4j_config["uri"],
                auth=(neo4j_config["user"], neo4j_config["password"])
            )
            async with driver.session() as session:
                result = await session.run("RETURN 1 as test")
                await result.single()
            await driver.close()
            results["neo4j"] = True
            logger.info("✅ Neo4j连接验证成功")
        except Exception as e:
            results["neo4j"] = False
            logger.error(f"❌ Neo4j连接验证失败: {str(e)}")
        
        # 验证Redis
        try:
            import redis.asyncio as redis
            redis_config = self.config["redis"]
            redis_client = redis.Redis(
                host=redis_config["host"],
                port=redis_config["port"],
                password=redis_config.get("password") or None,
                db=redis_config["db"]
            )
            await redis_client.ping()
            await redis_client.close()
            results["redis"] = True
            logger.info("✅ Redis连接验证成功")
        except Exception as e:
            results["redis"] = False
            logger.error(f"❌ Redis连接验证失败: {str(e)}")
        
        return results


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="初始化智能客服系统数据库")
    parser.add_argument(
        "--config",
        help="配置文件路径"
    )
    parser.add_argument(
        "--database",
        choices=["mysql", "milvus", "neo4j", "redis", "all"],
        default="all",
        help="要初始化的数据库类型 (默认: all)"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="仅验证数据库连接，不进行初始化"
    )
    
    args = parser.parse_args()
    
    # 创建初始化器
    initializer = DatabaseInitializer(args.config)
    
    try:
        if args.verify_only:
            logger.info("验证数据库连接...")
            results = await initializer.verify_databases()
        else:
            if args.database == "all":
                logger.info("初始化所有数据库...")
                results = await initializer.init_all_databases()
            else:
                logger.info(f"初始化 {args.database} 数据库...")
                if args.database == "mysql":
                    results = {"mysql": await initializer.init_mysql()}
                elif args.database == "milvus":
                    results = {"milvus": await initializer.init_milvus()}
                elif args.database == "neo4j":
                    results = {"neo4j": await initializer.init_neo4j()}
                elif args.database == "redis":
                    results = {"redis": await initializer.init_redis()}
        
        # 输出结果摘要
        print("\n" + "="*60)
        print("数据库初始化结果摘要")
        print("="*60)
        
        success_count = 0
        for db_name, success in results.items():
            if success:
                print(f"✅ {db_name.upper()}: 成功")
                success_count += 1
            else:
                print(f"❌ {db_name.upper()}: 失败")
        
        print(f"\n成功初始化: {success_count}/{len(results)} 个数据库")
        
        if success_count == len(results):
            print("\n🎉 所有数据库初始化完成！")
        else:
            print("\n⚠️  部分数据库初始化失败，请检查配置和日志信息。")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("用户中断初始化")
        sys.exit(1)
    except Exception as e:
        logger.error(f"初始化过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
