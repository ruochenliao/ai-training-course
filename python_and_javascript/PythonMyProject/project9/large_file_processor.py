import os
import re
from collections import Counter
from typing import Generator, Dict, List, Tuple

def large_file_processor(file_path: str) -> Generator[str, None, None]:
    """
    大文件处理生成器函数
    
    使用生成器逐行处理文件内容，节省内存占用。
    每行处理：去除空白字符并转换为大写。
    
    Args:
        file_path (str): 文件路径
    
    Yields:
        str: 处理后的文件行内容
    
    Raises:
        FileNotFoundError: 当文件不存在时抛出
        IOError: 当文件读取出错时抛出
    """
    try:
        print(f"📂 开始处理文件: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            line_count = 0
            
            for line in file:
                line_count += 1
                
                # 去除空白字符并转换为大写
                processed_line = line.strip().upper()
                
                # 跳过空行
                if processed_line:
                    print(f"🔄 处理第 {line_count} 行: {processed_line[:50]}{'...' if len(processed_line) > 50 else ''}")
                    yield processed_line
                
                # 每处理100行显示一次进度
                if line_count % 100 == 0:
                    print(f"📊 已处理 {line_count} 行")
        
        print(f"✅ 文件处理完成，共处理 {line_count} 行")
        
    except FileNotFoundError:
        print(f"❌ 错误：文件 '{file_path}' 不存在")
        raise
    except IOError as e:
        print(f"❌ 文件读取错误: {e}")
        raise
    except Exception as e:
        print(f"❌ 处理文件时发生未知错误: {e}")
        raise

def word_counter(text_generator: Generator[str, None, None]) -> Dict[str, int]:
    """
    词频统计函数
    
    接收生成器产生的文本行，统计所有单词的出现频率。
    使用字典存储单词计数，支持中英文混合文本。
    
    Args:
        text_generator (Generator[str, None, None]): 文本行生成器
    
    Returns:
        Dict[str, int]: 单词频率字典
    """
    print("\n📊 开始统计词频...")
    
    word_counts = {}
    total_words = 0
    processed_lines = 0
    
    try:
        for line in text_generator:
            processed_lines += 1
            
            # 使用正则表达式提取单词（支持中英文）
            # 匹配英文单词、中文字符、数字
            words = re.findall(r'[a-zA-Z]+|[\u4e00-\u9fa5]+|\d+', line)
            
            for word in words:
                # 过滤掉长度小于2的单词（避免无意义的短词）
                if len(word) >= 2:
                    total_words += 1
                    
                    # 统计词频
                    if word in word_counts:
                        word_counts[word] += 1
                    else:
                        word_counts[word] = 1
            
            # 每处理50行显示一次进度
            if processed_lines % 50 == 0:
                print(f"📈 已统计 {processed_lines} 行，发现 {len(word_counts)} 个不同单词")
    
    except Exception as e:
        print(f"❌ 词频统计过程中发生错误: {e}")
        raise
    
    print(f"\n✅ 词频统计完成！")
    print(f"📋 统计结果：")
    print(f"   • 处理行数: {processed_lines}")
    print(f"   • 总单词数: {total_words}")
    print(f"   • 不同单词数: {len(word_counts)}")
    
    return word_counts

def get_top_words(word_counts: Dict[str, int], top_n: int = 10) -> List[Tuple[str, int]]:
    """
    获取出现频率最高的N个单词
    
    Args:
        word_counts (Dict[str, int]): 单词频率字典
        top_n (int): 返回前N个单词，默认为10
    
    Returns:
        List[Tuple[str, int]]: 按频率排序的单词列表
    """
    print(f"\n🏆 获取出现频率最高的 {top_n} 个单词...")
    
    # 使用Counter进行排序，获取最常见的单词
    counter = Counter(word_counts)
    top_words = counter.most_common(top_n)
    
    return top_words

def display_top_words(top_words: List[Tuple[str, int]], top_n: int = 10):
    """
    美观地显示高频词汇统计结果
    
    Args:
        top_words (List[Tuple[str, int]]): 高频词汇列表
        top_n (int): 显示的词汇数量
    """
    print(f"\n" + "=" * 60)
    print(f"🎯 出现频率最高的 {top_n} 个单词")
    print(f"=" * 60)
    
    if not top_words:
        print("📭 没有找到任何单词")
        return
    
    # 计算最大频率，用于绘制简单的条形图
    max_count = top_words[0][1] if top_words else 0
    
    print(f"{'排名':<4} {'单词':<15} {'频率':<8} {'占比':<8} {'可视化':<20}")
    print("-" * 60)
    
    total_top_words = sum(count for _, count in top_words)
    
    for i, (word, count) in enumerate(top_words, 1):
        # 计算占比
        percentage = (count / total_top_words) * 100
        
        # 创建简单的条形图
        bar_length = int((count / max_count) * 15)
        bar = "█" * bar_length + "░" * (15 - bar_length)
        
        print(f"{i:<4} {word:<15} {count:<8} {percentage:<7.1f}% {bar}")
    
    print("-" * 60)
    print(f"📊 统计说明：")
    print(f"   • 总词频: {total_top_words}")
    print(f"   • 最高频率: {max_count}")
    print(f"   • 平均频率: {total_top_words / len(top_words):.1f}")

def create_sample_file(file_path: str):
    """
    创建示例文件用于测试
    
    Args:
        file_path (str): 示例文件路径
    """
    print(f"📝 创建示例文件: {file_path}")
    
    sample_content = """Python是一种高级编程语言，由Guido van Rossum于1989年发明。
Python具有简洁、易读的语法，使得编程变得更加高效和愉快。
Python广泛应用于Web开发、数据科学、人工智能、自动化脚本等领域。
Python的设计哲学强调代码的可读性和简洁性。
Python拥有丰富的标准库和第三方库生态系统。

Python supports multiple programming paradigms including procedural, object-oriented, and functional programming.
Python is an interpreted language which makes development and testing faster.
Python has a large and active community that contributes to its continuous improvement.
Python's syntax is designed to be intuitive and its code structure is enforced through indentation.
Python is cross-platform and runs on Windows, macOS, Linux, and many other operating systems.

Data science and machine learning are major application areas for Python.
Libraries like NumPy, Pandas, Matplotlib, and Scikit-learn make Python powerful for data analysis.
Python's simplicity makes it an excellent choice for beginners learning programming.
Python is also used in admin_web development with frameworks like Django and Flask.
Python automation scripts can help streamline repetitive tasks and improve productivity.

人工智能和机器学习是Python的重要应用领域。
Python的简单性使其成为初学者学习编程的绝佳选择。
Python也用于使用Django和Flask等框架进行Web开发。
Python自动化脚本可以帮助简化重复性任务并提高生产力。
Python的跨平台特性使其能在各种操作系统上运行。

The Python Package Index (PyPI) contains hundreds of thousands of third-party packages.
Python's duck typing and dynamic nature provide flexibility in programming.
Python supports both small scripts and large applications with equal effectiveness.
Python's extensive documentation and tutorials make learning accessible to everyone.
Python continues to evolve with regular updates and new features being added.
"""
    
    try:
        # 只有当文件路径包含目录时才创建目录
        dir_path = os.path.dirname(file_path)
        if dir_path:  # 如果目录路径不为空
            os.makedirs(dir_path, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(sample_content)
        
        print(f"✅ 示例文件创建成功")
        print(f"📄 文件大小: {os.path.getsize(file_path)} 字节")
        
    except Exception as e:
        print(f"❌ 创建示例文件失败: {e}")
        raise

def analyze_file_with_generator(file_path: str, top_n: int = 10):
    """
    使用生成器分析文件的完整流程
    
    Args:
        file_path (str): 文件路径
        top_n (int): 显示前N个高频词汇
    """
    try:
        print(f"\n🚀 开始分析文件: {file_path}")
        print(f"🎯 目标：找出出现频率最高的 {top_n} 个单词")
        print("=" * 70)
        
        # 步骤1：使用生成器处理文件
        print("\n📋 步骤1：使用生成器逐行处理文件")
        text_generator = large_file_processor(file_path)
        
        # 步骤2：统计词频
        print("\n📋 步骤2：统计词频")
        word_counts = word_counter(text_generator)
        
        # 步骤3：获取高频词汇
        print("\n📋 步骤3：分析高频词汇")
        top_words = get_top_words(word_counts, top_n)
        
        # 步骤4：显示结果
        print("\n📋 步骤4：显示分析结果")
        display_top_words(top_words, top_n)
        
        # 额外统计信息
        print(f"\n" + "=" * 60)
        print(f"📈 详细统计信息")
        print(f"=" * 60)
        print(f"📊 词汇分布分析：")
        
        # 分析词汇长度分布
        length_distribution = {}
        for word in word_counts:
            length = len(word)
            length_distribution[length] = length_distribution.get(length, 0) + 1
        
        print(f"   • 词汇长度分布:")
        for length in sorted(length_distribution.keys()):
            count = length_distribution[length]
            print(f"     - {length}字符: {count}个词汇")
        
        # 分析单次出现的词汇
        single_occurrence = sum(1 for count in word_counts.values() if count == 1)
        print(f"   • 只出现一次的词汇: {single_occurrence}个 ({single_occurrence/len(word_counts)*100:.1f}%)")
        
        # 分析高频词汇
        high_frequency = sum(1 for count in word_counts.values() if count >= 5)
        print(f"   • 出现5次以上的词汇: {high_frequency}个 ({high_frequency/len(word_counts)*100:.1f}%)")
        
        print(f"\n✅ 文件分析完成！")
        
    except Exception as e:
        print(f"❌ 文件分析过程中发生错误: {e}")
        raise

def demonstrate_generator_benefits():
    """
    演示生成器的优势
    """
    print(f"\n" + "=" * 70)
    print(f"🎓 生成器技术优势演示")
    print(f"=" * 70)
    
    print(f"\n🔍 生成器 vs 传统方法对比：")
    print(f"\n📊 传统方法（一次性读取全部内容）：")
    print(f"   ❌ 内存占用：文件大小 × 1倍（全部加载到内存）")
    print(f"   ❌ 处理速度：需要等待全部读取完成才能开始处理")
    print(f"   ❌ 内存风险：大文件可能导致内存不足")
    print(f"   ❌ 灵活性：无法中途停止或暂停处理")
    
    print(f"\n🚀 生成器方法（逐行处理）：")
    print(f"   ✅ 内存占用：仅占用单行内容的内存空间")
    print(f"   ✅ 处理速度：边读取边处理，响应更快")
    print(f"   ✅ 内存安全：无论文件多大都不会内存溢出")
    print(f"   ✅ 灵活性：可以随时中断或暂停处理")
    print(f"   ✅ 可扩展性：适用于无限数据流处理")
    
    print(f"\n💡 生成器核心特性：")
    print(f"   🔄 惰性求值：只在需要时才计算下一个值")
    print(f"   💾 内存高效：不会一次性加载所有数据")
    print(f"   🔁 可迭代：支持for循环和迭代器协议")
    print(f"   ⏸️ 状态保持：能够记住上次执行的位置")
    print(f"   🎯 yield关键字：暂停函数执行并返回值")
    
    print(f"\n🛠️ 适用场景：")
    print(f"   📁 大文件处理：日志分析、数据清洗")
    print(f"   🌊 数据流处理：实时数据分析")
    print(f"   🔢 数学序列：斐波那契数列、素数生成")
    print(f"   🕸️ 网络爬虫：分页数据获取")
    print(f"   🗄️ 数据库查询：大结果集分批处理")

def main():
    """
    主函数：演示生成器处理大文件的完整流程
    """
    print("=" * 80)
    print("🚀 Python生成器大文件处理演示")
    print("=" * 80)
    
    # 定义文件路径
    sample_file = "sample_large_file.txt"
    
    try:
        # 创建示例文件
        print("\n📋 步骤1：准备测试数据")
        create_sample_file(sample_file)
        
        # 使用生成器分析文件
        print("\n📋 步骤2：生成器文件分析")
        analyze_file_with_generator(sample_file, top_n=10)
        
        # 演示生成器优势
        print("\n📋 步骤3：技术优势说明")
        demonstrate_generator_benefits()
        
        print(f"\n" + "=" * 80)
        print(f"🎯 核心技术要点总结：")
        print(f"• 生成器函数：使用yield关键字实现惰性求值")
        print(f"• 内存优化：逐行处理避免大文件内存溢出")
        print(f"• 字典操作：高效的词频统计和数据存储")
        print(f"• 文件迭代：安全的文件读取和异常处理")
        print(f"• 数据分析：Counter类实现高效排序统计")
        print(f"=" * 80)
        
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理示例文件
        try:
            if os.path.exists(sample_file):
                os.remove(sample_file)
                print(f"\n🧹 清理示例文件: {sample_file}")
        except Exception as e:
            print(f"⚠️ 清理文件时出错: {e}")

if __name__ == "__main__":
    main()