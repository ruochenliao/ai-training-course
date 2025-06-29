#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算器程序 - 支持加减乘除和幂运算
功能：
1. 获取用户输入的两个数字和运算符
2. 支持基本运算（+、-、*、/）和幂运算（**）
3. 异常处理：数字转换错误和除零错误
4. 格式化输出结果（保留两位小数）
"""

def get_number_input(prompt):
    """获取用户输入的数字，包含异常处理"""
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("错误：请输入有效的数字！")

def get_operator_input():
    """获取用户输入的运算符"""
    valid_operators = ['+', '-', '*', '/', '**']
    while True:
        operator = input("请输入运算符（+、-、*、/、**）：")
        if operator in valid_operators:
            return operator
        else:
            print("错误：请输入有效的运算符（+、-、*、/、**）！")

def calculate(num1, num2, operator):
    """执行计算操作"""
    try:
        if operator == '+':
            return num1 + num2
        elif operator == '-':
            return num1 - num2
        elif operator == '*':
            return num1 * num2
        elif operator == '/':
            if num2 == 0:
                raise ZeroDivisionError("除数不能为零！")
            return num1 / num2
        elif operator == '**':
            return num1 ** num2
        return None
    except ZeroDivisionError as e:
        raise e
    except OverflowError:
        raise OverflowError("计算结果超出范围！")
    except Exception as e:
        raise Exception(f"计算过程中发生错误：{e}")

def main():
    """主程序"""
    print("=" * 50)
    print("欢迎使用计算器程序！")
    print("支持运算：加法(+)、减法(-)、乘法(*)、除法(/)、幂运算(**)")
    print("=" * 50)
    
    while True:
        try:
            # 获取用户输入
            print("\n请输入计算信息：")
            num1 = get_number_input("请输入第一个数字：")
            operator = get_operator_input()
            num2 = get_number_input("请输入第二个数字：")
            
            # 执行计算
            result = calculate(num1, num2, operator)
            
            # 格式化输出结果
            print(f"\n计算结果：")
            print(f"{num1} {operator} {num2} = {result:.2f}")
            
        except ZeroDivisionError as e:
            print(f"\n错误：{e}")
        except OverflowError as e:
            print(f"\n错误：{e}")
        except Exception as e:
            print(f"\n发生未知错误：{e}")
        
        # 询问是否继续
        print("\n" + "-" * 30)
        continue_choice = input("是否继续计算？(y/n)：").lower()
        if continue_choice not in ['y', 'yes', '是']:
            print("感谢使用计算器程序！再见！")
            break

if __name__ == "__main__":
    main()