#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
凯撒密码文件加密/解密工具
功能：
1. 实现凯撒密码加密和解密算法
2. 支持文件的批量加密和解密
3. 处理大小写字母，保持非字母字符不变
4. 自动生成加密/解密后的新文件
关键语法：函数定义、文件操作、字符串处理、条件判断
"""

import os

def caesar_cipher(text, shift, mode='encrypt'):
    """
    凯撒密码加密/解密函数
    
    Args:
        text (str): 要处理的文本
        shift (int): 偏移量（1-25）
        mode (str): 模式，'encrypt'为加密，'decrypt'为解密
    
    Returns:
        str: 处理后的文本
    """
    result = ""
    
    # 解密时偏移量取负值
    if mode == 'decrypt':
        shift = -shift
    
    for char in text:
        if char.isalpha():
            # 判断是大写还是小写字母
            if char.isupper():
                # 处理大写字母 (A-Z: ASCII 65-90)
                shifted = (ord(char) - ord('A') + shift) % 26
                result += chr(shifted + ord('A'))
            else:
                # 处理小写字母 (a-z: ASCII 97-122)
                shifted = (ord(char) - ord('a') + shift) % 26
                result += chr(shifted + ord('a'))
        else:
            # 非字母字符保持不变
            result += char
    
    return result

def encrypt_file(input_file, shift):
    """
    加密文件
    
    Args:
        input_file (str): 输入文件路径
        shift (int): 偏移量
    
    Returns:
        str: 输出文件路径
    """
    try:
        # 读取原文件内容
        with open(input_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 加密内容
        encrypted_content = caesar_cipher(content, shift, 'encrypt')
        
        # 生成输出文件名（添加encrypted_前缀）
        dir_name = os.path.dirname(input_file)
        base_name = os.path.basename(input_file)
        name, ext = os.path.splitext(base_name)
        output_file = os.path.join(dir_name, f"encrypted_{name}{ext}")
        
        # 写入加密后的内容
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(encrypted_content)
        
        print(f"✅ 文件加密成功！")
        print(f"📁 原文件：{input_file}")
        print(f"🔒 加密文件：{output_file}")
        print(f"🔑 偏移量：{shift}")
        
        return output_file
        
    except FileNotFoundError:
        print(f"❌ 错误：找不到文件 '{input_file}'")
        return None
    except Exception as e:
        print(f"❌ 加密过程中发生错误：{e}")
        return None

def decrypt_file(input_file, shift):
    """
    解密文件
    
    Args:
        input_file (str): 输入文件路径
        shift (int): 偏移量
    
    Returns:
        str: 输出文件路径
    """
    try:
        # 读取加密文件内容
        with open(input_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 解密内容
        decrypted_content = caesar_cipher(content, shift, 'decrypt')
        
        # 生成输出文件名（添加decrypted_前缀）
        dir_name = os.path.dirname(input_file)
        base_name = os.path.basename(input_file)
        name, ext = os.path.splitext(base_name)
        output_file = os.path.join(dir_name, f"decrypted_{name}{ext}")
        
        # 写入解密后的内容
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(decrypted_content)
        
        print(f"✅ 文件解密成功！")
        print(f"🔒 加密文件：{input_file}")
        print(f"📁 解密文件：{output_file}")
        print(f"🔑 偏移量：{shift}")
        
        return output_file
        
    except FileNotFoundError:
        print(f"❌ 错误：找不到文件 '{input_file}'")
        return None
    except Exception as e:
        print(f"❌ 解密过程中发生错误：{e}")
        return None

def create_sample_file():
    """
    创建示例文件用于测试
    """
    sample_content = """Hello World! This is a sample text file for Caesar Cipher encryption.
你好世界！这是一个用于凯撒密码加密的示例文本文件。
ABCDEFGHIJKLMNOPQRSTUVWXYZ
abcdefghijklmnopqrstuvwxyz
123456789!@#$%^&*()

This file contains:
- English letters (both uppercase and lowercase)
- Chinese characters (will remain unchanged)
- Numbers and special characters (will remain unchanged)
- Multiple lines of text

