import functools
import time


# 定义timer装饰器函数
def timer(func):
    """
    计算函数执行时间的装饰器
    
    Args:
        func: 被装饰的函数
    
    Returns:
        wrapper: 包装后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """
        装饰器内部的wrapper函数
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            result: 函数执行结果
        """
        # 记录函数开始时间
        start_time = time.time()
        
        # 执行被装饰的函数
        result = func(*args, **kwargs)
        
        # 记录函数结束时间
        end_time = time.time()
        
        # 计算执行时间
        execution_time = end_time - start_time
        
        # 打印函数执行时间
        print(f"⏱️  函数 '{func.__name__}' 执行时间: {execution_time:.6f} 秒")
        
        return result
    
    return wrapper

# 应用装饰器到fibonacci函数
@timer
def fibonacci(n):
    """
    计算斐波那契数列的第n项
    
    Args:
        n (int): 斐波那契数列的位置（从0开始）
    
    Returns:
        int: 斐波那契数列的第n项值
    """
    if n < 0:
        raise ValueError("输入必须是非负整数")
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        # 递归计算斐波那契数列
        return fibonacci(n - 1) + fibonacci(n - 2)

# 优化版本的斐波那契函数（使用动态规划）
@timer
def fibonacci_optimized(n):
    """
    使用动态规划优化的斐波那契数列计算
    
    Args:
        n (int): 斐波那契数列的位置（从0开始）
    
    Returns:
        int: 斐波那契数列的第n项值
    """
    if n < 0:
        raise ValueError("输入必须是非负整数")
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    
    # 使用动态规划避免重复计算
    a, b = 0, 1
    for i in range(2, n + 1):
        a, b = b, a + b
    
    return b

# 带缓存的斐波那契函数
@timer
def fibonacci_cached(n, cache={}):
    """
    使用缓存优化的斐波那契数列计算
    
    Args:
        n (int): 斐波那契数列的位置（从0开始）
        cache (dict): 缓存字典
    
    Returns:
        int: 斐波那契数列的第n项值
    """
    if n in cache:
        return cache[n]
    
    if n < 0:
        raise ValueError("输入必须是非负整数")
    elif n == 0:
        result = 0
    elif n == 1:
        result = 1
    else:
        result = fibonacci_cached(n - 1, cache) + fibonacci_cached(n - 2, cache)
    
    cache[n] = result
    return result

# 通用计时装饰器（支持自定义输出格式）
def advanced_timer(unit='seconds', precision=6):
    """
    高级计时装饰器，支持自定义时间单位和精度
    
    Args:
        unit (str): 时间单位 ('seconds', 'milliseconds', 'microseconds')
        precision (int): 小数点精度
    
    Returns:
        decorator: 装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # 根据单位转换时间
            if unit == 'milliseconds':
                execution_time *= 1000
                unit_symbol = 'ms'
            elif unit == 'microseconds':
                execution_time *= 1000000
                unit_symbol = 'μs'
            else:
                unit_symbol = 's'
            
            print(f"⚡ 函数 '{func.__name__}' 执行时间: {execution_time:.{precision}f} {unit_symbol}")
            
            return result
        return wrapper
    return decorator

# 使用高级计时装饰器
@advanced_timer(unit='milliseconds', precision=3)
def fibonacci_fast(n):
    """
    快速斐波那契计算（毫秒级计时）
    """
    if n < 0:
        raise ValueError("输入必须是非负整数")
    elif n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    
    return b

def main():
    """
    主函数：演示装饰器的使用
    """
    print("="*60)
    print("🚀 Python装饰器计时功能演示")
    print("="*60)
    
    # 测试不同的斐波那契实现
    test_numbers = [10, 20, 30, 35]
    
    print("\n📊 基础递归版本（较慢）:")
    for n in test_numbers[:2]:  # 只测试较小的数字，避免递归版本太慢
        try:
            result = fibonacci(n)
            print(f"   fibonacci({n}) = {result}")
        except Exception as e:
            print(f"   错误: {e}")
    
    print("\n⚡ 动态规划优化版本:")
    for n in test_numbers:
        try:
            result = fibonacci_optimized(n)
            print(f"   fibonacci_optimized({n}) = {result}")
        except Exception as e:
            print(f"   错误: {e}")
    
    print("\n💾 缓存优化版本:")
    for n in test_numbers:
        try:
            result = fibonacci_cached(n)
            print(f"   fibonacci_cached({n}) = {result}")
        except Exception as e:
            print(f"   错误: {e}")
    
    print("\n🏃 高级计时版本（毫秒显示）:")
    for n in test_numbers:
        try:
            result = fibonacci_fast(n)
            print(f"   fibonacci_fast({n}) = {result}")
        except Exception as e:
            print(f"   错误: {e}")
    
    print("\n" + "="*60)
    print("📈 性能对比总结:")
    print("• 基础递归版本: 时间复杂度O(2^n)，适合小数字")
    print("• 动态规划版本: 时间复杂度O(n)，空间复杂度O(1)")
    print("• 缓存版本: 时间复杂度O(n)，空间复杂度O(n)")
    print("• 装饰器功能: 无侵入式性能监控，支持多种时间单位")
    print("="*60)
    
    # 演示装饰器的其他特性
    print("\n🔧 装饰器特性演示:")
    print(f"• 函数名保持: {fibonacci.__name__}")
    print(f"• 函数文档: {fibonacci.__doc__[:30]}...")
    print(f"• 装饰器支持参数传递和返回值")
    
    # 测试错误处理
    print("\n❌ 错误处理测试:")
    try:
        fibonacci(-1)
    except ValueError as e:
        print(f"   捕获到预期错误: {e}")

if __name__ == "__main__":
    main()