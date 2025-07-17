"""
创建写作主题相关表的迁移脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from sqlalchemy import text
from app.database.connection import engine, SessionLocal


def create_writing_theme_tables():
    """创建写作主题相关表"""
    
    # 创建主题分类表
    create_theme_categories_sql = """
    CREATE TABLE IF NOT EXISTS theme_categories (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(50) UNIQUE NOT NULL COMMENT '分类名称',
        description TEXT COMMENT '分类描述',
        icon VARCHAR(50) COMMENT '分类图标',
        color VARCHAR(20) COMMENT '分类颜色',
        is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
        sort_order INT DEFAULT 0 COMMENT '排序顺序',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 创建写作主题表
    create_writing_themes_sql = """
    CREATE TABLE IF NOT EXISTS writing_themes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL COMMENT '主题名称',
        description TEXT COMMENT '主题描述',
        category VARCHAR(50) NOT NULL COMMENT '主题分类',
        icon VARCHAR(50) COMMENT '主题图标',
        theme_key VARCHAR(50) UNIQUE NOT NULL COMMENT '主题唯一标识',
        is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
        sort_order INT DEFAULT 0 COMMENT '排序顺序',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_category (category),
        INDEX idx_theme_key (theme_key),
        INDEX idx_is_active (is_active)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 创建主题字段表
    create_theme_fields_sql = """
    CREATE TABLE IF NOT EXISTS theme_fields (
        id INT AUTO_INCREMENT PRIMARY KEY,
        theme_id INT NOT NULL,
        field_key VARCHAR(50) NOT NULL COMMENT '字段键名',
        field_label VARCHAR(100) NOT NULL COMMENT '字段标签',
        field_type VARCHAR(20) NOT NULL DEFAULT 'text' COMMENT '字段类型',
        placeholder VARCHAR(200) COMMENT '占位符文本',
        default_value TEXT COMMENT '默认值',
        is_required BOOLEAN DEFAULT FALSE COMMENT '是否必填',
        max_length INT COMMENT '最大长度',
        min_length INT COMMENT '最小长度',
        options JSON COMMENT '选择项配置',
        validation_rules JSON COMMENT '验证规则',
        sort_order INT DEFAULT 0 COMMENT '显示顺序',
        is_visible BOOLEAN DEFAULT TRUE COMMENT '是否显示',
        help_text TEXT COMMENT '帮助文本',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (theme_id) REFERENCES writing_themes(id) ON DELETE CASCADE,
        INDEX idx_theme_id (theme_id),
        INDEX idx_field_key (field_key),
        INDEX idx_sort_order (sort_order)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 创建提示词模板表
    create_prompt_templates_sql = """
    CREATE TABLE IF NOT EXISTS prompt_templates (
        id INT AUTO_INCREMENT PRIMARY KEY,
        theme_id INT NOT NULL,
        template_name VARCHAR(100) NOT NULL COMMENT '模板名称',
        template_type VARCHAR(20) NOT NULL DEFAULT 'main' COMMENT '模板类型',
        system_prompt TEXT COMMENT '系统提示词',
        user_prompt_template TEXT NOT NULL COMMENT '用户提示词模板',
        variables JSON COMMENT '模板变量配置',
        ai_model VARCHAR(50) COMMENT '推荐AI模型',
        temperature VARCHAR(10) COMMENT '温度参数',
        max_tokens INT COMMENT '最大令牌数',
        is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
        version VARCHAR(20) DEFAULT '1.0' COMMENT '模板版本',
        usage_count INT DEFAULT 0 COMMENT '使用次数',
        success_rate VARCHAR(10) COMMENT '成功率',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (theme_id) REFERENCES writing_themes(id) ON DELETE CASCADE,
        INDEX idx_theme_id (theme_id),
        INDEX idx_template_type (template_type),
        INDEX idx_is_active (is_active)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 创建写作历史记录表
    create_writing_history_sql = """
    CREATE TABLE IF NOT EXISTS writing_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        theme_id INT NOT NULL,
        input_data JSON COMMENT '输入数据',
        generated_content TEXT COMMENT '生成的内容',
        final_content TEXT COMMENT '最终内容',
        quality_score VARCHAR(10) COMMENT '质量评分',
        user_rating INT COMMENT '用户评分',
        feedback TEXT COMMENT '用户反馈',
        generation_time INT COMMENT '生成耗时(秒)',
        token_usage INT COMMENT '令牌使用量',
        model_used VARCHAR(50) COMMENT '使用的模型',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (theme_id) REFERENCES writing_themes(id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id),
        INDEX idx_theme_id (theme_id),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    try:
        with engine.connect() as connection:
            # 执行建表语句
            connection.execute(text(create_theme_categories_sql))
            print("✅ 创建 theme_categories 表成功")
            
            connection.execute(text(create_writing_themes_sql))
            print("✅ 创建 writing_themes 表成功")
            
            connection.execute(text(create_theme_fields_sql))
            print("✅ 创建 theme_fields 表成功")
            
            connection.execute(text(create_prompt_templates_sql))
            print("✅ 创建 prompt_templates 表成功")
            
            connection.execute(text(create_writing_history_sql))
            print("✅ 创建 writing_history 表成功")
            
            connection.commit()
            print("🎉 所有写作主题相关表创建完成！")
            
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        raise


def drop_writing_theme_tables():
    """删除写作主题相关表（用于回滚）"""
    
    drop_tables_sql = """
    SET FOREIGN_KEY_CHECKS = 0;
    DROP TABLE IF EXISTS writing_history;
    DROP TABLE IF EXISTS prompt_templates;
    DROP TABLE IF EXISTS theme_fields;
    DROP TABLE IF EXISTS writing_themes;
    DROP TABLE IF EXISTS theme_categories;
    SET FOREIGN_KEY_CHECKS = 1;
    """
    
    try:
        with engine.connect() as connection:
            for sql in drop_tables_sql.split(';'):
                if sql.strip():
                    connection.execute(text(sql))
            connection.commit()
            print("🗑️ 所有写作主题相关表已删除")
            
    except Exception as e:
        print(f"❌ 删除表失败: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        print("⚠️  准备删除所有写作主题相关表...")
        confirm = input("确定要删除吗？(yes/no): ")
        if confirm.lower() == 'yes':
            drop_writing_theme_tables()
        else:
            print("操作已取消")
    else:
        print("🚀 开始创建写作主题相关表...")
        create_writing_theme_tables()
