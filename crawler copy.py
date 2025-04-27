# 导入 requests 库，它用于发送 HTTP 请求
import requests

# --- 配置区 ---

# 1. 设置你要爬取的网页 URL
# 请将下面的 'YOUR_TARGET_URL_HERE' 替换成你实际想要爬取的网址
target_url = 'https://www.coles.com.au/on-special?filter_Special=halfprice&page=1&pid=homepage_herotile_halfprice'

# 2. 设置浏览器头部信息 (Headers)
#    User-Agent 是必须的，它告诉服务器你是什么类型的浏览器。
#    很多网站会检查这个字段，如果没有或者值很奇怪，可能会拒绝访问。
#    你可以根据需要添加更多头部字段，比如 'Accept-Language', 'Referer' 等。
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    # 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    # 'Connection': 'keep-alive',
    # 'Referer': 'https://www.google.com/' # 有些网站会检查来源页
}

# 3. 设置请求超时时间（可选，单位：秒）
#    防止请求卡死太久
timeout_seconds = 15

# --- 脚本执行区 ---

print(f"准备爬取网页: {target_url}")

try:
    # 使用 requests.get 方法发送 GET 请求
    # - 第一个参数是目标 URL
    # - headers 参数传入我们定义的头部信息字典
    # - timeout 参数设置超时时间
    response = requests.get(target_url, headers=headers, timeout=timeout_seconds)

    # 检查 HTTP 响应状态码
    # response.raise_for_status() 会在状态码不是 2xx (例如 404 Not Found, 500 Internal Server Error) 时抛出异常
    response.raise_for_status()
    print(f"请求成功，状态码: {response.status_code}")

    # --- 处理响应内容 ---

    # 尝试自动检测并设置正确的文本编码，防止中文等字符乱码
    # response.apparent_encoding 会根据内容猜测编码
    response.encoding = response.apparent_encoding
    print(f"网页编码识别为: {response.encoding}")

    # 获取网页的 HTML 源代码文本
    html_content = response.text

    # --- 输出或保存结果 ---

    # 打印获取到的网页内容 (如果内容很多，可能会刷屏)
    print("\n--- 网页 HTML 内容开始 ---")
    print(html_content)
    print("--- 网页 HTML 内容结束 ---\n")

    # (可选) 将内容保存到本地文件
    # file_name = 'scraped_page.html'
    # try:
    #     with open(file_name, 'w', encoding='utf-8') as f:
    #         f.write(html_content)
    #     print(f"网页内容已成功保存到文件: {file_name}")
    # except IOError as e:
    #     print(f"保存文件时出错: {e}")


except requests.exceptions.Timeout as e:
    # 处理请求超时错误
    print(f"请求超时 ({timeout_seconds}秒): {e}")
except requests.exceptions.HTTPError as e:
    # 处理 HTTP 错误 (例如 404, 500 等)
    print(f"HTTP 错误: {e}")
except requests.exceptions.ConnectionError as e:
    # 处理连接错误 (例如 DNS 查询失败、拒绝连接等)
    print(f"网络连接错误: {e}")
except requests.exceptions.RequestException as e:
    # 处理其他 requests 库相关的异常
    print(f"请求过程中发生错误: {e}")
except Exception as e:
    # 捕获其他所有未知错误
    print(f"发生未知错误: {e}")