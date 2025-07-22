import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import base64
import email
import quopri
from bs4 import BeautifulSoup
import os
import pandas as pd # <<<--- 导入 pandas

# --- Selenium 设置 ---
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument("--disable-extensions")
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

base_url = 'https://www.woolworths.com.au/shop/browse/specials/half-price?pageNumber='
output_excel_filename = 'woolworths_data.xlsx' # <<<--- 修改输出文件名后缀

driver = None
all_product_data = []
total_pages = 1

# --- MHTML 解析函数 (保持不变) ---
def extract_html_from_mhtml_string(mhtml_data_string):
    try:
        msg = email.message_from_string(mhtml_data_string)
        html_content = None
        charset = 'utf-8'
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/html':
                transfer_encoding = part.get('Content-Transfer-Encoding', '').lower()
                part_charset = part.get_content_charset()
                if part_charset:
                    charset = part_charset
                payload = part.get_payload(decode=False)
                payload_bytes = None
                if isinstance(payload, bytes): payload_bytes = payload
                elif isinstance(payload, str):
                    if transfer_encoding == 'base64':
                        try:
                            payload_clean = "".join(payload.split())
                            payload_bytes = base64.b64decode(payload_clean)
                        except base64.binascii.Error: continue
                    elif transfer_encoding == 'quoted-printable':
                        try: payload_bytes = quopri.decodestring(payload.encode('ascii', errors='ignore'))
                        except Exception:
                            try: payload_bytes = payload.encode(charset, errors='ignore')
                            except Exception: continue
                    elif transfer_encoding in ('8bit', '7bit', 'binary', ''):
                       try: payload_bytes = payload.encode(charset, errors='ignore')
                       except Exception: continue
                    else:
                       try: payload_bytes = payload.encode(charset, errors='ignore')
                       except Exception: continue
                else: continue
                if payload_bytes is not None:
                    try:
                        html_content = payload_bytes.decode(charset, errors='replace')
                        break
                    except Exception: html_content = None
        return html_content
    except Exception as e:
        print(f"处理 MHTML 字符串时发生错误: {e}")
        return None

# --- Selenium 操作 (保持不变) ---
try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.set_window_size(1920, 1080)

    print("正在访问第一页以获取总页数...")
    first_page_url = f"{base_url}1"
    driver.get(first_page_url)
    time.sleep(5)
    try:
        mhtml_content_page1 = driver.execute_cdp_cmd('Page.captureSnapshot', {'format': 'mhtml'})['data']
        html_page1 = extract_html_from_mhtml_string(mhtml_content_page1)
        if html_page1:
            soup_page1 = BeautifulSoup(html_page1, 'html.parser')
            try:
                page_links = soup_page1.find_all('a', class_='paging-pageNumber')
                if page_links:
                    total_pages = int(page_links[-1].contents[-1].strip())
                    print(f"获取到总页数: {total_pages}")
                else:
                    print("未找到分页链接，将只处理第一页。")
                    total_pages = 1
            except (IndexError, ValueError, TypeError, AttributeError) as e:
                print(f"解析总页数时出错: {e}，将只处理第一页。")
                total_pages = 1
        else:
            print("未能解析第一页的 HTML，无法获取总页数，将只处理第一页。")
            total_pages = 1
    except Exception as e:
        print(f"访问第一页或获取总页数时发生 Selenium 错误: {e}")
        total_pages = 1

    if total_pages >= 1:
        for current_page_num in range(1, total_pages + 1):
            print(f"正在处理第 {current_page_num} 页 / 共 {total_pages} 页...")
            current_page_url = f"{base_url}{current_page_num}"
            driver.get(current_page_url)
            time.sleep(5)

            try:
                mhtml_content_page = driver.execute_cdp_cmd('Page.captureSnapshot', {'format': 'mhtml'})['data']
                extracted_html = extract_html_from_mhtml_string(mhtml_content_page)

                if extracted_html:
                    soup = BeautifulSoup(extracted_html, 'html.parser')
                    product_tiles = soup.find_all('div', class_='product-tile-content')

                    if product_tiles:
                        for tile in product_tiles:
                            original_price = "N/A"
                            current_price = "N/A"
                            price_per_unit = "N/A"
                            product_name = "N/A"
                            try: original_price = tile.find('span', class_='was-price').contents[1].strip()
                            except Exception: pass
                            try: current_price = tile.find('div', class_='primary').contents[1].strip()
                            except Exception: pass
                            try: price_per_unit = tile.find('span', class_='price-per-cup').contents[1].strip()
                            except Exception: pass
                            try: product_name = tile.find('div', class_='title').find('a').contents[1].strip()
                            except Exception: pass
                            try: product_href = tile.find('div', class_='title').find('a')['href']
                            except Exception: pass

                            # 只添加包含有效原价的条目（根据你之前的逻辑）
                            if current_price != "N/A" or original_price != "N/A":
                                all_product_data.append([product_name, product_href, original_price, current_price, price_per_unit])

            except Exception as page_e:
                 print(f"处理第 {current_page_num} 页时出错: {page_e}")

except Exception as e:
    print(f"Selenium 运行出错: {e}")
finally:
    if driver:
        driver.quit()

# --- 步骤 3: 将所有数据写入 Excel 文件 ---
if all_product_data:
    print(f"\n所有页面处理完毕，共找到 {len(all_product_data)} 条有效产品数据，正在写入 Excel 文件...")
    try:
        # 定义列名
        header = ['产品名称', '产品链接', '原价', '现价', '单位价格']
        # 创建 pandas DataFrame
        df = pd.DataFrame(all_product_data, columns=header)
        # 写入 Excel 文件，不包含索引列
        df.to_excel(output_excel_filename, index=False, engine='openpyxl')
        print(f"数据已成功写入 '{output_excel_filename}'")
    except ImportError:
         print("错误：需要安装 'pandas' 和 'openpyxl' 库才能写入 Excel 文件。")
         print("请运行: pip install pandas openpyxl")
    except Exception as e:
         print(f"写入 Excel 文件时发生错误: {e}")
else:
    print("未能收集到任何有效产品数据，Excel 文件未生成。")