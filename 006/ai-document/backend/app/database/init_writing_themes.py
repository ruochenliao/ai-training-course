"""
初始化写作主题数据
"""
import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '../..')
sys.path.insert(0, backend_dir)

from sqlalchemy.orm import Session
from app.models.writing_theme import WritingTheme, ThemeField, PromptTemplate, ThemeCategory
from app.database.connection import SessionLocal


def init_theme_categories():
    """初始化主题分类"""
    db = SessionLocal()
    try:
        categories = [
            {
                "name": "通报",
                "description": "各类通报文件，包括表彰通报、批评通报等",
                "icon": "📢",
                "color": "#1890ff",
                "sort_order": 1
            },
            {
                "name": "会务",
                "description": "会议相关文件，包括会议通知、会议纪要等",
                "icon": "📅",
                "color": "#52c41a",
                "sort_order": 2
            },
            {
                "name": "汇报",
                "description": "各类工作汇报和总结文件",
                "icon": "📊",
                "color": "#fa8c16",
                "sort_order": 3
            },
            {
                "name": "调研",
                "description": "调研报告和分析文件",
                "icon": "🔍",
                "color": "#722ed1",
                "sort_order": 4
            }
        ]
        
        for cat_data in categories:
            existing = db.query(ThemeCategory).filter(ThemeCategory.name == cat_data["name"]).first()
            if not existing:
                category = ThemeCategory(**cat_data)
                db.add(category)
        
        db.commit()
        print("✅ 主题分类初始化完成")
        
    except Exception as e:
        print(f"❌ 主题分类初始化失败: {e}")
        db.rollback()
    finally:
        db.close()


def init_writing_themes():
    """初始化写作主题"""
    db = SessionLocal()
    try:
        # 表彰通报主题
        commendation_theme = WritingTheme(
            name="表彰通报",
            description="用于表彰先进个人或集体的通报文件",
            category="通报",
            icon="🏆",
            theme_key="commendation",
            sort_order=1
        )
        
        # 表彰通报字段
        commendation_fields = [
            ThemeField(
                field_key="title",
                field_label="标题",
                field_type="text",
                placeholder="请输入表彰通报标题",
                is_required=True,
                sort_order=1
            ),
            ThemeField(
                field_key="recipient",
                field_label="表彰对象",
                field_type="text",
                placeholder="请输入被表彰的个人或集体名称",
                is_required=True,
                sort_order=2
            ),
            ThemeField(
                field_key="reason",
                field_label="表彰原因",
                field_type="textarea",
                placeholder="请详细描述表彰的具体原因和事迹",
                is_required=True,
                sort_order=3
            ),
            ThemeField(
                field_key="achievement",
                field_label="主要成就",
                field_type="textarea",
                placeholder="请描述主要成就和贡献",
                is_required=True,
                sort_order=4
            )
        ]
        
        # 表彰通报提示词模板
        commendation_template = PromptTemplate(
            template_name="表彰通报标准模板",
            template_type="main",
            system_prompt="你是一名专业的公文写作专家，擅长撰写各类正式文件。",
            user_prompt_template="""请帮我撰写一份正式的表彰通报。

**文档信息：**
- 标题：{title}
- 表彰对象：{recipient}
- 表彰原因：{reason}
- 主要成就：{achievement}

**写作要求：**
1. 使用正式的公文格式和语言
2. 结构清晰，包含表彰决定、表彰原因、主要成就、决定等部分
3. 语言庄重、准确、简洁
4. 体现表彰的正面意义和激励作用
5. 符合党政机关公文写作规范

请生成一份完整、专业的表彰通报文档。""",
            ai_model="deepseek-chat",
            temperature="0.7"
        )
        
        # 检查是否已存在
        existing = db.query(WritingTheme).filter(WritingTheme.theme_key == "commendation").first()
        if not existing:
            db.add(commendation_theme)
            db.flush()
            
            # 添加字段
            for field in commendation_fields:
                field.theme_id = commendation_theme.id
                db.add(field)
            
            # 添加模板
            commendation_template.theme_id = commendation_theme.id
            db.add(commendation_template)
        
        # 会议通知主题
        meeting_theme = WritingTheme(
            name="会议通知",
            description="用于发布会议安排的通知文件",
            category="会务",
            icon="📅",
            theme_key="meeting_notice",
            sort_order=2
        )
        
        # 会议通知字段
        meeting_fields = [
            ThemeField(
                field_key="title",
                field_label="会议主题",
                field_type="text",
                placeholder="请输入会议主题",
                is_required=True,
                sort_order=1
            ),
            ThemeField(
                field_key="time",
                field_label="会议时间",
                field_type="text",
                placeholder="请输入会议时间",
                is_required=True,
                sort_order=2
            ),
            ThemeField(
                field_key="location",
                field_label="会议地点",
                field_type="text",
                placeholder="请输入会议地点",
                is_required=True,
                sort_order=3
            ),
            ThemeField(
                field_key="agenda",
                field_label="会议议程",
                field_type="textarea",
                placeholder="请输入会议议程和主要内容",
                is_required=True,
                sort_order=4
            ),
            ThemeField(
                field_key="participants",
                field_label="参会人员",
                field_type="textarea",
                placeholder="请输入参会人员范围",
                is_required=True,
                sort_order=5
            )
        ]
        
        # 会议通知提示词模板
        meeting_template = PromptTemplate(
            template_name="会议通知标准模板",
            template_type="main",
            system_prompt="你是一名专业的行政文秘，擅长撰写各类会议文件。",
            user_prompt_template="""请帮我撰写一份正式的会议通知。

**会议信息：**
- 会议主题：{title}
- 会议时间：{time}
- 会议地点：{location}
- 会议议程：{agenda}
- 参会人员：{participants}

**写作要求：**
1. 使用标准的会议通知格式
2. 信息完整、准确、清晰
3. 语言正式、简洁明了
4. 包含会议安排、议程、参会人员、注意事项等
5. 体现会议的重要性和必要性

请生成一份完整、规范的会议通知文档。""",
            ai_model="deepseek-chat",
            temperature="0.7"
        )
        
        # 检查是否已存在
        existing = db.query(WritingTheme).filter(WritingTheme.theme_key == "meeting_notice").first()
        if not existing:
            db.add(meeting_theme)
            db.flush()
            
            # 添加字段
            for field in meeting_fields:
                field.theme_id = meeting_theme.id
                db.add(field)
            
            # 添加模板
            meeting_template.theme_id = meeting_theme.id
            db.add(meeting_template)
        
        db.commit()
        print("✅ 写作主题初始化完成")
        
    except Exception as e:
        print(f"❌ 写作主题初始化失败: {e}")
        db.rollback()
    finally:
        db.close()


def init_all():
    """初始化所有数据"""
    print("🚀 开始初始化写作主题数据...")
    init_theme_categories()
    init_writing_themes()
    print("🎉 写作主题数据初始化完成！")


if __name__ == "__main__":
    init_all()
