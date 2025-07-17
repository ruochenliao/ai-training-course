from sqlalchemy.orm import Session
from app.models.template import TemplateCategory, TemplateType, WritingScenarioConfig
from app.schemas.template import TemplateCategoryCreate, TemplateTypeCreate, WritingScenarioConfigCreate, WritingFieldConfig
from app.services.template_service import template_service


class TemplateInitService:
    """模板初始化服务"""

    @staticmethod
    def get_init_data():
        """获取初始化数据"""
        # 模板分类和类型的对应关系 - 根据用户需求更新
        template_data = {
            "通报": ["表彰", "批评", "其它通报"],
            "会务": [
                "政协提案(自上而下式)", "政协提案(自下而上式)", "人大议案和建议(政府向人大议案)",
                "政协提案(横向移植式)", "人大议案和建议(代表向大会议案)", "人大议案和建议(代表建议)",
                "提案建议答复", "会议纪要"
            ],
            "报告和上报信息": [
                "政府工作报告", "地区调研报告", "部门工作报告", "问题调研报告", "落实指示报告",
                "整改报告", "项目汇报", "学习心得报告", "工作汇报", "项目申请报告"
            ],
            "讲话": [
                "形势报告", "开幕式致辞", "政策解读", "闭幕式致辞", "人物评价",
                "事件评价", "交流", "就职演讲", "集会演讲"
            ],
            "计划": ["规划", "计划", "行动计划", "工作方案", "工作预案"],
            "总结": ["年度总结", "半年总结", "季度总结", "述职报告"],
            "许可": ["批复", "鉴定"],
            "书信": ["倡议书", "决心书", "表扬信", "感谢信", "慰问信", "贺信"],
            "汇报": ["答复上级批示", "阶段工作汇报", "主题工作汇报"],
            "调研": ["实地考察调研", "意见汇总调研", "资料分析调研"],
            "方案": ["工作方案", "应急处置预案"],
            "党建": ["思想情况报告", "主题学习体会", "对照检查材料"],
            "新闻": ["新闻消息", "新闻发布稿"],
            "通知": ["活动通知", "会议通知"]
        }

        categories = []
        types = []
        sort_order = 0

        for category_name, type_names in template_data.items():
            # 创建分类
            category = TemplateCategoryCreate(
                name=category_name,
                description=f"{category_name}相关文档模板",
                sort_order=sort_order,
                is_active=True
            )
            categories.append(category)

            # 创建该分类下的类型
            type_sort_order = 0
            for type_name in type_names:
                template_type = TemplateTypeCreate(
                    category_id=0,  # 这里先设为0，后面会更新
                    name=type_name,
                    description=f"{type_name}模板",
                    sort_order=type_sort_order,
                    is_active=True
                )
                # 添加分类索引信息，用于后续关联（作为额外属性）
                types.append((template_type, sort_order))
                type_sort_order += 1

            sort_order += 1

        return categories, types

    @staticmethod
    def get_default_writing_scenario_configs():
        """获取默认的写作场景配置"""
        # 为特定模板类型定义默认的写作场景配置
        scenario_configs = {
            "表彰": {
                "config_name": "表彰文档写作场景",
                "description": "表彰类文档的写作场景配置",
                "field_configs": [
                    {
                        "field_name": "标题",
                        "field_key": "title",
                        "field_type": "text",
                        "required": True,
                        "ai_enabled": True,
                        "doc_enabled": False,
                        "placeholder": "请输入表彰文档标题"
                    },
                    {
                        "field_name": "关键词",
                        "field_key": "keywords",
                        "field_type": "text",
                        "required": False,
                        "ai_enabled": True,
                        "doc_enabled": False,
                        "placeholder": "请输入关键词，用逗号分隔"
                    },
                    {
                        "field_name": "表彰原因",
                        "field_key": "reason",
                        "field_type": "textarea",
                        "required": True,
                        "ai_enabled": True,
                        "doc_enabled": True,
                        "placeholder": "请描述表彰的原因和背景"
                    },
                    {
                        "field_name": "表彰内容",
                        "field_key": "content",
                        "field_type": "textarea",
                        "required": True,
                        "ai_enabled": True,
                        "doc_enabled": True,
                        "placeholder": "请描述具体的表彰内容"
                    },
                    {
                        "field_name": "表彰目的",
                        "field_key": "purpose",
                        "field_type": "textarea",
                        "required": False,
                        "ai_enabled": True,
                        "doc_enabled": True,
                        "placeholder": "请描述表彰的目的和意义"
                    }
                ],
                "default_config": {
                    "ai_model": "gpt-4",
                    "max_length": 2000,
                    "style": "formal"
                }
            },
            "批评": {
                "config_name": "批评文档写作场景",
                "description": "批评类文档的写作场景配置",
                "field_configs": [
                    {
                        "field_name": "标题",
                        "field_key": "title",
                        "field_type": "text",
                        "required": True,
                        "ai_enabled": True,
                        "doc_enabled": False,
                        "placeholder": "请输入批评文档标题"
                    },
                    {
                        "field_name": "关键词",
                        "field_key": "keywords",
                        "field_type": "text",
                        "required": False,
                        "ai_enabled": True,
                        "doc_enabled": False,
                        "placeholder": "请输入关键词，用逗号分隔"
                    },
                    {
                        "field_name": "问题描述",
                        "field_key": "problem",
                        "field_type": "textarea",
                        "required": True,
                        "ai_enabled": True,
                        "doc_enabled": True,
                        "placeholder": "请描述存在的问题"
                    },
                    {
                        "field_name": "批评内容",
                        "field_key": "content",
                        "field_type": "textarea",
                        "required": True,
                        "ai_enabled": True,
                        "doc_enabled": True,
                        "placeholder": "请描述具体的批评内容"
                    },
                    {
                        "field_name": "整改要求",
                        "field_key": "requirements",
                        "field_type": "textarea",
                        "required": False,
                        "ai_enabled": True,
                        "doc_enabled": True,
                        "placeholder": "请描述整改要求和措施"
                    }
                ]
            },
            "会议纪要": {
                "config_name": "会议纪要写作场景",
                "description": "会议纪要的写作场景配置",
                "field_configs": [
                    {
                        "field_name": "会议标题",
                        "field_key": "title",
                        "field_type": "text",
                        "required": True,
                        "ai_enabled": True,
                        "doc_enabled": False,
                        "placeholder": "请输入会议名称"
                    },
                    {
                        "field_name": "会议时间",
                        "field_key": "meeting_time",
                        "field_type": "text",
                        "required": True,
                        "ai_enabled": False,
                        "doc_enabled": False,
                        "placeholder": "请输入会议时间"
                    },
                    {
                        "field_name": "会议地点",
                        "field_key": "location",
                        "field_type": "text",
                        "required": True,
                        "ai_enabled": False,
                        "doc_enabled": False,
                        "placeholder": "请输入会议地点"
                    },
                    {
                        "field_name": "参会人员",
                        "field_key": "attendees",
                        "field_type": "textarea",
                        "required": True,
                        "ai_enabled": False,
                        "doc_enabled": False,
                        "placeholder": "请输入参会人员名单"
                    },
                    {
                        "field_name": "会议议题",
                        "field_key": "agenda",
                        "field_type": "textarea",
                        "required": True,
                        "ai_enabled": True,
                        "doc_enabled": True,
                        "placeholder": "请输入会议主要议题"
                    },
                    {
                        "field_name": "会议内容",
                        "field_key": "content",
                        "field_type": "textarea",
                        "required": True,
                        "ai_enabled": True,
                        "doc_enabled": True,
                        "placeholder": "请输入会议讨论的主要内容"
                    }
                ]
            }
        }

        return scenario_configs

    @staticmethod
    def init_template_data(db: Session) -> dict:
        """初始化模板数据"""
        try:
            # 检查是否已经初始化过
            existing_categories = template_service.get_categories(db, limit=1)
            if existing_categories:
                return {
                    "success": False,
                    "message": "模板数据已存在，无需重复初始化",
                    "data": {
                        "categories_count": len(template_service.get_categories(db, limit=1000)),
                        "types_count": 0
                    }
                }

            categories_data, types_data = TemplateInitService.get_init_data()

            # 创建分类
            created_categories = []
            for category_data in categories_data:
                category = template_service.create_category(db, category_data)
                created_categories.append(category)

            # 创建类型，并关联到对应的分类
            created_types = []
            for type_data, category_index in types_data:
                # 根据category_index找到对应的分类ID
                if category_index < len(created_categories):
                    type_data.category_id = created_categories[category_index].id
                    template_type = template_service.create_type(db, type_data)
                    created_types.append(template_type)

            # 创建默认的写作场景配置
            scenario_configs = TemplateInitService.get_default_writing_scenario_configs()
            created_configs = []

            for template_type in created_types:
                if template_type.name in scenario_configs:
                    config_data = scenario_configs[template_type.name]

                    # 转换field_configs为WritingFieldConfig对象
                    field_configs = []
                    for field_config in config_data["field_configs"]:
                        field_configs.append(WritingFieldConfig(**field_config))

                    scenario_config = WritingScenarioConfigCreate(
                        template_type_id=template_type.id,
                        config_name=config_data["config_name"],
                        description=config_data["description"],
                        field_configs=field_configs,
                        default_config=config_data.get("default_config"),
                        is_active=True
                    )

                    created_config = template_service.create_writing_scenario_config(db, scenario_config)
                    created_configs.append(created_config)

            return {
                "success": True,
                "message": "模板数据初始化成功",
                "data": {
                    "categories_count": len(created_categories),
                    "types_count": len(created_types),
                    "scenario_configs_count": len(created_configs),
                    "categories": [{"id": c.id, "name": c.name} for c in created_categories],
                    "types": [{"id": t.id, "name": t.name, "category_id": t.category_id} for t in created_types],
                    "scenario_configs": [{"id": c.id, "template_type_id": c.template_type_id, "config_name": c.config_name} for c in created_configs]
                }
            }

        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "message": f"初始化失败: {str(e)}",
                "data": None
            }

    @staticmethod
    def reset_template_data(db: Session) -> dict:
        """重置模板数据"""
        try:
            # 删除所有模板数据（按依赖关系顺序删除）
            db.query(WritingScenarioConfig).delete()
            db.query(TemplateType).delete()
            db.query(TemplateCategory).delete()
            db.commit()

            # 重新初始化
            return TemplateInitService.init_template_data(db)

        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "message": f"重置失败: {str(e)}",
                "data": None
            }

    @staticmethod
    def get_template_statistics(db: Session) -> dict:
        """获取模板统计信息"""
        categories_count = db.query(TemplateCategory).count()
        types_count = db.query(TemplateType).count()
        
        # 按分类统计类型数量
        category_stats = []
        categories = template_service.get_categories(db, limit=1000)
        
        for category in categories:
            types = template_service.get_types_by_category(db, category.id)
            category_stats.append({
                "category_id": category.id,
                "category_name": category.name,
                "types_count": len(types),
                "types": [{"id": t.id, "name": t.name} for t in types]
            })

        return {
            "total_categories": categories_count,
            "total_types": types_count,
            "category_statistics": category_stats
        }


template_init_service = TemplateInitService()
