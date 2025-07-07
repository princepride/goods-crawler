import os
import re
import requests
from lxml import html
import pypandoc
from urllib.parse import urljoin

# --- 配置 ---
START_URL = "https://sbr-pet.apra.gov.au/ARF/ARF.html"
OUTPUT_DIR = "ARF_Word_Documents"
XPATH_SELECTOR = "/html/body/div/div[2]/div/table/tbody/tr/td[3]/div/a"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def sanitize_filename(filename):
    """
    移除文件名中的非法字符，避免创建文件时出错。
    """
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def main():
    """
    主执行函数
    """
    print("脚本开始执行...")

    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(f"输出文件夹 '{OUTPUT_DIR}' 已准备就绪。")
    except OSError as e:
        print(f"错误：无法创建文件夹 '{OUTPUT_DIR}': {e}")
        return

    try:
        print(f"正在访问主页面: {START_URL}")
        response = requests.get(START_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"错误：无法访问主页面 {START_URL}。请检查网络连接或 URL 是否正确。")
        print(f"详细信息: {e}")
        return

    tree = html.fromstring(response.content)
    target_links = tree.xpath(XPATH_SELECTOR)

    if not target_links:
        print(f"警告：在页面上没有找到任何匹配 XPath '{XPATH_SELECTOR}' 的链接。")
        return

    print(f"成功找到 {len(target_links)} 个目标链接。开始逐个处理...")
    print("-" * 30)

    for i, link_element in enumerate(target_links, 1):
        link_text = link_element.text_content().strip()
        relative_url = link_element.get('href')

        if not relative_url:
            print(f"({i}/{len(target_links)}) 跳过：链接 '{link_text}' 没有 href 属性。")
            continue
        
        relative_url = relative_url.replace('\\', '/')
        full_url = urljoin(START_URL, relative_url)
        
        # ======================================================================
        # <--- 关键修正：创建唯一的文件名
        # 1. 从URL中提取文件名部分 (例如 "ARF_112_2A-D2A2.html")
        url_filename = os.path.basename(relative_url)
        # 2. 去掉其扩展名 (例如 ".html")
        unique_part = os.path.splitext(url_filename)[0]
        # 3. 将链接文本和唯一部分组合起来
        new_filename_base = f"{link_text} ({unique_part})"
        # 4. 清洗最终的文件名以备保存
        filename = sanitize_filename(new_filename_base)
        # ======================================================================

        output_filepath = os.path.join(OUTPUT_DIR, f"{filename}.docx")
        
        print(f"({i}/{len(target_links)}) 正在处理: {link_text}")
        print(f"  -> 生成文件名: {filename}.docx")


        if os.path.exists(output_filepath):
            print(f"  -> 已跳过：文件已存在。")
            continue

        try:
            print(f"  -> 正在下载: {full_url}")
            sub_page_response = requests.get(full_url, headers=HEADERS, timeout=30)
            sub_page_response.raise_for_status()
            sub_page_response.encoding = 'utf-8'
            html_content = sub_page_response.text

            print(f"  -> 正在转换为 Word 文档...")
            pypandoc.convert_text(
                source=html_content,
                to='docx',
                format='html',
                outputfile=output_filepath,
                extra_args=['--standalone']
            )
            print(f"  -> 成功保存到: {output_filepath}")

        except requests.exceptions.RequestException as e:
            print(f"  -> 错误：下载 '{full_url}' 失败: {e}")
        except Exception as e:
            print(f"  -> 错误：转换或保存文件失败: {e}")
            if "pandoc" in str(e).lower() and "not found" in str(e).lower():
                print("  -> 致命错误：找不到 Pandoc！请确认你已正确安装 Pandoc。")
                break
        
        print("-" * 30)

    print("脚本执行完毕！")

if __name__ == "__main__":
    main()