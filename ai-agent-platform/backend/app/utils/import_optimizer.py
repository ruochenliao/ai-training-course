# Copyright (c) 2025 左岚. All rights reserved.
"""
导入优化工具 - 自动优化Python导入语句
"""

# # Standard library imports
import ast
from collections import defaultdict
import logging
import os
from pathlib import Path
import re
from typing import Dict, List, Optional, Set, Tuple

# # Third-party imports
import isort
from isort import Config

logger = logging.getLogger(__name__)


class ImportOptimizer:
    """导入优化器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.app_root = self.project_root / "app"
        
        # isort配置
        self.isort_config = Config(
            profile="black",
            multi_line_output=3,
            include_trailing_comma=True,
            force_grid_wrap=0,
            use_parentheses=True,
            ensure_newline_before_comments=True,
            line_length=88,
            known_first_party=["app"],
            known_third_party=[
                "fastapi", "sqlalchemy", "pydantic", "redis", "celery",
                "openai", "langchain", "transformers", "torch", "numpy",
                "pandas", "pytest", "uvicorn", "alembic", "pymysql",
                "minio", "pymilvus", "structlog", "prometheus_client"
            ],
            sections=["FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"],
            import_heading_future="# Future imports",
            import_heading_stdlib="# Standard library imports", 
            import_heading_thirdparty="# Third-party imports",
            import_heading_firstparty="# Local application imports",
            import_heading_localfolder="# Local folder imports",
            force_sort_within_sections=True,
            order_by_type=True,
            group_by_package=True,
            combine_as_imports=True,
            force_single_line=False,
            single_line_exclusions=["typing"],
            remove_redundant_aliases=True,
            honor_noqa=True,
        )
    
    def analyze_file(self, file_path: Path) -> Dict[str, any]:
        """分析Python文件的导入情况"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            analysis = {
                'file_path': str(file_path),
                'imports': [],
                'from_imports': [],
                'unused_imports': [],
                'duplicate_imports': [],
                'circular_imports': [],
                'issues': []
            }
            
            # 收集所有导入
            imports = []
            from_imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'module': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno
                        })
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        from_imports.append({
                            'module': module,
                            'name': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno,
                            'level': node.level
                        })
            
            analysis['imports'] = imports
            analysis['from_imports'] = from_imports
            
            # 检测重复导入
            seen_imports = set()
            for imp in imports + from_imports:
                import_key = f"{imp.get('module', '')}.{imp.get('name', imp.get('module', ''))}"
                if import_key in seen_imports:
                    analysis['duplicate_imports'].append(imp)
                else:
                    seen_imports.add(import_key)
            
            # 检测未使用的导入
            analysis['unused_imports'] = self._find_unused_imports(content, imports, from_imports)
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析文件失败 {file_path}: {e}")
            return {'error': str(e)}
    
    def _find_unused_imports(self, content: str, imports: List[Dict], from_imports: List[Dict]) -> List[Dict]:
        """查找未使用的导入"""
        unused = []
        
        # 简单的文本搜索检测（可以改进为AST分析）
        for imp in imports:
            module_name = imp['alias'] or imp['module'].split('.')[-1]
            if not re.search(rf'\b{re.escape(module_name)}\b', content[content.find('\n', content.find(f"import {imp['module']}")):]):
                unused.append(imp)
        
        for imp in from_imports:
            name = imp['alias'] or imp['name']
            if name != '*' and not re.search(rf'\b{re.escape(name)}\b', content[content.find('\n', content.find(f"from {imp['module']}")):]):
                unused.append(imp)
        
        return unused
    
    def optimize_file(self, file_path: Path) -> Dict[str, any]:
        """优化单个文件的导入"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # 使用isort优化导入
            optimized_content = isort.code(original_content, config=self.isort_config)
            
            # 添加版权声明（如果没有）
            if not optimized_content.startswith('# Copyright'):
                copyright_header = "# Copyright (c) 2025 左岚. All rights reserved.\n"
                
                # 查找第一个非注释、非空行
                lines = optimized_content.split('\n')
                insert_index = 0
                
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                        insert_index = i
                        break
                
                lines.insert(insert_index, copyright_header)
                optimized_content = '\n'.join(lines)
            
            # 检查是否有变化
            if original_content != optimized_content:
                # 备份原文件
                backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # 写入优化后的内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(optimized_content)
                
                logger.info(f"优化文件: {file_path}")
                return {
                    'status': 'optimized',
                    'file_path': str(file_path),
                    'backup_path': str(backup_path),
                    'changes': True
                }
            else:
                return {
                    'status': 'no_changes',
                    'file_path': str(file_path),
                    'changes': False
                }
                
        except Exception as e:
            logger.error(f"优化文件失败 {file_path}: {e}")
            return {
                'status': 'error',
                'file_path': str(file_path),
                'error': str(e)
            }
    
    def optimize_directory(self, directory: Path = None) -> Dict[str, any]:
        """优化目录中的所有Python文件"""
        if directory is None:
            directory = self.app_root
        
        results = {
            'total_files': 0,
            'optimized_files': 0,
            'error_files': 0,
            'no_change_files': 0,
            'file_results': []
        }
        
        # 查找所有Python文件
        python_files = list(directory.rglob('*.py'))
        results['total_files'] = len(python_files)
        
        for file_path in python_files:
            # 跳过虚拟环境和缓存目录
            if any(part in str(file_path) for part in ['venv', '__pycache__', '.git', 'node_modules']):
                continue
            
            result = self.optimize_file(file_path)
            results['file_results'].append(result)
            
            if result['status'] == 'optimized':
                results['optimized_files'] += 1
            elif result['status'] == 'error':
                results['error_files'] += 1
            else:
                results['no_change_files'] += 1
        
        logger.info(f"导入优化完成: {results['optimized_files']}/{results['total_files']} 文件已优化")
        return results
    
    def analyze_project_imports(self) -> Dict[str, any]:
        """分析整个项目的导入情况"""
        analysis = {
            'total_files': 0,
            'total_imports': 0,
            'unused_imports': 0,
            'duplicate_imports': 0,
            'circular_imports': 0,
            'import_graph': defaultdict(set),
            'module_usage': defaultdict(int),
            'issues': []
        }
        
        python_files = list(self.app_root.rglob('*.py'))
        analysis['total_files'] = len(python_files)
        
        for file_path in python_files:
            if any(part in str(file_path) for part in ['venv', '__pycache__', '.git']):
                continue
            
            file_analysis = self.analyze_file(file_path)
            
            if 'error' in file_analysis:
                analysis['issues'].append(f"分析失败: {file_path} - {file_analysis['error']}")
                continue
            
            # 统计导入
            analysis['total_imports'] += len(file_analysis['imports']) + len(file_analysis['from_imports'])
            analysis['unused_imports'] += len(file_analysis['unused_imports'])
            analysis['duplicate_imports'] += len(file_analysis['duplicate_imports'])
            
            # 构建导入图
            for imp in file_analysis['imports'] + file_analysis['from_imports']:
                module = imp.get('module', '')
                if module:
                    analysis['import_graph'][str(file_path)].add(module)
                    analysis['module_usage'][module] += 1
        
        # 检测循环导入
        analysis['circular_imports'] = self._detect_circular_imports(analysis['import_graph'])
        
        return analysis
    
    def _detect_circular_imports(self, import_graph: Dict[str, Set[str]]) -> List[List[str]]:
        """检测循环导入"""
        # 简化的循环检测算法
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            if node in rec_stack:
                # 找到循环
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in import_graph.get(node, []):
                dfs(neighbor, path + [neighbor])
            
            rec_stack.remove(node)
        
        for node in import_graph:
            if node not in visited:
                dfs(node, [node])
        
        return cycles
    
    def generate_report(self) -> str:
        """生成导入分析报告"""
        analysis = self.analyze_project_imports()
        
        report = f"""
