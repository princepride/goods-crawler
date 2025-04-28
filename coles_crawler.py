import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import email
from bs4 import BeautifulSoup
import pandas as pd

user_data_dir = r"C:\Users\wangz\AppData\Local\Google\Chrome\User Data" # <-- 把 '你的用户名' 换成你的实际 Windows 用户名
profile_directory = "Default"  # 或者 "Profile 1", "Profile 2" 等，取决于 chrome://version 显示的

target_class = 'product__message-title_area' # 你要查找的 class 名称
html_content = None # 用来存储提取出来的 HTML 文本
# -----------
excel_file_name = 'coles_data.xlsx'
product_data = []

chrome_options = webdriver.ChromeOptions()

chrome_options.add_argument(f"user-data-dir={user_data_dir}")
chrome_options.add_argument(f"profile-directory={profile_directory}")

chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument("--disable-extensions") # 注意：这个选项可能会阻止加载你本地配置中的扩展，如果需要扩展运行，可以注释掉这行
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = None # 初始化 driver 变量
try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.set_window_size(1920, 1080)
    main_page_url = "https://www.coles.com.au"
    driver.get(main_page_url)
    time.sleep(5)

    pageNumber = 2
    special_url = f'https://www.coles.com.au/on-special?filter_Special=halfprice&page={pageNumber}'
    driver.get(special_url)
    time.sleep(5)
    result = driver.execute_cdp_cmd('Page.captureSnapshot', {'format': 'mhtml'})
    msg = email.message_from_string(result['data'])
    for part in msg.walk():
        content_type = part.get_content_type()
        if content_type == 'text/html':
            payload_bytes = part.get_payload(decode=True)
            charset = part.get_content_charset() or 'utf-8'
            try:
                html_content = payload_bytes.decode(charset)
                print(f"成功提取并解码 HTML 内容 (使用编码: {charset})。")
                break # 找到主要的 HTML 部分就停止
            except UnicodeDecodeError:
                print(f"警告：使用声明的编码 '{charset}' 解码失败，尝试使用 'utf-8' 作为备用...")
                try:
                    html_content = payload_bytes.decode('utf-8')
                    break
                except Exception as decode_err:
                    html_content = None # 重置以防部分解码
                    continue # 继续查找下一个部分

    if html_content:
        print(f"\n正在使用 BeautifulSoup 解析提取的 HTML...")
        soup = BeautifulSoup(html_content, 'html.parser')

        print(f"查找所有 class 为 '{target_class}' 的 div 元素...")
        # 5. 查找所有符合条件的 div 元素
        elements = soup.find_all('div', class_=target_class)

        # 6. 打印找到的元素内容
        if elements:
            print(f"找到了 {len(elements)} 个匹配的元素：")
            for i, element in enumerate(elements):
                product_info = {
                    '产品名称': "N/A",
                    '原价': "N/A",
                    '现价': "N/A",
                    '单位价格': "N/A"
                }
                product_info['产品名称'] = element.find("h2", class_="product__title").contents[0]
                product_info['原价'] = element.find("span", class_="price__was").contents[0].replace(" | Was ", "")
                product_info['现价'] = element.find("span", class_="price__value").contents[0]
                product_info['单位价格'] = element.find("div", class_="price__calculation_method").contents[0]
                product_data.append(product_info)
        else:
            print(f"在 HTML 内容中未找到任何 class 为 '{target_class}' 的 div 元素。")
    else:
        print("错误：未能在 MHTML 文件中找到有效的 HTML 内容部分。")
except Exception as e:
    print(f"在处理页面或保存 MHTML 时出错: {e}")
    # import traceback; traceback.print_exc() # 取消注释查看详细错误栈

finally:
    if driver:
        print("正在关闭 WebDriver...")
        driver.quit()
        print("WebDriver 已关闭。")
    else:
        print("WebDriver 未成功初始化，无需关闭。")

if product_data:
    print(f"\n正在将提取的 {len(product_data)} 条产品数据保存到 Excel 文件: {excel_file_name}")
    try:
        # 将字典列表转换为 pandas DataFrame
        df = pd.DataFrame(product_data)
        # 可以指定列的顺序
        df = df[['产品名称', '现价', '原价', '单位价格']]
        # 将 DataFrame 写入 Excel 文件，不包含索引列
        df.to_excel(excel_file_name, index=False, engine='openpyxl')
        print(f"Excel 文件 '{excel_file_name}' 保存成功。")
    except ImportError:
            print("错误: 需要安装 'pandas' 和 'openpyxl' 库来保存 Excel 文件。请运行: pip install pandas openpyxl")
    except Exception as ex:
            print(f"保存 Excel 文件时出错: {ex}")
else:
    print("没有提取到任何产品数据，未创建 Excel 文件。")