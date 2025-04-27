import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import base64 # 需要导入 base64 库来解码 MHTML 数据

# --- Selenium 配置 ---
chrome_options = webdriver.ChromeOptions()
# 添加一些反检测选项 (你已经有了)
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument("--disable-extensions")
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
# (可选) 启用无头模式，如果不需要看到浏览器窗口
# chrome_options.add_argument('--headless')
# chrome_options.add_argument('--disable-gpu') # 在无头模式下有时需要

pageNumber = 2
url = f'https://www.woolworths.com.au/shop/browse/specials/half-price?pageNumber={pageNumber}'

# --- 初始化 WebDriver ---
print("正在初始化 WebDriver...")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
# (可选) 设置窗口大小，有时影响页面布局
driver.set_window_size(1920, 1080)
print(f"正在访问 URL: {url}")
driver.get(url)

try:
    # --- 等待页面加载 ---
    # 使用更智能的等待代替固定的 time.sleep() 会更好，但这里暂时保留你的 sleep
    # 例如，等待某个关键容器元素出现
    # wait = WebDriverWait(driver, 30) # 等待最多30秒
    # wait.until(EC.presence_of_element_located((By.TAG_NAME, 'main'))) # 等待 <main> 标签出现
    print("等待页面加载 (15秒)...")
    time.sleep(15) # 增加等待时间，确保 JS 有足够时间渲染

    # --- 修改点：使用 CDP 保存为 MHTML ---
    print("尝试通过 CDP 命令将页面保存为 MHTML...")
    # 执行 Chrome DevTools Protocol 命令 'Page.captureSnapshot'
    # 需要 Chrome 浏览器支持此命令 (较新版本通常都支持)
    # 'format': 'mhtml' 指定了输出格式
    result = driver.execute_cdp_cmd('Page.captureSnapshot', {'format': 'mhtml'})

    # CDP 命令返回的数据在 'data' 键中，是 MHTML 内容
    mhtml_content = result['data']

    # 指定 MHTML 保存的文件名
    mhtml_file_path = f'complete_page_{pageNumber}.mhtml'

    # 将 MHTML 内容写入文件
    # 注意：直接写入字符串，不需要解码 base64，CDP 返回的就是 MHTML 文本
    with open(mhtml_file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(mhtml_content)

    print(f'页面已尝试保存为 MHTML 文件: {mhtml_file_path}')
    print("你可以尝试用 Chrome 或 Edge 浏览器打开这个 .mhtml 文件查看效果。")

    # --- 原有的 page_source 方法 (现在可以注释掉或删除) ---
    # html_content = driver.page_source
    # file_path = f'light_dom_page_{pageNumber}.html'
    # with open(file_path, 'w', encoding='utf-8') as f:
    #     f.write(html_content)
    # print(f'仅 Light DOM 的网页内容已保存到文件: {file_path}')
    # --- ---

except Exception as e:
    print(f"在处理页面或保存 MHTML 时出错: {e}")

finally:
    print("正在关闭 WebDriver...")
    driver.quit()
    print("WebDriver 已关闭。")