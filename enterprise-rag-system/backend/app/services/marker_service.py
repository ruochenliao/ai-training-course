"""
Marker文档解析服务
"""

import os
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

from loguru import logger
import fitz  # PyMuPDF
from docx import Document
from pptx import Presentation
import pandas as pd

from app.core.config import settings
from app.core.exceptions import DocumentProcessingException


class MarkerService:
    """Marker文档解析服务类"""
    
    def __init__(self):
        """初始化Marker服务"""
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.supported_formats = {
            '.pdf': self._parse_pdf,
            '.docx': self._parse_docx,
            '.doc': self._parse_docx,
            '.pptx': self._parse_pptx,
            '.ppt': self._parse_pptx,
            '.txt': self._parse_txt,
            '.md': self._parse_txt,
            '.html': self._parse_html,
            '.htm': self._parse_html,
            '.csv': self._parse_csv,
            '.xlsx': self._parse_excel,
            '.xls': self._parse_excel,
            '.json': self._parse_json
        }
        logger.info("Marker文档解析服务初始化完成")
    
    async def parse_document(
        self,
        file_path: str,
        file_name: str,
        extract_images: bool = True,
        extract_tables: bool = True
    ) -> Dict[str, Any]:
        """
        解析文档
        
        Args:
            file_path: 文件路径
            file_name: 文件名
            extract_images: 是否提取图片
            extract_tables: 是否提取表格
            
        Returns:
            解析结果字典
        """
        try:
            # 获取文件扩展名
            file_ext = Path(file_name).suffix.lower()
            
            if file_ext not in self.supported_formats:
                raise DocumentProcessingException(f"不支持的文件格式: {file_ext}")
            
            # 在线程池中执行解析
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._parse_document_sync,
                file_path,
                file_name,
                file_ext,
                extract_images,
                extract_tables
            )
            
            logger.info(f"文档解析完成: {file_name}")
            return result
            
        except Exception as e:
            logger.error(f"文档解析失败 {file_name}: {e}")
            raise DocumentProcessingException(f"文档解析失败: {e}")
    
    def _parse_document_sync(
        self,
        file_path: str,
        file_name: str,
        file_ext: str,
        extract_images: bool,
        extract_tables: bool
    ) -> Dict[str, Any]:
        """同步解析文档"""
        parser_func = self.supported_formats[file_ext]
        
        result = {
            'file_name': file_name,
            'file_path': file_path,
            'file_type': file_ext,
            'content': '',
            'metadata': {},
            'images': [],
            'tables': [],
            'structure': {},
            'page_count': 0,
            'word_count': 0
        }
        
        # 调用对应的解析函数
        parsed_data = parser_func(file_path, extract_images, extract_tables)
        result.update(parsed_data)
        
        # 计算字数
        if result['content']:
            result['word_count'] = len(result['content'].split())
        
        return result
    
    def _parse_pdf(self, file_path: str, extract_images: bool, extract_tables: bool) -> Dict[str, Any]:
        """解析PDF文件"""
        try:
            doc = fitz.open(file_path)
            content_parts = []
            images = []
            tables = []
            metadata = {}
            
            # 获取文档元数据
            metadata.update({
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'creator': doc.metadata.get('creator', ''),
                'producer': doc.metadata.get('producer', ''),
                'creation_date': doc.metadata.get('creationDate', ''),
                'modification_date': doc.metadata.get('modDate', '')
            })
            
            # 逐页处理
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 提取文本
                text = page.get_text()
                if text.strip():
                    content_parts.append(f"## 第{page_num + 1}页\n\n{text}\n")
                
                # 提取图片
                if extract_images:
                    image_list = page.get_images()
                    for img_index, img in enumerate(image_list):
                        try:
                            xref = img[0]
                            pix = fitz.Pixmap(doc, xref)
                            if pix.n - pix.alpha < 4:  # 确保是RGB或灰度图
                                img_data = pix.tobytes("png")
                                images.append({
                                    'page': page_num + 1,
                                    'index': img_index,
                                    'data': img_data,
                                    'width': pix.width,
                                    'height': pix.height
                                })
                            pix = None
                        except Exception as e:
                            logger.warning(f"提取图片失败 page {page_num + 1}, img {img_index}: {e}")
                
                # 提取表格（简单实现）
                if extract_tables:
                    tables_on_page = page.find_tables()
                    for table_index, table in enumerate(tables_on_page):
                        try:
                            table_data = table.extract()
                            tables.append({
                                'page': page_num + 1,
                                'index': table_index,
                                'data': table_data,
                                'bbox': table.bbox
                            })
                        except Exception as e:
                            logger.warning(f"提取表格失败 page {page_num + 1}, table {table_index}: {e}")
            
            doc.close()
            
            return {
                'content': '\n'.join(content_parts),
                'metadata': metadata,
                'images': images,
                'tables': tables,
                'page_count': len(doc),
                'structure': {'type': 'pdf', 'pages': len(doc)}
            }
            
        except Exception as e:
            logger.error(f"PDF解析失败: {e}")
            raise DocumentProcessingException(f"PDF解析失败: {e}")
    
    def _parse_docx(self, file_path: str, extract_images: bool, extract_tables: bool) -> Dict[str, Any]:
        """解析DOCX文件"""
        try:
            doc = Document(file_path)
            content_parts = []
            images = []
            tables = []
            
            # 获取文档属性
            metadata = {
                'title': doc.core_properties.title or '',
                'author': doc.core_properties.author or '',
                'subject': doc.core_properties.subject or '',
                'created': str(doc.core_properties.created) if doc.core_properties.created else '',
                'modified': str(doc.core_properties.modified) if doc.core_properties.modified else ''
            }
            
            # 提取段落文本
            for para in doc.paragraphs:
                if para.text.strip():
                    # 根据样式添加标记
                    if para.style.name.startswith('Heading'):
                        level = para.style.name.replace('Heading ', '')
                        content_parts.append(f"{'#' * int(level)} {para.text}\n")
                    else:
                        content_parts.append(f"{para.text}\n")
            
            # 提取表格
            if extract_tables:
                for table_index, table in enumerate(doc.tables):
                    table_data = []
                    for row in table.rows:
                        row_data = [cell.text.strip() for cell in row.cells]
                        table_data.append(row_data)
                    
                    tables.append({
                        'index': table_index,
                        'data': table_data,
                        'rows': len(table.rows),
                        'cols': len(table.columns) if table.rows else 0
                    })
            
            # 提取图片（简化实现）
            if extract_images:
                # 这里可以扩展图片提取逻辑
                pass
            
            return {
                'content': '\n'.join(content_parts),
                'metadata': metadata,
                'images': images,
                'tables': tables,
                'page_count': 1,  # Word文档没有固定页数概念
                'structure': {'type': 'docx', 'paragraphs': len(doc.paragraphs), 'tables': len(doc.tables)}
            }
            
        except Exception as e:
            logger.error(f"DOCX解析失败: {e}")
            raise DocumentProcessingException(f"DOCX解析失败: {e}")
    
    def _parse_pptx(self, file_path: str, extract_images: bool, extract_tables: bool) -> Dict[str, Any]:
        """解析PPTX文件"""
        try:
            prs = Presentation(file_path)
            content_parts = []
            images = []
            tables = []
            
            # 获取演示文稿属性
            metadata = {
                'title': prs.core_properties.title or '',
                'author': prs.core_properties.author or '',
                'subject': prs.core_properties.subject or '',
                'created': str(prs.core_properties.created) if prs.core_properties.created else '',
                'modified': str(prs.core_properties.modified) if prs.core_properties.modified else ''
            }
            
            # 逐幻灯片处理
            for slide_index, slide in enumerate(prs.slides):
                slide_content = [f"## 幻灯片 {slide_index + 1}\n"]
                
                # 提取文本
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_content.append(shape.text)
                    
                    # 提取表格
                    if extract_tables and shape.shape_type == 19:  # 表格类型
                        try:
                            table = shape.table
                            table_data = []
                            for row in table.rows:
                                row_data = [cell.text.strip() for cell in row.cells]
                                table_data.append(row_data)
                            
                            tables.append({
                                'slide': slide_index + 1,
                                'data': table_data,
                                'rows': len(table.rows),
                                'cols': len(table.rows[0].cells) if table.rows else 0
                            })
                        except Exception as e:
                            logger.warning(f"提取PPT表格失败 slide {slide_index + 1}: {e}")
                
                content_parts.append('\n'.join(slide_content) + '\n')
            
            return {
                'content': '\n'.join(content_parts),
                'metadata': metadata,
                'images': images,
                'tables': tables,
                'page_count': len(prs.slides),
                'structure': {'type': 'pptx', 'slides': len(prs.slides)}
            }
            
        except Exception as e:
            logger.error(f"PPTX解析失败: {e}")
            raise DocumentProcessingException(f"PPTX解析失败: {e}")
    
    def _parse_txt(self, file_path: str, extract_images: bool, extract_tables: bool) -> Dict[str, Any]:
        """解析文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                'content': content,
                'metadata': {'encoding': 'utf-8'},
                'images': [],
                'tables': [],
                'page_count': 1,
                'structure': {'type': 'text', 'lines': len(content.split('\n'))}
            }
            
        except UnicodeDecodeError:
            # 尝试其他编码
            for encoding in ['gbk', 'gb2312', 'latin1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    
                    return {
                        'content': content,
                        'metadata': {'encoding': encoding},
                        'images': [],
                        'tables': [],
                        'page_count': 1,
                        'structure': {'type': 'text', 'lines': len(content.split('\n'))}
                    }
                except UnicodeDecodeError:
                    continue
            
            raise DocumentProcessingException("无法识别文本文件编码")
            
        except Exception as e:
            logger.error(f"文本文件解析失败: {e}")
            raise DocumentProcessingException(f"文本文件解析失败: {e}")
    
    def _parse_html(self, file_path: str, extract_images: bool, extract_tables: bool) -> Dict[str, Any]:
        """解析HTML文件"""
        try:
            from bs4 import BeautifulSoup
            
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取文本内容
            text_content = soup.get_text(separator='\n', strip=True)
            
            # 提取元数据
            metadata = {}
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text()
            
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                if meta.get('name'):
                    metadata[meta.get('name')] = meta.get('content', '')
            
            # 提取表格
            tables = []
            if extract_tables:
                table_tags = soup.find_all('table')
                for table_index, table in enumerate(table_tags):
                    table_data = []
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        row_data = [cell.get_text(strip=True) for cell in cells]
                        if row_data:
                            table_data.append(row_data)
                    
                    if table_data:
                        tables.append({
                            'index': table_index,
                            'data': table_data,
                            'rows': len(table_data),
                            'cols': len(table_data[0]) if table_data else 0
                        })
            
            return {
                'content': text_content,
                'metadata': metadata,
                'images': [],
                'tables': tables,
                'page_count': 1,
                'structure': {'type': 'html', 'tags': len(soup.find_all())}
            }
            
        except Exception as e:
            logger.error(f"HTML解析失败: {e}")
            raise DocumentProcessingException(f"HTML解析失败: {e}")
    
    def _parse_csv(self, file_path: str, extract_images: bool, extract_tables: bool) -> Dict[str, Any]:
        """解析CSV文件"""
        try:
            df = pd.read_csv(file_path)
            
            # 转换为文本格式
            content = df.to_string(index=False)
            
            # 表格数据
            table_data = [df.columns.tolist()] + df.values.tolist()
            
            return {
                'content': content,
                'metadata': {'rows': len(df), 'columns': len(df.columns)},
                'images': [],
                'tables': [{
                    'index': 0,
                    'data': table_data,
                    'rows': len(df) + 1,  # +1 for header
                    'cols': len(df.columns)
                }],
                'page_count': 1,
                'structure': {'type': 'csv', 'rows': len(df), 'columns': len(df.columns)}
            }
            
        except Exception as e:
            logger.error(f"CSV解析失败: {e}")
            raise DocumentProcessingException(f"CSV解析失败: {e}")
    
    def _parse_excel(self, file_path: str, extract_images: bool, extract_tables: bool) -> Dict[str, Any]:
        """解析Excel文件"""
        try:
            # 读取所有工作表
            excel_file = pd.ExcelFile(file_path)
            content_parts = []
            tables = []
            
            for sheet_index, sheet_name in enumerate(excel_file.sheet_names):
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # 添加工作表标题
                content_parts.append(f"## 工作表: {sheet_name}\n")
                content_parts.append(df.to_string(index=False))
                content_parts.append('\n')
                
                # 表格数据
                if not df.empty:
                    table_data = [df.columns.tolist()] + df.values.tolist()
                    tables.append({
                        'sheet': sheet_name,
                        'index': sheet_index,
                        'data': table_data,
                        'rows': len(df) + 1,
                        'cols': len(df.columns)
                    })
            
            return {
                'content': '\n'.join(content_parts),
                'metadata': {'sheets': len(excel_file.sheet_names)},
                'images': [],
                'tables': tables,
                'page_count': len(excel_file.sheet_names),
                'structure': {'type': 'excel', 'sheets': len(excel_file.sheet_names)}
            }
            
        except Exception as e:
            logger.error(f"Excel解析失败: {e}")
            raise DocumentProcessingException(f"Excel解析失败: {e}")
    
    def _parse_json(self, file_path: str, extract_images: bool, extract_tables: bool) -> Dict[str, Any]:
        """解析JSON文件"""
        try:
            import json
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 格式化JSON为可读文本
            content = json.dumps(data, ensure_ascii=False, indent=2)
            
            return {
                'content': content,
                'metadata': {'type': type(data).__name__},
                'images': [],
                'tables': [],
                'page_count': 1,
                'structure': {'type': 'json', 'size': len(str(data))}
            }
            
        except Exception as e:
            logger.error(f"JSON解析失败: {e}")
            raise DocumentProcessingException(f"JSON解析失败: {e}")


# 全局Marker服务实例
marker_service = MarkerService()
