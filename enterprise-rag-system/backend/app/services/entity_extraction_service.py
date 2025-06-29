"""
基于spaCy + NER的实体抽取服务 - 企业级RAG系统
严格按照技术栈要求：spaCy + 自定义NER模型进行实体识别和关系抽取
"""
import asyncio
import re
from datetime import datetime
from typing import List, Dict, Any

import jieba
import jieba.posseg as pseg
import spacy
from loguru import logger


class EntityExtractionService:
    """实体抽取服务"""
    
    def __init__(self):
        self.zh_nlp = None  # 中文模型
        self.en_nlp = None  # 英文模型
        self._initialized = False
        
        # 实体类型映射
        self.entity_type_mapping = {
            # spaCy 标准实体类型
            "PERSON": "Person",      # 人物
            "ORG": "Organization",   # 组织
            "GPE": "Location",       # 地理政治实体
            "LOC": "Location",       # 地点
            "EVENT": "Event",        # 事件
            "PRODUCT": "Product",    # 产品
            "WORK_OF_ART": "Work",   # 艺术作品
            "LAW": "Law",           # 法律
            "LANGUAGE": "Language",  # 语言
            "DATE": "Date",         # 日期
            "TIME": "Time",         # 时间
            "PERCENT": "Percent",   # 百分比
            "MONEY": "Money",       # 货币
            "QUANTITY": "Quantity", # 数量
            "ORDINAL": "Ordinal",   # 序数
            "CARDINAL": "Cardinal", # 基数
            
            # 中文实体类型 (jieba)
            "nr": "Person",         # 人名
            "ns": "Location",       # 地名
            "nt": "Organization",   # 机构名
            "nz": "Concept",        # 其他专名
            "m": "Quantity",        # 数词
            "t": "Time",           # 时间词
        }
        
        # 关系模式
        self.relation_patterns = [
            # 工作关系
            (r"(.+?)(?:在|于|任职于|工作于)(.+?)(?:公司|企业|机构|组织)", "WORKS_FOR"),
            # 位置关系
            (r"(.+?)(?:位于|在|坐落于)(.+?)(?:市|省|国|地区)", "LOCATED_IN"),
            # 隶属关系
            (r"(.+?)(?:属于|隶属于|是)(.+?)(?:的|部门|分支)", "PART_OF"),
            # 参与关系
            (r"(.+?)(?:参与|参加|出席)(.+?)(?:会议|活动|项目)", "PARTICIPATES_IN"),
            # 相似关系
            (r"(.+?)(?:类似于|像|如同)(.+)", "SIMILAR_TO"),
        ]
        
        # 停用词
        self.stop_words = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
            "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
            "自己", "这", "那", "它", "他", "她", "们", "个", "中", "可以", "这个", "我们"
        }
    
    async def initialize(self):
        """初始化spaCy模型"""
        if self._initialized:
            return
        
        try:
            logger.info("正在初始化spaCy NER模型...")
            
            # 在线程池中加载模型
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_models)
            
            self._initialized = True
            logger.info("spaCy NER模型初始化完成")
            
        except Exception as e:
            logger.error(f"spaCy模型初始化失败: {e}")
            raise
    
    def _load_models(self):
        """同步加载spaCy模型"""
        try:
            # 加载中文模型
            try:
                self.zh_nlp = spacy.load("zh_core_web_sm")
                logger.info("中文spaCy模型加载成功")
            except OSError:
                logger.warning("中文spaCy模型未找到，尝试加载基础模型")
                self.zh_nlp = spacy.blank("zh")
            
            # 加载英文模型
            try:
                self.en_nlp = spacy.load("en_core_web_sm")
                logger.info("英文spaCy模型加载成功")
            except OSError:
                logger.warning("英文spaCy模型未找到，尝试加载基础模型")
                self.en_nlp = spacy.blank("en")
            
            # 初始化jieba
            jieba.initialize()
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        # 简单的中英文检测
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if chinese_chars > english_chars:
            return "zh"
        else:
            return "en"
    
    async def extract_entities_spacy(self, text: str) -> List[Dict[str, Any]]:
        """使用spaCy提取实体"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # 检测语言
            language = self._detect_language(text)
            nlp = self.zh_nlp if language == "zh" else self.en_nlp
            
            # 在线程池中执行NER
            loop = asyncio.get_event_loop()
            entities = await loop.run_in_executor(
                None, 
                self._extract_entities_sync, 
                nlp, text
            )
            
            return entities
            
        except Exception as e:
            logger.error(f"spaCy实体提取失败: {e}")
            return []
    
    def _extract_entities_sync(self, nlp, text: str) -> List[Dict[str, Any]]:
        """同步执行spaCy实体提取"""
        try:
            doc = nlp(text)
            entities = []
            
            for ent in doc.ents:
                entity_type = self.entity_type_mapping.get(ent.label_, "Entity")
                
                # 过滤停用词和短实体
                if (ent.text.strip() not in self.stop_words and 
                    len(ent.text.strip()) > 1):
                    
                    entities.append({
                        "name": ent.text.strip(),
                        "label": ent.label_,
                        "type": entity_type,
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "confidence": 0.8,  # spaCy默认置信度
                        "source": "spacy"
                    })
            
            return entities
            
        except Exception as e:
            logger.error(f"同步spaCy实体提取失败: {e}")
            return []
    
    async def extract_entities_jieba(self, text: str) -> List[Dict[str, Any]]:
        """使用jieba提取中文实体"""
        try:
            # 在线程池中执行jieba分词
            loop = asyncio.get_event_loop()
            entities = await loop.run_in_executor(
                None, 
                self._extract_entities_jieba_sync, 
                text
            )
            
            return entities
            
        except Exception as e:
            logger.error(f"jieba实体提取失败: {e}")
            return []
    
    def _extract_entities_jieba_sync(self, text: str) -> List[Dict[str, Any]]:
        """同步执行jieba实体提取"""
        try:
            entities = []
            words = pseg.cut(text)
            
            current_pos = 0
            for word, flag in words:
                word = word.strip()
                
                # 查找词在文本中的位置
                start_pos = text.find(word, current_pos)
                end_pos = start_pos + len(word)
                current_pos = end_pos
                
                # 根据词性标注判断实体类型
                if flag in self.entity_type_mapping:
                    entity_type = self.entity_type_mapping[flag]
                    
                    # 过滤停用词和短实体
                    if (word not in self.stop_words and 
                        len(word) > 1 and
                        not word.isdigit()):
                        
                        entities.append({
                            "name": word,
                            "label": flag,
                            "type": entity_type,
                            "start": start_pos,
                            "end": end_pos,
                            "confidence": 0.7,  # jieba默认置信度
                            "source": "jieba"
                        })
            
            return entities
            
        except Exception as e:
            logger.error(f"同步jieba实体提取失败: {e}")
            return []
    
    async def extract_entities_combined(self, text: str) -> List[Dict[str, Any]]:
        """组合spaCy和jieba的实体提取结果"""
        try:
            # 并行执行两种提取方法
            spacy_entities, jieba_entities = await asyncio.gather(
                self.extract_entities_spacy(text),
                self.extract_entities_jieba(text)
            )
            
            # 合并和去重
            combined_entities = self._merge_entities(spacy_entities + jieba_entities)
            
            logger.debug(f"组合实体提取完成，共提取 {len(combined_entities)} 个实体")
            return combined_entities
            
        except Exception as e:
            logger.error(f"组合实体提取失败: {e}")
            return []
    
    def _merge_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并和去重实体"""
        # 按名称分组
        entity_groups = {}
        for entity in entities:
            name = entity["name"].lower()
            if name not in entity_groups:
                entity_groups[name] = []
            entity_groups[name].append(entity)
        
        # 合并同名实体
        merged_entities = []
        for name, group in entity_groups.items():
            if len(group) == 1:
                merged_entities.append(group[0])
            else:
                # 选择置信度最高的实体
                best_entity = max(group, key=lambda x: x["confidence"])
                
                # 合并来源信息
                sources = list(set(e["source"] for e in group))
                best_entity["source"] = "+".join(sources)
                
                # 提高置信度
                if len(sources) > 1:
                    best_entity["confidence"] = min(1.0, best_entity["confidence"] + 0.1)
                
                merged_entities.append(best_entity)
        
        return merged_entities
    
    async def extract_relations(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取实体间关系"""
        try:
            relations = []
            
            # 基于模式的关系提取
            pattern_relations = await self._extract_pattern_relations(text)
            relations.extend(pattern_relations)
            
            # 基于共现的关系提取
            cooccurrence_relations = await self._extract_cooccurrence_relations(text, entities)
            relations.extend(cooccurrence_relations)
            
            # 去重和过滤
            filtered_relations = self._filter_relations(relations)
            
            logger.debug(f"关系提取完成，共提取 {len(filtered_relations)} 个关系")
            return filtered_relations
            
        except Exception as e:
            logger.error(f"关系提取失败: {e}")
            return []
    
    async def _extract_pattern_relations(self, text: str) -> List[Dict[str, Any]]:
        """基于模式的关系提取"""
        relations = []
        
        for pattern, relation_type in self.relation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if len(match.groups()) >= 2:
                    source = match.group(1).strip()
                    target = match.group(2).strip()
                    
                    if (source and target and 
                        source not in self.stop_words and 
                        target not in self.stop_words):
                        
                        relations.append({
                            "source": source,
                            "target": target,
                            "type": relation_type,
                            "confidence": 0.8,
                            "evidence": match.group(0),
                            "method": "pattern"
                        })
        
        return relations
    
    async def _extract_cooccurrence_relations(
        self, 
        text: str, 
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """基于共现的关系提取"""
        relations = []
        
        # 按句子分割文本
        sentences = re.split(r'[。！？；\n]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # 跳过过短的句子
                continue
            
            # 找到在同一句子中的实体
            sentence_entities = []
            for entity in entities:
                if entity["name"] in sentence:
                    sentence_entities.append(entity)
            
            # 为同一句子中的实体创建关系
            for i, entity1 in enumerate(sentence_entities):
                for entity2 in sentence_entities[i+1:]:
                    # 避免自关联
                    if entity1["name"] != entity2["name"]:
                        relations.append({
                            "source": entity1["name"],
                            "target": entity2["name"],
                            "type": "RELATES_TO",
                            "confidence": 0.6,
                            "evidence": sentence,
                            "method": "cooccurrence"
                        })
        
        return relations
    
    def _filter_relations(self, relations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤和去重关系"""
        # 去重
        unique_relations = {}
        for relation in relations:
            key = f"{relation['source']}_{relation['target']}_{relation['type']}"
            if key not in unique_relations:
                unique_relations[key] = relation
            else:
                # 保留置信度更高的关系
                if relation["confidence"] > unique_relations[key]["confidence"]:
                    unique_relations[key] = relation
        
        # 过滤低置信度关系
        filtered_relations = [
            rel for rel in unique_relations.values() 
            if rel["confidence"] >= 0.5
        ]
        
        return filtered_relations
    
    async def process_chunk(self, chunk_content: str) -> Dict[str, Any]:
        """处理单个文档分块"""
        try:
            # 提取实体
            entities = await self.extract_entities_combined(chunk_content)
            
            # 提取关系
            relations = await self.extract_relations(chunk_content, entities)
            
            # 统计信息
            stats = {
                "total_entities": len(entities),
                "entity_types": {},
                "total_relations": len(relations),
                "relation_types": {}
            }
            
            # 统计实体类型
            for entity in entities:
                entity_type = entity["type"]
                stats["entity_types"][entity_type] = stats["entity_types"].get(entity_type, 0) + 1
            
            # 统计关系类型
            for relation in relations:
                relation_type = relation["type"]
                stats["relation_types"][relation_type] = stats["relation_types"].get(relation_type, 0) + 1
            
            return {
                "entities": entities,
                "relations": relations,
                "stats": stats,
                "processed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"分块处理失败: {e}")
            return {
                "entities": [],
                "relations": [],
                "stats": {},
                "error": str(e)
            }


# 全局实体抽取服务实例
entity_extraction_service = EntityExtractionService()


# 便捷函数
async def extract_entities_from_text(text: str) -> List[Dict[str, Any]]:
    """从文本提取实体的便捷函数"""
    return await entity_extraction_service.extract_entities_combined(text)


async def extract_relations_from_text(text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从文本提取关系的便捷函数"""
    return await entity_extraction_service.extract_relations(text, entities)


async def process_text_chunk(chunk_content: str) -> Dict[str, Any]:
    """处理文本分块的便捷函数"""
    return await entity_extraction_service.process_chunk(chunk_content)