Perfect for testing the Caesar Cipher algorithm!"""
    
    sample_file = "sample_text.txt"
    
    try:
        with open(sample_file, 'w', encoding='utf-8') as file:
            file.write(sample_content)
        print(f"📝 示例文件已创建：{sample_file}")
        return sample_file
    except Exception as e:
        print(f"❌ 创建示例文件时发生错误：{e}")
        return None

def validate_shift(shift_str):
    """
    验证偏移量输入
    
    Args:
        shift_str (str): 用户输入的偏移量字符串
    
    Returns:
        int or None: 有效的偏移量或None
    """
    try:
        shift = int(shift_str)
        if 1 <= shift <= 25:
            return shift
        else:
            print("❌ 偏移量必须在1-25之间！")
            return None
    except ValueError:
        print("❌ 请输入有效的数字！")
        return None

def show_menu():
    """
    显示主菜单
    """
    print("\n" + "="*60)
    print("🔐 凯撒密码文件加密/解密工具")
    print("="*60)
    print("1. 🔒 加密文件")
    print("2. 🔓 解密文件")
    print("3. 📝 创建示例文件")
    print("4. 🧪 测试凯撒密码算法")
    print("5. 📖 查看帮助信息")
    print("6. 🚪 退出程序")
    print("="*60)

def test_caesar_cipher():
    """
    测试凯撒密码算法
    """
    print("\n=== 🧪 凯撒密码算法测试 ===")
    
    # 使用固定测试文本和偏移量，避免交互式输入
    test_text = "Hello World! ABC xyz 123"
    shift = 3
    
    print(f"📝 原文本：{test_text}")
    print(f"🔑 偏移量：{shift}")
    
    # 加密
    encrypted = caesar_cipher(test_text, shift, 'encrypt')
    print(f"🔒 加密后：{encrypted}")
    
    # 解密
    decrypted = caesar_cipher(encrypted, shift, 'decrypt')
    print(f"🔓 解密后：{decrypted}")
    
    # 验证
    if test_text == decrypted:
        print("✅ 测试通过！加密解密过程正确。")
        return True
    else:
        print("❌ 测试失败！加密解密过程有误。")
        return False

def show_help():
    """
    显示帮助信息
    """
    print("\n=== 📖 帮助信息 ===")
    print("\n🔐 凯撒密码原理：")
    print("凯撒密码是一种简单的替换密码，通过将字母表中的每个字母")
    print("替换为字母表中固定位置后的字母来实现加密。")
    print("\n🔧 使用说明：")
    print("1. 选择加密或解密功能")
    print("2. 输入文件路径（支持相对路径和绝对路径）")
    print("3. 输入偏移量（1-25之间的整数）")
    print("4. 程序会自动生成新文件，文件名添加相应前缀")
    print("\n📋 注意事项：")
    print("• 只有英文字母会被加密/解密")
    print("• 大小写字母分别处理")
    print("• 数字、标点符号、中文等字符保持不变")
    print("• 加密文件名格式：encrypted_原文件名")
    print("• 解密文件名格式：decrypted_原文件名")
    print("\n💡 示例：")
    print("原文：Hello World!")
    print("偏移量：3")
    print("加密后：Khoor Zruog!")

def main():
    """
    主程序
    """
    print("🎉 欢迎使用凯撒密码文件加密/解密工具！")
    print("💡 本工具支持文件的凯撒密码加密和解密功能")
    
    while True:
        try:
            show_menu()
            choice = input("请选择操作（1-6）：").strip()
            
            if choice == '1':
                # 加密文件
                print("\n=== 🔒 文件加密 ===")
                file_path = input("请输入要加密的文件路径：").strip()
                if not file_path:
                    print("❌ 文件路径不能为空！")
                    continue
                
                shift_str = input("请输入偏移量（1-25）：").strip()
                shift = validate_shift(shift_str)
                
                if shift is not None:
                    encrypt_file(file_path, shift)
                    
            elif choice == '2':
                # 解密文件
                print("\n=== 🔓 文件解密 ===")
                file_path = input("请输入要解密的文件路径：").strip()
                if not file_path:
                    print("❌ 文件路径不能为空！")
                    continue
                
                shift_str = input("请输入偏移量（1-25）：").strip()
                shift = validate_shift(shift_str)
                
                if shift is not None:
                    decrypt_file(file_path, shift)
                    
            elif choice == '3':
                # 创建示例文件
                print("\n=== 📝 创建示例文件 ===")
                create_sample_file()
                
            elif choice == '4':
                # 测试算法
                test_caesar_cipher()
                
            elif choice == '5':
                # 查看帮助
                show_help()
                
            elif choice == '6':
                print("\n👋 感谢使用凯撒密码工具！再见！")
                break
                
            else:
                print("❌ 无效选择，请输入1-6之间的数字！")
                
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