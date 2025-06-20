#!/usr/bin/env python3
"""
系统优化脚本
自动执行系统性能优化和配置调优
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.cache_manager import get_cache_manager
from app.core.graph_store import get_graph_store
from app.services.monitoring_service import monitoring_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemOptimizer:
    """系统优化器"""
    
    def __init__(self):
        """初始化优化器"""
        self.optimization_results = []
        self.performance_baseline = {}
        
    async def run_optimization(self):
        """运行完整的系统优化"""
        logger.info("🚀 开始系统优化...")
        
        try:
            # 1. 收集性能基线
            await self._collect_performance_baseline()
            
            # 2. 数据库优化
            await self._optimize_databases()
            
            # 3. 缓存优化
            await self._optimize_cache()
            
            # 4. 内存优化
            await self._optimize_memory()
            
            # 5. 网络优化
            await self._optimize_network()
            
            # 6. 文件系统优化
            await self._optimize_filesystem()
            
            # 7. 应用配置优化
            await self._optimize_application_config()
            
            # 8. 验证优化效果
            await self._verify_optimization_results()
            
            # 9. 生成优化报告
            await self._generate_optimization_report()
            
            logger.info("✅ 系统优化完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 系统优化失败: {str(e)}")
            return False
    
    async def _collect_performance_baseline(self):
        """收集性能基线"""
        logger.info("📊 收集性能基线...")
        
        try:
            # 获取当前系统指标
            current_metrics = await monitoring_service.get_current_metrics()
            
            self.performance_baseline = {
                "timestamp": time.time(),
                "system": current_metrics.get("system", {}),
                "application": current_metrics.get("application", {}),
                "model": current_metrics.get("model", {})
            }
            
            logger.info("✅ 性能基线收集完成")
            
        except Exception as e:
            logger.error(f"收集性能基线失败: {str(e)}")
    
    async def _optimize_databases(self):
        """优化数据库"""
        logger.info("🗄️ 优化数据库...")
        
        optimizations = []
        
        try:
            # Neo4j优化
            graph_store = get_graph_store()
            await graph_store.connect()
            
            # 检查并创建缺失的索引
            index_queries = [
                "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.type)",
                "CREATE INDEX entity_kb_idx IF NOT EXISTS FOR (e:Entity) ON (e.knowledge_base_id)",
                "CREATE INDEX document_title_idx IF NOT EXISTS FOR (d:Document) ON (d.title)"
            ]
            
            for query in index_queries:
                try:
                    await graph_store.execute_cypher(query)
                    optimizations.append(f"创建索引: {query}")
                except Exception as e:
                    logger.warning(f"索引创建跳过: {str(e)}")
            
            # 清理孤立节点
            cleanup_query = """
            MATCH (n)
            WHERE NOT (n)--()
            AND labels(n) <> ['TempNode']
            DELETE n
            """
            
            try:
                result = await graph_store.execute_cypher(cleanup_query)
                optimizations.append("清理孤立节点")
            except Exception as e:
                logger.warning(f"清理孤立节点失败: {str(e)}")
            
            self.optimization_results.append({
                "category": "数据库优化",
                "optimizations": optimizations,
                "status": "success"
            })
            
            logger.info("✅ 数据库优化完成")
            
        except Exception as e:
            logger.error(f"数据库优化失败: {str(e)}")
            self.optimization_results.append({
                "category": "数据库优化",
                "optimizations": [],
                "status": "failed",
                "error": str(e)
            })
    
    async def _optimize_cache(self):
        """优化缓存"""
        logger.info("💾 优化缓存...")
        
        optimizations = []
        
        try:
            cache_manager = get_cache_manager()
            await cache_manager.connect()
            
            # 获取缓存统计
            cache_stats = await cache_manager.get_stats()
            
            # 清理过期缓存
            categories_to_clean = ["search", "temp", "session"]
            for category in categories_to_clean:
                cleaned_count = await cache_manager.clear_category(category)
                if cleaned_count > 0:
                    optimizations.append(f"清理 {category} 缓存: {cleaned_count} 个键")
            
            # 优化缓存配置
            hit_rate = cache_stats.get("cache_stats", {}).get("hit_rate", 0)
            if hit_rate < 50:
                optimizations.append("缓存命中率较低，建议调整缓存策略")
            
            self.optimization_results.append({
                "category": "缓存优化",
                "optimizations": optimizations,
                "status": "success",
                "cache_stats": cache_stats
            })
            
            logger.info("✅ 缓存优化完成")
            
        except Exception as e:
            logger.error(f"缓存优化失败: {str(e)}")
            self.optimization_results.append({
                "category": "缓存优化",
                "optimizations": [],
                "status": "failed",
                "error": str(e)
            })
    
    async def _optimize_memory(self):
        """优化内存使用"""
        logger.info("🧠 优化内存使用...")
        
        optimizations = []
        
        try:
            import gc
            import psutil
            
            # 获取当前内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 强制垃圾回收
            collected = gc.collect()
            if collected > 0:
                optimizations.append(f"垃圾回收: 清理 {collected} 个对象")
            
            # 检查内存使用情况
            if memory_percent > 80:
                optimizations.append("内存使用率过高，建议增加内存或优化代码")
            elif memory_percent < 30:
                optimizations.append("内存使用率较低，可以考虑增加缓存大小")
            
            # 清理监控服务的历史数据
            old_metrics_count = len(monitoring_service.metrics_history)
            if old_metrics_count > 1000:
                monitoring_service.metrics_history = monitoring_service.metrics_history[-500:]
                optimizations.append(f"清理监控历史数据: {old_metrics_count - 500} 条")
            
            self.optimization_results.append({
                "category": "内存优化",
                "optimizations": optimizations,
                "status": "success",
                "memory_usage": memory_percent
            })
            
            logger.info("✅ 内存优化完成")
            
        except Exception as e:
            logger.error(f"内存优化失败: {str(e)}")
            self.optimization_results.append({
                "category": "内存优化",
                "optimizations": [],
                "status": "failed",
                "error": str(e)
            })
    
    async def _optimize_network(self):
        """优化网络配置"""
        logger.info("🌐 优化网络配置...")
        
        optimizations = []
        
        try:
            # 检查网络连接
            import psutil
            
            network_stats = psutil.net_io_counters()
            
            # 检查网络使用情况
            if network_stats.bytes_sent > 1024**3:  # 1GB
                optimizations.append("网络发送量较大，建议检查数据传输优化")
            
            if network_stats.bytes_recv > 1024**3:  # 1GB
                optimizations.append("网络接收量较大，建议检查数据接收优化")
            
            # 网络连接数检查
            connections = psutil.net_connections()
            active_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
            
            if active_connections > 100:
                optimizations.append(f"活跃连接数较多: {active_connections}")
            
            self.optimization_results.append({
                "category": "网络优化",
                "optimizations": optimizations,
                "status": "success",
                "network_stats": {
                    "bytes_sent": network_stats.bytes_sent,
                    "bytes_recv": network_stats.bytes_recv,
                    "active_connections": active_connections
                }
            })
            
            logger.info("✅ 网络优化完成")
            
        except Exception as e:
            logger.error(f"网络优化失败: {str(e)}")
            self.optimization_results.append({
                "category": "网络优化",
                "optimizations": [],
                "status": "failed",
                "error": str(e)
            })
    
    async def _optimize_filesystem(self):
        """优化文件系统"""
        logger.info("📁 优化文件系统...")
        
        optimizations = []
        
        try:
            import shutil
            
            # 清理临时文件
            temp_dirs = [
                project_root / "temp",
                project_root / "logs" / "old",
                project_root / "uploads" / "temp"
            ]
            
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    try:
                        shutil.rmtree(temp_dir)
                        temp_dir.mkdir(exist_ok=True)
                        optimizations.append(f"清理临时目录: {temp_dir}")
                    except Exception as e:
                        logger.warning(f"清理目录失败 {temp_dir}: {str(e)}")
            
            # 检查磁盘空间
            import psutil
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            if disk_percent > 90:
                optimizations.append("磁盘空间不足，建议清理或扩容")
            elif disk_percent > 80:
                optimizations.append("磁盘空间使用率较高，建议定期清理")
            
            # 日志文件轮转
            log_dir = project_root / "logs"
            if log_dir.exists():
                log_files = list(log_dir.glob("*.log"))
                large_logs = [f for f in log_files if f.stat().st_size > 100 * 1024 * 1024]  # 100MB
                
                for log_file in large_logs:
                    try:
                        # 压缩大日志文件
                        import gzip
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        log_file.unlink()
                        optimizations.append(f"压缩日志文件: {log_file.name}")
                    except Exception as e:
                        logger.warning(f"压缩日志文件失败 {log_file}: {str(e)}")
            
            self.optimization_results.append({
                "category": "文件系统优化",
                "optimizations": optimizations,
                "status": "success",
                "disk_usage": disk_percent
            })
            
            logger.info("✅ 文件系统优化完成")
            
        except Exception as e:
            logger.error(f"文件系统优化失败: {str(e)}")
            self.optimization_results.append({
                "category": "文件系统优化",
                "optimizations": [],
                "status": "failed",
                "error": str(e)
            })
    
    async def _optimize_application_config(self):
        """优化应用配置"""
        logger.info("⚙️ 优化应用配置...")
        
        optimizations = []
        
        try:
            # 检查环境变量配置
            env_vars_to_check = [
                "REDIS_URL",
                "NEO4J_URI",
                "DEEPSEEK_API_KEY",
                "QWEN_API_KEY"
            ]
            
            missing_vars = []
            for var in env_vars_to_check:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                optimizations.append(f"缺少环境变量: {', '.join(missing_vars)}")
            
            # 检查配置文件
            config_files = [
                project_root / ".env",
                project_root / "docker-compose.yml"
            ]
            
            for config_file in config_files:
                if not config_file.exists():
                    optimizations.append(f"缺少配置文件: {config_file.name}")
            
            # 优化建议
            optimizations.extend([
                "建议启用生产环境配置",
                "建议配置日志轮转",
                "建议启用监控告警",
                "建议配置备份策略"
            ])
            
            self.optimization_results.append({
                "category": "应用配置优化",
                "optimizations": optimizations,
                "status": "success"
            })
            
            logger.info("✅ 应用配置优化完成")
            
        except Exception as e:
            logger.error(f"应用配置优化失败: {str(e)}")
            self.optimization_results.append({
                "category": "应用配置优化",
                "optimizations": [],
                "status": "failed",
                "error": str(e)
            })
    
    async def _verify_optimization_results(self):
        """验证优化效果"""
        logger.info("🔍 验证优化效果...")
        
        try:
            # 等待一段时间让系统稳定
            await asyncio.sleep(5)
            
            # 收集优化后的指标
            current_metrics = await monitoring_service.get_current_metrics()
            
            # 比较优化前后的性能
            comparison = {
                "before": self.performance_baseline,
                "after": {
                    "timestamp": time.time(),
                    "system": current_metrics.get("system", {}),
                    "application": current_metrics.get("application", {}),
                    "model": current_metrics.get("model", {})
                }
            }
            
            self.optimization_results.append({
                "category": "优化效果验证",
                "comparison": comparison,
                "status": "success"
            })
            
            logger.info("✅ 优化效果验证完成")
            
        except Exception as e:
            logger.error(f"优化效果验证失败: {str(e)}")
    
    async def _generate_optimization_report(self):
        """生成优化报告"""
        logger.info("📋 生成优化报告...")
        
        try:
            report = {
                "optimization_time": time.time(),
                "total_optimizations": len(self.optimization_results),
                "successful_optimizations": len([r for r in self.optimization_results if r["status"] == "success"]),
                "failed_optimizations": len([r for r in self.optimization_results if r["status"] == "failed"]),
                "results": self.optimization_results,
                "recommendations": [
                    "定期运行系统优化脚本",
                    "监控系统性能指标",
                    "及时清理临时文件和缓存",
                    "保持数据库索引优化",
                    "配置自动化监控告警"
                ]
            }
            
            # 保存报告
            report_file = project_root / "optimization_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 优化报告已保存: {report_file}")
            
            # 打印摘要
            print("\n" + "="*60)
            print("🎉 系统优化完成摘要")
            print("="*60)
            print(f"总优化项目: {report['total_optimizations']}")
            print(f"成功项目: {report['successful_optimizations']}")
            print(f"失败项目: {report['failed_optimizations']}")
            print("\n优化类别:")
            
            for result in self.optimization_results:
                status_icon = "✅" if result["status"] == "success" else "❌"
                print(f"  {status_icon} {result['category']}: {len(result.get('optimizations', []))} 项优化")
            
            print(f"\n详细报告: {report_file}")
            print("="*60)
            
        except Exception as e:
            logger.error(f"生成优化报告失败: {str(e)}")


async def main():
    """主函数"""
    print("🚀 智能客服系统优化工具")
    print("="*50)
    
    optimizer = SystemOptimizer()
    success = await optimizer.run_optimization()
    
    if success:
        print("\n🎉 系统优化成功完成！")
        return 0
    else:
        print("\n❌ 系统优化失败，请检查日志")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
