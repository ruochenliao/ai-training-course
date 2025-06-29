#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生信息管理系统 - 基于字典和列表的数据管理
功能：
1. 添加学生：自动生成ID，输入姓名、年龄和课程列表
2. 查看学生：遍历并格式化输出所有学生信息
3. 删除学生：根据ID删除指定学生
4. 交互界面：使用无限循环提供用户操作选项
关键语法：列表、字典、循环控制、字符串操作、列表推导式
"""

# 全局变量：学生列表和ID计数器
students = []  # 存储所有学生信息的列表
next_id = 1    # 自动生成学生ID的计数器

def add_student():
    """添加新学生"""
    global next_id
    
    print("\n=== 添加学生信息 ===")
    
    # 获取学生基本信息
    name = input("请输入学生姓名：").strip()
    if not name:
        print("错误：姓名不能为空！")
        return
    
    try:
        age = int(input("请输入学生年龄："))
        if age <= 0 or age > 150:
            print("错误：请输入有效的年龄（1-150）！")
            return
    except ValueError:
        print("错误：年龄必须是数字！")
        return
    
    # 获取课程列表（用逗号分隔）
    courses_input = input("请输入课程列表（用逗号分隔）：").strip()
    if not courses_input:
        courses = []
    else:
        # 使用列表推导式处理课程输入，去除空白字符
        courses = [course.strip() for course in courses_input.split(',') if course.strip()]
    
    # 创建学生字典
    student = {
        'id': next_id,
        'name': name,
        'age': age,
        'courses': courses
    }
    
    # 添加到学生列表
    students.append(student)
    next_id += 1
    
    print(f"\n✅ 学生 '{name}' 添加成功！学生ID：{student['id']}")
    if courses:
        print(f"📚 已选课程：{', '.join(courses)}")
    else:
        print("📚 暂无选课")

def view_students():
    """查看所有学生信息"""
    print("\n=== 学生信息列表 ===")
    
    if not students:
        print("📝 暂无学生信息")
        return
    
    print(f"📊 共有 {len(students)} 名学生：\n")
    
    # 遍历学生列表并格式化输出
    for i, student in enumerate(students, 1):
        print(f"【学生 {i}】")
        print(f"  🆔 学生ID：{student['id']}")
        print(f"  👤 姓名：{student['name']}")
        print(f"  🎂 年龄：{student['age']}岁")
        
        if student['courses']:
            print(f"  📚 课程：{', '.join(student['courses'])}")
        else:
            print(f"  📚 课程：暂无选课")
        
        print(f"  📈 课程数量：{len(student['courses'])}门")
        print("-" * 40)

def delete_student():
    """删除学生信息"""
    global students
    
    print("\n=== 删除学生信息 ===")
    
    if not students:
        print("📝 暂无学生信息可删除")
        return
    
    # 显示当前学生列表供参考
    print("当前学生列表：")
    for student in students:
        print(f"  ID: {student['id']} - {student['name']}")
    
    try:
        student_id = int(input("\n请输入要删除的学生ID："))
    except ValueError:
        print("错误：请输入有效的数字ID！")
        return
    
    # 查找要删除的学生
    student_to_delete = None
    for student in students:
        if student['id'] == student_id:
            student_to_delete = student
            break
    
    if student_to_delete is None:
        print(f"❌ 未找到ID为 {student_id} 的学生！")
        return
    
    # 确认删除
    confirm = input(f"确认删除学生 '{student_to_delete['name']}' (ID: {student_id})？(y/n)：").lower()
    if confirm not in ['y', 'yes', '是']:
        print("❌ 删除操作已取消")
        return
    
    # 使用列表推导式删除学生
    students = [student for student in students if student['id'] != student_id]
    
    print(f"✅ 学生 '{student_to_delete['name']}' 删除成功！")

def show_statistics():
    """显示统计信息"""
    print("\n=== 统计信息 ===")
    
    if not students:
        print("📝 暂无学生数据")
        return
    
    total_students = len(students)
    total_courses = sum(len(student['courses']) for student in students)
    avg_age = sum(student['age'] for student in students) / total_students
    
    # 统计最受欢迎的课程
    all_courses = []
    for student in students:
        all_courses.extend(student['courses'])
    
    course_count = {}
    for course in all_courses:
        course_count[course] = course_count.get(course, 0) + 1
    
    print(f"👥 学生总数：{total_students}")
    print(f"📚 课程总数：{total_courses}")
    print(f"🎂 平均年龄：{avg_age:.1f}岁")
    
    if course_count:
        popular_course = max(course_count, key=course_count.get)
        print(f"🔥 最受欢迎课程：{popular_course} ({course_count[popular_course]}人选修)")
    else:
        print("🔥 暂无课程数据")

def show_menu():
    """显示主菜单"""
    print("\n" + "=" * 50)
    print("🎓 学生信息管理系统")
    print("=" * 50)
    print("1. 📝 添加学生")
    print("2. 👀 查看学生")
    print("3. 🗑️  删除学生")
    print("4. 📊 统计信息")
    print("5. 🚪 退出系统")
    print("=" * 50)

def main():
    """主程序"""
    print("🎉 欢迎使用学生信息管理系统！")
    print("💡 本系统支持学生信息的添加、查看、删除和统计功能")
    
    # 使用无限循环实现交互界面
    while True:
        try:
            show_menu()
            choice = input("请选择操作（1-5）：").strip()
            
            if choice == '1':
                add_student()
            elif choice == '2':
                view_students()
            elif choice == '3':
                delete_student()
            elif choice == '4':
                show_statistics()
            elif choice == '5':
                print("\n👋 感谢使用学生信息管理系统！再见！")
                break
            else:
                print("❌ 无效选择，请输入1-5之间的数字！")
                
        except KeyboardInterrupt:
            print("\n\n👋 程序被用户中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 程序发生错误：{e}")
            print("请重试或联系管理员")
        
        # 暂停，等待用户查看结果
        input("\n按回车键继续...")

if __name__ == "__main__":
    main()