# 导入分析报告

## 总体统计
- 总文件数: {analysis['total_files']}
- 总导入数: {analysis['total_imports']}
- 未使用导入: {analysis['unused_imports']}
- 重复导入: {analysis['duplicate_imports']}
- 循环导入: {len(analysis['circular_imports'])}

## 最常用模块
"""
        
        # 最常用的模块
        sorted_modules = sorted(analysis['module_usage'].items(), key=lambda x: x[1], reverse=True)
        for module, count in sorted_modules[:10]:
            report += f"- {module}: {count} 次\n"
        
        # 问题报告
        if analysis['issues']:
            report += "\n## 问题\n"
            for issue in analysis['issues']:
                report += f"- {issue}\n"
        
        # 循环导入
        if analysis['circular_imports']:
            report += "\n## 循环导入\n"
            for cycle in analysis['circular_imports']:
                report += f"- {' -> '.join(cycle)}\n"
        
        return report
    
    def cleanup_unused_imports(self) -> Dict[str, any]:
        """清理未使用的导入"""
        results = {
            'cleaned_files': 0,
            'removed_imports': 0,
            'errors': []
        }
        
        python_files = list(self.app_root.rglob('*.py'))
        
        for file_path in python_files:
            if any(part in str(file_path) for part in ['venv', '__pycache__', '.git']):
                continue
            
            try:
                analysis = self.analyze_file(file_path)
                
                if analysis.get('unused_imports'):
                    # 这里可以实现自动移除未使用导入的逻辑
                    # 为了安全起见，目前只记录
                    results['cleaned_files'] += 1
                    results['removed_imports'] += len(analysis['unused_imports'])
                    
                    logger.info(f"发现未使用导入: {file_path} - {len(analysis['unused_imports'])} 个")
                    
            except Exception as e:
                results['errors'].append(f"{file_path}: {e}")
        
        return results


def optimize_imports(project_root: str = None) -> Dict[str, any]:
    """优化项目导入的便捷函数"""
    if project_root is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    optimizer = ImportOptimizer(project_root)
    return optimizer.optimize_directory()


def analyze_imports(project_root: str = None) -> Dict[str, any]:
    """分析项目导入的便捷函数"""
    if project_root is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    optimizer = ImportOptimizer(project_root)
    return optimizer.analyze_project_imports()


if __name__ == "__main__":
    # 运行导入优化
    optimizer = ImportOptimizer(".")
    
    print("开始导入优化...")
    results = optimizer.optimize_directory()
    print(f"优化完成: {results['optimized_files']}/{results['total_files']} 文件已优化")
    
    print("\n生成分析报告...")
    report = optimizer.generate_report()
    print(report)
