import pandas as pd

# 1. 创建包含姓名、年龄、工资和部门的字典数据
data = {
    '姓名': ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十'],
    '年龄': [25, 32, 28, 35, 29, 31, 27, 33],
    '工资': [8000, 12000, 9500, 15000, 10000, 11500, 8500, 13000],
    '部门': ['技术部', '销售部', '技术部', '管理部', '销售部', '技术部', '人事部', '管理部']
}

print("="*50)
print("Pandas数据分析示例")
print("="*50)

# 2. 将字典转换为DataFrame
df = pd.DataFrame(data)
print("\n1. 原始数据:")
print(df)
print(f"\n数据形状: {df.shape}")
print(f"数据类型:\n{df.dtypes}")

# 3. 计算平均工资：使用mean()方法
average_salary = df['工资'].mean()
print(f"\n2. 全体员工平均工资: {average_salary:.2f}元")

# 4. 按部门分组计算平均工资：使用groupby()
dept_avg_salary = df.groupby('部门')['工资'].mean()
print("\n3. 各部门平均工资:")
for dept, avg_sal in dept_avg_salary.items():
    print(f"   {dept}: {avg_sal:.2f}元")

# 更详细的分组统计
dept_stats = df.groupby('部门').agg({
    '工资': ['mean', 'max', 'min', 'count'],
    '年龄': 'mean'
})
print("\n4. 各部门详细统计:")
print(dept_stats)

# 5. 筛选年龄大于30的员工：使用布尔索引
older_employees = df[df['年龄'] > 30]
print("\n5. 年龄大于30岁的员工:")
print(older_employees)
print(f"\n年龄大于30岁的员工数量: {len(older_employees)}人")
print(f"年龄大于30岁员工的平均工资: {older_employees['工资'].mean():.2f}元")

# 6. 格式化输出分析结果
print("\n" + "="*50)
print("数据分析总结报告")
print("="*50)

# 基本统计信息
print("\n📊 基本统计信息:")
print(f"• 总员工数: {len(df)}人")
print(f"• 平均年龄: {df['年龄'].mean():.1f}岁")
print(f"• 平均工资: {df['工资'].mean():.2f}元")
print(f"• 工资范围: {df['工资'].min()}-{df['工资'].max()}元")

# 部门分析
print("\n🏢 部门分析:")
dept_count = df['部门'].value_counts()
for dept, count in dept_count.items():
    avg_sal = df[df['部门'] == dept]['工资'].mean()
    print(f"• {dept}: {count}人, 平均工资{avg_sal:.2f}元")

# 年龄分析
print("\n👥 年龄分析:")
young_employees = df[df['年龄'] <= 30]
old_employees = df[df['年龄'] > 30]
print(f"• 30岁及以下: {len(young_employees)}人, 平均工资{young_employees['工资'].mean():.2f}元")
print(f"• 30岁以上: {len(old_employees)}人, 平均工资{old_employees['工资'].mean():.2f}元")

# 工资分析
print("\n💰 工资分析:")
high_salary = df[df['工资'] >= 12000]
print(f"• 高薪员工(≥12000元): {len(high_salary)}人")
print(f"• 工资中位数: {df['工资'].median():.2f}元")
print(f"• 工资标准差: {df['工资'].std():.2f}元")

# 相关性分析
print("\n📈 年龄与工资相关性:")
correlation = df['年龄'].corr(df['工资'])
print(f"• 相关系数: {correlation:.3f}")
if correlation > 0.5:
    print("• 年龄与工资呈强正相关")
elif correlation > 0.3:
    print("• 年龄与工资呈中等正相关")
elif correlation > 0:
    print("• 年龄与工资呈弱正相关")
else:
    print("• 年龄与工资相关性较弱")

print("\n" + "="*50)
print("分析完成！")
print("="*50)

# 额外功能：数据导出
print("\n💾 数据导出功能演示:")
# 保存为CSV文件
df.to_csv('employee_data.csv', index=False, encoding='utf-8-sig')
print("• 原始数据已保存为 employee_data.csv")

# 保存分析结果
analysis_result = {
    '总员工数': len(df),
    '平均年龄': df['年龄'].mean(),
    '平均工资': df['工资'].mean(),
    '各部门平均工资': dept_avg_salary.to_dict(),
    '30岁以上员工数': len(older_employees)
}

import json
with open('analysis_result.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_result, f, ensure_ascii=False, indent=2)
print("• 分析结果已保存为 analysis_result.json")