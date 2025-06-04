import requests
import json

# 城市名称映射字典，用于中文城市名转换
CITY_NAME_MAP = {
    "北京": "Beijing",
    "上海": "Shanghai",
    "广州": "Guangzhou",
    "深圳": "Shenzhen",
    "杭州": "Hangzhou",
    "南京": "Nanjing",
    "武汉": "Wuhan",
    "成都": "Chengdu",
    "西安": "Xi'an",
    "重庆": "Chongqing",
    "天津": "Tianjin",
    "苏州": "Suzhou",
    "青岛": "Qingdao",
    "大连": "Dalian",
    "厦门": "Xiamen",
    "宁波": "Ningbo",
    "无锡": "Wuxi",
    "福州": "Fuzhou",
    "济南": "Jinan",
    "长沙": "Changsha"
}

def get_weather(city: str) -> dict:
    """
    获取指定城市的当前天气报告
    
    参数:
        city (str): 要获取天气报告的城市名称（中文或英文）
        
    返回:
        dict: 包含状态和结果或错误信息的字典
    """
    # API配置
    api_key = "9b946c4f3a0a478b8f964200251504"
    base_url = "http://api.weatherapi.com/v1/current.json"
    
    # 转换城市名
    query_city = CITY_NAME_MAP.get(city, city)
    
    try:
        # 发送API请求
        response = requests.get(
            base_url,
            params={"key": api_key, "q": query_city},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # 提取天气信息
            location = data["location"]["name"]
            country = data["location"]["country"]
            temp_c = data["current"]["temp_c"]
            temp_f = data["current"]["temp_f"]
            condition = data["current"]["condition"]["text"]
            humidity = data["current"]["humidity"]
            wind_kph = data["current"]["wind_kph"]
            
            # 构建天气报告
            report = (
                f"当前{city}({country})的天气为{condition}，"
                f"温度{temp_c}°C ({temp_f}°F)，"
                f"湿度{humidity}%，风速{wind_kph}公里/小时。"
            )
            
            # 返回详细信息用于显示
            weather_info = {
                'success': True,
                'city': location,
                'country': country,
                'temperature': temp_c,
                'temp_f': temp_f,
                'humidity': humidity,
                'description': condition,
                'wind_speed': wind_kph,
                'report': report
            }
            
            return weather_info
        else:
            return {
                "status": "error",
                "success": False,
                "error": f"无法获取'{city}'的天气信息。请检查城市名称是否正确。"
            }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': '请求超时，请检查网络连接'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': '网络连接错误，请检查网络设置'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'网络请求错误: {str(e)}'
        }
    except json.JSONDecodeError:
        return {
            'success': False,
            'error': 'JSON解析错误，服务器响应格式异常'
        }
    except KeyError as e:
        return {
            'success': False,
            'error': f'数据格式错误，缺少字段: {str(e)}'
        }
    except Exception as e:
        return {
            "status": "error",
            "success": False,
            "error": f"获取'{city}'的天气信息时出错: {str(e)}"
        }

def display_weather(weather_info):
    """
    格式化显示天气信息
    
    Args:
        weather_info (dict): 天气信息字典
    """
    if not weather_info['success']:
        print(f"❌ 错误: {weather_info['error']}")
        return
    
    print("\n" + "="*50)
    print(f"🌍 城市: {weather_info['city']}, {weather_info['country']}")
    print("="*50)
    print(f"🌡️  温度: {weather_info['temperature']}°C ({weather_info['temp_f']}°F)")
    print(f"💧 湿度: {weather_info['humidity']}%")
    print(f"☁️  天气: {weather_info['description']}")
    print(f"💨 风速: {weather_info['wind_speed']} 公里/小时")
    print("="*50)
    print(f"📝 天气报告: {weather_info['report']}")
    print("="*50)

def get_multiple_cities_weather(cities):
    """
    批量查询多个城市的天气信息
    
    Args:
        cities (list): 城市名称列表
    
    Returns:
        dict: 包含所有城市天气信息的字典
    """
    results = {}
    
    for city in cities:
        print(f"\n正在查询 {city} 的天气信息...")
        weather_info = get_weather(city)
        results[city] = weather_info
        
        if weather_info['success']:
            print(f"✅ {city}: {weather_info['temperature']}°C, {weather_info['description']}")
        else:
            print(f"❌ {city}: {weather_info['error']}")
    
    return results

def validate_api_connection():
    """
    验证API连接是否有效
    
    Returns:
        bool: API连接是否有效
    """
    # 尝试查询一个已知城市来验证API连接
    test_result = get_weather("London")
    return test_result['success']

def main():
    """
    主程序入口
    """
    print("🌤️  天气查询工具 (WeatherAPI版本)")
    print("="*50)
    
    # 验证API连接
    print("🔍 正在验证API连接...")
    if not validate_api_connection():
        print("❌ 错误: API连接失败")
        print("💡 提示: 请检查网络连接，或稍后重试")
        return
    
    print("✅ API连接验证成功！")
    
    while True:
        print("\n" + "-"*30)
        print("请选择操作:")
        print("1. 查询单个城市天气")
        print("2. 批量查询多个城市天气")
        print("3. 显示支持的中文城市列表")
        print("4. 退出程序")
        
        choice = input("请输入选项 (1-4): ").strip()
        
        if choice == '1':
            city_name = input("\n请输入城市名称 (中文或英文): ").strip()
            if city_name:
                weather_info = get_weather(city_name)
                display_weather(weather_info)
            else:
                print("❌ 错误: 城市名称不能为空")
        
        elif choice == '2':
            cities_input = input("\n请输入城市名称，用逗号分隔 (例如: 北京,上海,广州): ").strip()
            if cities_input:
                cities = [city.strip() for city in cities_input.split(',') if city.strip()]
                if cities:
                    results = get_multiple_cities_weather(cities)
                    
                    print("\n" + "="*50)
                    print("📊 批量查询结果汇总")
                    print("="*50)
                    
                    for city, info in results.items():
                        if info['success']:
                            print(f"✅ {city}: {info['temperature']}°C, {info['description']}")
                        else:
                            print(f"❌ {city}: 查询失败")
                else:
                    print("❌ 错误: 请输入有效的城市名称")
            else:
                print("❌ 错误: 城市名称不能为空")
        
        elif choice == '3':
            print("\n🏙️  支持的中文城市列表:")
            print("="*50)
            for chinese_name, english_name in CITY_NAME_MAP.items():
                print(f"🌆 {chinese_name} ({english_name})")
            print("="*50)
            print("💡 提示: 您也可以直接使用英文城市名称查询")
        
        elif choice == '4':
            print("\n👋 感谢使用天气查询工具，再见！")
            break
        
        else:
            print("❌ 错误: 请输入有效的选项 (1-4)")

def test_weather_api():
    """
    测试函数 - 测试WeatherAPI功能
    """
    print("🧪 测试天气API功能")
    print("="*50)
    
    # 测试单个城市查询
    test_cities = ["北京", "上海", "London", "New York"]
    
    for city in test_cities:
        print(f"\n测试查询: {city}")
        weather_info = get_weather(city)
        
        if weather_info['success']:
            print(f"✅ 成功: {city} - {weather_info['temperature']}°C")
            print(f"📝 报告: {weather_info['report']}")
        else:
            print(f"❌ 失败: {weather_info['error']}")
    
    return "测试完成"

if __name__ == "__main__":
    # 运行主程序
    main()
    
    # 如果需要测试，可以取消下面的注释
    # test_weather_api()