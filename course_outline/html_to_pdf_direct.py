"""
HTML精确转PDF工具 - 使用系统已安装的Chrome浏览器

准备工作:
1. 确保系统已安装Chrome浏览器
2. 安装依赖: pip install selenium webdriver-manager
"""

import base64
import os
import sys
import time

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def convert_html_to_pdf(html_file, output_file, page_size='A4'):
    """
    使用系统已安装的Chrome浏览器将HTML文件转换为PDF
    
    参数:
        html_file: HTML文件路径
        output_file: 输出的PDF文件路径
        page_size: 页面大小，如'A4', 'A3'等
    """
    if not os.path.exists(html_file):
        print(f"错误: HTML文件 {html_file} 不存在")
        return False
    
    print(f"正在将 {html_file} 精确转换为 {output_file}...")
    
    # 获取HTML文件的绝对路径
    html_path = os.path.abspath(html_file)
    file_url = f"file:///{html_path}"
    
    try:
        # 修改HTML文件，注入打印优化CSS
        optimize_html_for_printing(html_file)
        
        # 配置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无头模式
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--font-render-hinting=none')  # 改进字体渲染
        chrome_options.add_argument('--disable-web-security')  # 允许加载本地文件
        chrome_options.add_argument('--allow-file-access-from-files')  # 允许文件访问
        
        # 使用高分辨率设置
        chrome_options.add_argument('--high-dpi-support=1')
        chrome_options.add_argument('--force-device-scale-factor=1')
        
        # 设置PDF打印参数 - 优化边距和尺寸
        page_settings = {
            'landscape': False,
            'paperWidth': 8.27,  # A4宽度(英寸)
            'paperHeight': 11.69,  # A4高度(英寸)
            'marginTop': 0.5,     # 增加顶部边距
            'marginBottom': 0.5,  # 增加底部边距
            'marginLeft': 0.5,    # 增加左边距
            'marginRight': 0.5,   # 增加右边距
            'printBackground': True,
            'preferCSSPageSize': True,
            'scale': 0.9           # 缩小内容比例，确保不会溢出页面
        }
        
        # 根据指定的页面大小调整
        if page_size == 'A3':
            page_settings['paperWidth'] = 11.69
            page_settings['paperHeight'] = 16.54
        elif page_size == 'Letter':
            page_settings['paperWidth'] = 8.5
            page_settings['paperHeight'] = 11
        
        # 设置打印参数
        print_options = {
            'printBackground': True,
            'paperWidth': page_settings['paperWidth'],
            'paperHeight': page_settings['paperHeight'],
            'marginTop': page_settings['marginTop'],
            'marginBottom': page_settings['marginBottom'],
            'marginLeft': page_settings['marginLeft'],
            'marginRight': page_settings['marginRight'],
            'preferCSSPageSize': page_settings['preferCSSPageSize'],
            'landscape': page_settings['landscape'],
            'scale': page_settings['scale'],
            'displayHeaderFooter': False,
        }
        
        # 添加打印参数
        chrome_options.add_experimental_option('prefs', {
            'printing.print_preview_sticky_settings.appState': json.dumps({
                'recentDestinations': [{
                    'id': 'Save as PDF',
                    'origin': 'local',
                    'account': '',
                }],
                'selectedDestinationId': 'Save as PDF',
                'version': 2,
                'isHeaderFooterEnabled': False,
                'isCssBackgroundEnabled': True,
                'mediaSize': {
                    'width_microns': int(page_settings['paperWidth'] * 25400),
                    'height_microns': int(page_settings['paperHeight'] * 25400),
                    'name': page_size,
                },
                'customMargins': {
                    'top': page_settings['marginTop'],
                    'bottom': page_settings['marginBottom'],
                    'left': page_settings['marginLeft'],
                    'right': page_settings['marginRight'],
                },
            }),
            'savefile.default_directory': os.path.dirname(os.path.abspath(output_file))
        })
        
        # 自动下载和使用最新的ChromeDriver
        service = Service(ChromeDriverManager().install())
        
        # 初始化浏览器
        print("正在启动Chrome浏览器...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 设置窗口大小，确保能完整显示内容 - 使用更大的窗口
        driver.set_window_size(1600, 2000)
        
        # 导航到HTML文件
        print(f"正在加载HTML文件: {file_url}")
        driver.get(file_url)
        
        # 等待页面完全加载 - 增加等待时间确保样式正确加载
        print("等待页面完全加载...")
        time.sleep(7)  # 增加等待时间到7秒
        
        # 注入脚本确保字体和样式正确加载，并优化内容显示
        driver.execute_script("""
            // 确保所有字体已加载
            document.fonts.ready.then(function() {
                console.log('所有字体已加载完成');
            });
            
            // 强制应用样式
            var styles = document.querySelectorAll('style');
            for(var i=0; i<styles.length; i++) {
                styles[i].innerHTML = styles[i].innerHTML + ' ';
            }
            
            // 防止内容被截断的优化
            var modules = document.querySelectorAll('.module');
            modules.forEach(function(module) {
                module.style.pageBreakInside = 'avoid';
                module.style.breakInside = 'avoid';
            });
            
            // 确保颜色正确显示
            var elements = document.querySelectorAll('[style*="color"]');
            elements.forEach(function(el) {
                var style = window.getComputedStyle(el);
                var color = style.color;
                el.style.color = color;
            });
        """)
        
        # 再等待一下确保脚本执行完成
        time.sleep(3)
        
        # 生成PDF
        print("正在生成PDF...")
        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", print_options)
        
        # 保存PDF文件
        with open(output_file, 'wb') as f:
            f.write(base64.b64decode(pdf_data['data']))
        
        # 关闭浏览器
        driver.quit()
        
        # 恢复原始HTML文件
        restore_original_html(html_file)
        
        print(f"转换完成! PDF已保存至: {output_file}")
        return True
    
    except WebDriverException as e:
        print(f"浏览器驱动错误: {str(e)}")
        print("请确保系统已安装Chrome浏览器并且版本与驱动兼容")
        import traceback
        traceback.print_exc()
        # 恢复原始HTML文件
        restore_original_html(html_file)
        return False
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        # 恢复原始HTML文件
        restore_original_html(html_file)
        return False

def optimize_html_for_printing(html_file):
    """为打印优化HTML文件，添加打印特定的CSS"""
    try:
        # 创建备份
        backup_file = html_file + '.bak'
        if not os.path.exists(backup_file):
            import shutil
            shutil.copy2(html_file, backup_file)
        
        # 读取HTML内容
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加打印优化CSS
        print_css = """
        <style>
            @media print {
                body {
                    width: 100%;
                    margin: 0;
                    padding: 0;
                    font-family: 'Microsoft YaHei', 'SimSun', Arial, sans-serif !important;
                }
                
                .module {
                    page-break-inside: avoid;
                    break-inside: avoid;
                    margin-bottom: 20px;
                }
                
                h1, h2, h3 {
                    page-break-after: avoid;
                    break-after: avoid;
                }
                
                .stage {
                    page-break-inside: avoid;
                    break-inside: avoid;
                }
                
                .module-topics {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 10px;
                }
                
                .topic {
                    flex: 1 0 45%;
                    min-width: 200px;
                }
                
                @page {
                    margin: 1cm;
                    size: A4;
                }
                
                /* 避免文本过小 */
                p, div, li {
                    font-size: 11pt !important;
                    line-height: 1.5 !important;
                }
                
                /* 确保颜色正确打印 */
                * {
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                    color-adjust: exact !important;
                }
            }
        </style>
        """
        
        # 在</head>前插入打印CSS
        if '</head>' in content:
            content = content.replace('</head>', print_css + '</head>')
        else:
            # 如果没有</head>标签，就在文件开头添加
            content = print_css + content
        
        # 写回文件
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("已添加打印优化CSS")
        return True
    except Exception as e:
        print(f"添加打印CSS时出错: {str(e)}")
        return False

def restore_original_html(html_file):
    """恢复原始HTML文件"""
    backup_file = html_file + '.bak'
    if os.path.exists(backup_file):
        import shutil
        shutil.copy2(backup_file, html_file)
        print("已恢复原始HTML文件")
        return True
    return False

def show_help():
    """显示使用说明"""
    print("HTML精确转PDF工具 - 系统Chrome版")
    print("\n准备工作:")
    print("1. 确保系统已安装Chrome浏览器")
    print("2. 安装依赖: pip install selenium webdriver-manager")
    print("\n用法:")
    print(f"  python {os.path.basename(__file__)} <html文件路径> [pdf输出路径] [页面大小]")
    print("\n参数:")
    print("  html文件路径    要转换的HTML文件路径")
    print("  pdf输出路径     输出的PDF文件路径 (可选，默认为HTML文件名+.pdf)")
    print("  页面大小        PDF页面大小，如'A4'(默认)、'A3'、'Letter'等")
    print("\n示例:")
    print(f"  python {os.path.basename(__file__)} curriculum.html")
    print(f"  python {os.path.basename(__file__)} curriculum.html 课程大纲.pdf")
    print(f"  python {os.path.basename(__file__)} curriculum.html 课程大纲.pdf A3")

if __name__ == "__main__":
    # 导入json模块 (在这里导入避免全局导入不必要的模块)
    import json
    
    # 处理命令行参数
    if len(sys.argv) < 2 or sys.argv[1] in ["--help", "-h"]:
        show_help()
        sys.exit(0)
    
    # 获取HTML文件路径
    html_file = sys.argv[1]
    
    # 处理输出文件参数
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # 默认输出文件名为HTML文件名加上.pdf后缀
        base_name = os.path.splitext(os.path.basename(html_file))[0]
        output_file = f"{base_name}.pdf"
    
    # 处理页面大小参数
    if len(sys.argv) >= 4:
        page_size = sys.argv[3]
    else:
        page_size = 'A4'
    
    # 执行转换
    success = convert_html_to_pdf(html_file, output_file, page_size)
    
    if success:
        print("\n转换成功完成!")
    else:
        print("\n转换失败，请检查错误信息。")
        sys.exit(1) 