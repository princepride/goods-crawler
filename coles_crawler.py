import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import email
from bs4 import BeautifulSoup
import pandas as pd

user_data_dir = r"~/Library/Application Support/Google/Chrome/"
profile_directory = "Default"

target_class = 'product__message-title_area'
product_data = []
excel_file_name = 'coles_data.xlsx'

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f"user-data-dir={user_data_dir}")
chrome_options.add_argument(f"profile-directory={profile_directory}")
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument("--disable-extensions")
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = None
try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.set_window_size(1920, 1080)
    main_page_url = "https://www.coles.com.au"
    driver.get(main_page_url)
    time.sleep(60)

    special_url_base = 'https://www.coles.com.au/on-special?filter_Special=halfprice&page='
    current_page = 1
    total_pages = 100

    while current_page <= total_pages:
        special_url = f'{special_url_base}{current_page}'
        driver.get(special_url)
        time.sleep(5)
        result = driver.execute_cdp_cmd('Page.captureSnapshot', {'format': 'mhtml'})
        msg = email.message_from_string(result['data'])
        html_content = None
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/html':
                payload_bytes = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                try:
                    html_content = payload_bytes.decode(charset)
                    print(f"成功提取并解码第 {current_page} 页的 HTML 内容 (使用编码: {charset})。")
                    break
                except UnicodeDecodeError:
                    print(f"警告：使用声明的编码 '{charset}' 解码第 {current_page} 页失败，尝试使用 'utf-8' 作为备用...")
                    try:
                        html_content = payload_bytes.decode('utf-8')
                        print(f"成功使用 'utf-8' 备用编码解码第 {current_page} 页。")
                        break
                    except Exception as decode_err:
                        print(f"使用备用编码解码第 {current_page} 页也失败: {decode_err}")
                        html_content = None
                        continue
                except Exception as decode_err:
                    print(f"解码第 {current_page} 页时发生其他错误: {decode_err}")
                    html_content = None
                    continue

        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')

            elements = soup.find_all('div', class_=target_class)
            pricing_elements = soup.find_all('section', class_='product__pricing')
            print(pricing_elements)
            if elements:
                print(f"在第 {current_page} 页找到了 {len(elements)} 个匹配的元素：")
                for element, price_element in zip(elements, pricing_elements):
                    product_info = {
                        '产品名称': "N/A",
                        '原价': "N/A",
                        '现价': "N/A",
                        '单位价格': "N/A"
                    }
                    href = element.find("a")['href']
                    title_href = element.find("a")['href'].split("/")[-1]
                    title_href_list = title_href.split("-")
                    code = title_href_list[-1]
                    title_element = " ".join(title_href_list[:-1])
                    was_price_element = price_element.find("span", class_="price__was")
                    now_price_element = price_element.find("span", class_="price__value")
                    unit_price_element = price_element.find("div", class_="price__calculation_method")

                    if href:
                        product_info['产品链接'] = href
                    if code:
                        product_info['产品代码'] = code
                    if title_element:
                        product_info['产品名称'] = title_element
                    if was_price_element and was_price_element.contents:
                        product_info['原价'] = was_price_element.contents[0].replace(" | Was ", "")
                    if now_price_element and now_price_element.contents:
                        product_info['现价'] = now_price_element.contents[0]
                    if unit_price_element and unit_price_element.contents:
                        product_info['单位价格'] = unit_price_element.contents[0]

                    product_data.append(product_info)
            else:
                print(f"在第 {current_page} 页的 HTML 内容中未找到任何 class 为 '{target_class}' 的 div 元素。")
                break
        else:
            print(f"错误：未能在第 {current_page} 页的 MHTML 文件中找到有效的 HTML 内容部分。")

        current_page += 1

except Exception as e:
    print(f"在处理页面或保存 MHTML 时出错: {e}")

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
        df = pd.DataFrame(product_data)
        df = df[['产品代码', '产品名称', '产品链接', '原价', '现价', '单位价格']]
        df.to_excel(excel_file_name, index=False, engine='openpyxl')
        print(f"Excel 文件 '{excel_file_name}' 保存成功。")
    except ImportError:
        print("错误: 需要安装 'pandas' 和 'openpyxl' 库来保存 Excel 文件。请运行: pip install pandas openpyxl")
    except Exception as ex:
        print(f"保存 Excel 文件时出错: {ex}")
else:
    print("没有提取到任何产品数据，未创建 Excel 文件。")