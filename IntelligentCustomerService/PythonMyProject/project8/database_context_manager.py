import sqlite3
import time
from typing import Optional, List, Tuple, Any

class DatabaseConnection:
    """
    数据库连接上下文管理器
    
    这个类实现了上下文管理器协议，用于安全地管理数据库连接资源。
    使用with语句可以确保数据库连接在使用完毕后自动关闭。
    """
    
    def __init__(self, database_path: str = ":memory:"):
        """
        初始化数据库连接管理器
        
        Args:
            database_path (str): 数据库文件路径，默认为内存数据库
        """
        self.database_path = database_path
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.connect_time: Optional[float] = None
    
    def __enter__(self):
        """
        进入上下文时调用，建立数据库连接
        
        Returns:
            DatabaseConnection: 返回自身实例
        """
        try:
            # 记录连接开始时间
            self.connect_time = time.time()
            
            # 建立数据库连接
            self.connection = sqlite3.connect(self.database_path)
            
            # 设置行工厂，使查询结果更易读
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            
            print(f"🔗 数据库连接已建立")
            print(f"📍 数据库路径: {self.database_path}")
            print(f"⏰ 连接时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.connect_time))}")
            print(f"✅ 连接状态: 活跃")
            print("-" * 50)
            
            return self
            
        except sqlite3.Error as e:
            print(f"❌ 数据库连接失败: {e}")
            raise
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            raise
    
    def __exit__(self, exc_type, exc_value, traceback):
        """
        退出上下文时调用，关闭数据库连接
        
        Args:
            exc_type: 异常类型
            exc_value: 异常值
            traceback: 异常追踪信息
        
        Returns:
            bool: 是否抑制异常（False表示不抑制）
        """
        try:
            # 计算连接持续时间
            if self.connect_time:
                duration = time.time() - self.connect_time
                duration_str = f"{duration:.3f}秒"
            else:
                duration_str = "未知"
            
            print("-" * 50)
            print(f"🔌 正在关闭数据库连接...")
            print(f"⏱️ 连接持续时间: {duration_str}")
            
            # 处理异常情况
            if exc_type is not None:
                print(f"⚠️ 检测到异常: {exc_type.__name__}: {exc_value}")
                if self.connection:
                    print(f"🔄 正在回滚事务...")
                    self.connection.rollback()
            else:
                # 正常情况下提交事务
                if self.connection:
                    self.connection.commit()
                    print(f"💾 事务已提交")
            
            # 关闭游标和连接
            if self.cursor:
                self.cursor.close()
                print(f"📝 游标已关闭")
            
            if self.connection:
                self.connection.close()
                print(f"🔒 数据库连接已关闭")
            
            print(f"✅ 资源清理完成")
            
        except Exception as e:
            print(f"❌ 关闭连接时发生错误: {e}")
        
        # 返回False，不抑制异常
        return False
    
    def query(self, sql: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """
        执行SQL查询
        
        Args:
            sql (str): SQL查询语句
            params (Tuple): 查询参数
        
        Returns:
            List[sqlite3.Row]: 查询结果列表
        
        Raises:
            RuntimeError: 当连接未建立时抛出
            sqlite3.Error: 当SQL执行出错时抛出
        """
        if not self.connection or not self.cursor:
            raise RuntimeError("数据库连接未建立，请在with语句中使用")
        
        try:
            print(f"🔍 执行查询: {sql}")
            if params:
                print(f"📋 查询参数: {params}")
            
            start_time = time.time()
            self.cursor.execute(sql, params)
            results = self.cursor.fetchall()
            execution_time = time.time() - start_time
            
            print(f"📊 查询结果: {len(results)} 行")
            print(f"⚡ 执行时间: {execution_time:.3f}秒")
            
            return results
            
        except sqlite3.Error as e:
            print(f"❌ SQL执行错误: {e}")
            raise
        except Exception as e:
            print(f"❌ 查询执行失败: {e}")
            raise
    
    def execute(self, sql: str, params: Tuple = ()) -> int:
        """
        执行SQL语句（INSERT, UPDATE, DELETE等）
        
        Args:
            sql (str): SQL语句
            params (Tuple): 参数
        
        Returns:
            int: 受影响的行数
        """
        if not self.connection or not self.cursor:
            raise RuntimeError("数据库连接未建立，请在with语句中使用")
        
        try:
            print(f"⚙️ 执行SQL: {sql}")
            if params:
                print(f"📋 参数: {params}")
            
            start_time = time.time()
            self.cursor.execute(sql, params)
            affected_rows = self.cursor.rowcount
            execution_time = time.time() - start_time
            
            print(f"📈 受影响行数: {affected_rows}")
            print(f"⚡ 执行时间: {execution_time:.3f}秒")
            
            return affected_rows
            
        except sqlite3.Error as e:
            print(f"❌ SQL执行错误: {e}")
            raise
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            raise
    
    def execute_many(self, sql: str, params_list: List[Tuple]) -> int:
        """
        批量执行SQL语句
        
        Args:
            sql (str): SQL语句
            params_list (List[Tuple]): 参数列表
        
        Returns:
            int: 总受影响行数
        """
        if not self.connection or not self.cursor:
            raise RuntimeError("数据库连接未建立，请在with语句中使用")
        
        try:
            print(f"🔄 批量执行SQL: {sql}")
            print(f"📦 批量大小: {len(params_list)}")
            
            start_time = time.time()
            self.cursor.executemany(sql, params_list)
            affected_rows = self.cursor.rowcount
            execution_time = time.time() - start_time
            
            print(f"📈 总受影响行数: {affected_rows}")
            print(f"⚡ 执行时间: {execution_time:.3f}秒")
            
            return affected_rows
            
        except sqlite3.Error as e:
            print(f"❌ 批量执行错误: {e}")
            raise
        except Exception as e:
            print(f"❌ 批量执行失败: {e}")
            raise

def create_sample_table(db: DatabaseConnection):
    """
    创建示例表
    
    Args:
        db (DatabaseConnection): 数据库连接实例
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        salary REAL NOT NULL,
        hire_date TEXT NOT NULL
    )
    """
    
    db.execute(create_table_sql)
    print("📋 员工表创建成功")

def insert_sample_data(db: DatabaseConnection):
    """
    插入示例数据
    
    Args:
        db (DatabaseConnection): 数据库连接实例
    """
    # 单条插入
    insert_sql = "INSERT INTO employees (name, department, salary, hire_date) VALUES (?, ?, ?, ?)"
    
    employees_data = [
        ("张三", "技术部", 8000.0, "2023-01-15"),
        ("李四", "销售部", 6500.0, "2023-02-20"),
        ("王五", "技术部", 9500.0, "2023-03-10"),
        ("赵六", "人事部", 7000.0, "2023-04-05"),
        ("钱七", "财务部", 7500.0, "2023-05-12")
    ]
    
    # 批量插入
    affected_rows = db.execute_many(insert_sql, employees_data)
    print(f"📊 成功插入 {len(employees_data)} 条员工记录")

def query_employees(db: DatabaseConnection):
    """
    查询员工信息
    
    Args:
        db (DatabaseConnection): 数据库连接实例
    """
    print("\n" + "=" * 60)
    print("📋 查询所有员工信息")
    print("=" * 60)
    
    # 查询所有员工
    all_employees = db.query("SELECT * FROM employees ORDER BY id")
    
    if all_employees:
        print(f"\n👥 员工列表 (共 {len(all_employees)} 人):")
        print("-" * 80)
        print(f"{'ID':<4} {'姓名':<10} {'部门':<10} {'薪资':<10} {'入职日期':<12}")
        print("-" * 80)
        
        for emp in all_employees:
            print(f"{emp['id']:<4} {emp['name']:<10} {emp['department']:<10} {emp['salary']:<10.0f} {emp['hire_date']:<12}")
    else:
        print("📭 没有找到员工记录")
    
    print("\n" + "=" * 60)
    print("🔍 按部门查询员工")
    print("=" * 60)
    
    # 按部门查询
    tech_employees = db.query(
        "SELECT * FROM employees WHERE department = ? ORDER BY salary DESC", 
        ("技术部",)
    )
    
    if tech_employees:
        print(f"\n💻 技术部员工 (共 {len(tech_employees)} 人):")
        print("-" * 60)
        for emp in tech_employees:
            print(f"• {emp['name']} - 薪资: ¥{emp['salary']:.0f} - 入职: {emp['hire_date']}")
    
    print("\n" + "=" * 60)
    print("📊 薪资统计查询")
    print("=" * 60)
    
    # 统计查询
    stats = db.query("""
        SELECT 
            department,
            COUNT(*) as employee_count,
            AVG(salary) as avg_salary,
            MAX(salary) as max_salary,
            MIN(salary) as min_salary
        FROM employees 
        GROUP BY department 
        ORDER BY avg_salary DESC
    """)
    
    if stats:
        print(f"\n📈 各部门薪资统计:")
        print("-" * 80)
        print(f"{'部门':<10} {'人数':<6} {'平均薪资':<10} {'最高薪资':<10} {'最低薪资':<10}")
        print("-" * 80)
        
        for stat in stats:
            print(f"{stat['department']:<10} {stat['employee_count']:<6} "
                  f"{stat['avg_salary']:<10.0f} {stat['max_salary']:<10.0f} {stat['min_salary']:<10.0f}")

def demonstrate_error_handling():
    """
    演示错误处理机制
    """
    print("\n" + "=" * 60)
    print("❌ 错误处理演示")
    print("=" * 60)
    
    try:
        with DatabaseConnection(":memory:") as db:
            # 故意执行错误的SQL
            print("\n🔍 尝试执行错误的SQL语句...")
            db.query("SELECT * FROM non_existent_table")
    except sqlite3.Error as e:
        print(f"✅ 成功捕获SQL错误: {e}")
    except Exception as e:
        print(f"✅ 成功捕获其他错误: {e}")
    
    print("\n🔍 尝试在上下文外使用连接...")
    try:
        db_outside = DatabaseConnection(":memory:")
        db_outside.query("SELECT 1")
    except RuntimeError as e:
        print(f"✅ 成功捕获运行时错误: {e}")

def main():
    """
    主函数：演示数据库上下文管理器的使用
    """
    print("=" * 80)
    print("🚀 Python数据库上下文管理器演示")
    print("=" * 80)
    
    try:
        # 使用with语句管理数据库连接
        with DatabaseConnection(":memory:") as db:
            print("\n📋 创建示例表和数据...")
            
            # 创建表
            create_sample_table(db)
            
            # 插入数据
            insert_sample_data(db)
            
            # 查询数据
            query_employees(db)
            
            print("\n" + "=" * 60)
            print("🔄 更新员工薪资")
            print("=" * 60)
            
            # 更新数据
            update_result = db.execute(
                "UPDATE employees SET salary = salary * 1.1 WHERE department = ?",
                ("技术部",)
            )
            print(f"💰 技术部员工薪资上调10%，影响 {update_result} 人")
            
            # 再次查询验证更新
            print("\n🔍 验证更新结果:")
            updated_tech = db.query(
                "SELECT name, salary FROM employees WHERE department = ? ORDER BY salary DESC",
                ("技术部",)
            )
            
            for emp in updated_tech:
                print(f"• {emp['name']}: ¥{emp['salary']:.0f}")
        
        print("\n" + "=" * 80)
        print("✅ 数据库操作完成，连接已自动关闭")
        print("=" * 80)
        
        # 演示错误处理
        demonstrate_error_handling()
        
        print("\n" + "=" * 80)
        print("🎯 上下文管理器特性总结:")
        print("• __enter__方法: 自动建立数据库连接")
        print("• __exit__方法: 自动关闭连接并处理异常")
        print("• with语句: 确保资源安全管理")
        print("• 异常处理: 自动回滚事务和清理资源")
        print("• 事务管理: 正常情况下自动提交事务")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()