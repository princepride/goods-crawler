import os
import re
import requests
from lxml import html
import pypandoc
from urllib.parse import urljoin
import concurrent.futures
from tqdm import tqdm

# --- 配置 ---

# !!! 关键：并行数量配置 !!!
# 设置同时执行任务的最大线程数。建议范围 5-16。
# 设置过高可能会导致IP被封锁或程序出错。
MAX_WORKERS = 50

START_URL = "https://sbr-pet.apra.gov.au/ARF/ARF.html"
OUTPUT_DIR = "ARF_Word_Documents"
XPATH_LEVEL_1 = "/html/body/div/div[2]/div/table/tbody/tr/td[3]/div/a"
XPATH_LEVEL_2 = "//a[starts-with(@href, 'attributes/')]"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def sanitize_filename(filename):
    """移除文件名中的非法字符。"""
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def fetch_html(url, headers):
    """封装的HTML下载函数，返回文本内容或None。"""
    try:
        response = requests.get(url, headers=headers, timeout=45)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.text
    except requests.exceptions.RequestException:
        # 在工作线程中，错误信息通过返回值传递
        return None

def process_primary_link(link_info):
    """
    处理单个主报告链接的完整流程（下载、解析、合并、转换）。
    这个函数将在独立的线程中被执行。
    """
    # 从传入的字典中解析信息
    index = link_info['index']
    total = link_info['total']
    link_text = link_info['text']
    relative_url = link_info['href']

    # --- 文件名和URL处理 ---
    primary_full_url = urljoin(START_URL, relative_url)
    url_filename = os.path.basename(relative_url)
    unique_part = os.path.splitext(url_filename)[0]
    filename_base = sanitize_filename(f"{link_text} ({unique_part})")
    output_filepath = os.path.join(OUTPUT_DIR, f"{filename_base}.docx")
    
    # 构造日志前缀，方便追踪
    log_prefix = f"[Worker {index+1}/{total}] {filename_base}"

    if os.path.exists(output_filepath):
        return f"{log_prefix}: 已跳过，文件已存在。"

    html_parts_for_word = []

    # --- 内容抓取与合并 ---
    primary_page_html = fetch_html(primary_full_url, HEADERS)
    if not primary_page_html:
        return f"{log_prefix}: 失败，无法下载主报告页面。"

    html_parts_for_word.append(f"<h1>主报告: {link_text}</h1>")
    html_parts_for_word.append(f"<p><em>来源URL: {primary_full_url}</em></p><hr>")
    html_parts_for_word.append(primary_page_html)

    tree_level_2 = html.fromstring(primary_page_html)
    sub_links = tree_level_2.xpath(XPATH_LEVEL_2)

    for sub_link_element in sub_links:
        sub_relative_url = sub_link_element.get('href', '').replace('\\', '/')
        if not sub_relative_url:
            continue
        sub_full_url = urljoin(primary_full_url, sub_relative_url)
        sub_link_text = sub_link_element.text_content().strip()
        sub_page_html = fetch_html(sub_full_url, HEADERS)
        if sub_page_html:
            html_parts_for_word.append(f"<hr><h2>子页面: {sub_link_text}</h2>")
            html_parts_for_word.append(f"<p><em>来源URL: {sub_full_url}</em></p><hr>")
            html_parts_for_word.append(sub_page_html)

    # --- 合并与转换 ---
    combined_html = "".join(html_parts_for_word)
    try:
        pypandoc.convert_text(
            source=combined_html, to='docx', format='html',
            outputfile=output_filepath, extra_args=['--standalone', '--quiet']
        )
        return f"{log_prefix}: 成功保存。"
    except Exception as e:
        # 检查是否是Pandoc未找到的致命错误
        if "pandoc" in str(e).lower() and "not found" in str(e).lower():
            # 这是一个应该停止所有任务的致命错误
            raise e
        return f"{log_prefix}: 转换失败 - {e}"

def main():
    """主执行函数"""
    print(f"脚本开始执行 (V5 - 并行版，最大并发数: {MAX_WORKERS})...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"正在访问主索引页面: {START_URL}")
    index_page_html = fetch_html(START_URL, HEADERS)
    if not index_page_html:
        print("错误：无法获取主索引页，脚本终止。")
        return

    tree_level_1 = html.fromstring(index_page_html)
    primary_links = tree_level_1.xpath(XPATH_LEVEL_1)
    if not primary_links:
        print("警告：在主索引页上没有找到任何匹配XPath的链接。")
        return

    # 将所有任务信息准备好，存入一个列表
    tasks = []
    total_links = len(primary_links)
    for i, link_element in enumerate(primary_links):
        tasks.append({
            "index": i,
            "total": total_links,
            "text": link_element.text_content().strip(),
            "href": link_element.get('href', '').replace('\\', '/'),
        })

    print(f"成功找到 {total_links} 个主报告链接。开始并行处理...")

    # 使用线程池和tqdm进度条来执行所有任务
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 使用tqdm来包装，自动处理进度条
        # executor.map会保持任务的原始顺序
        results = list(tqdm(executor.map(process_primary_link, tasks), total=total_links, desc="处理报告中"))
    
    print("-" * 40)
    print("所有任务处理完毕。以下是执行摘要：")
    # 打印出所有非None的结果（通常是错误或跳过信息）
    for res in results:
        if res:
            print(res)
    print("脚本执行完毕！")

if __name__ == "__main__":
    main()