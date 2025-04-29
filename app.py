import gradio as gr
import subprocess
import pandas as pd
import os
import sys # 用于获取当前 Python 解释器路径
import time

# --- 配置 ---
COLES_SCRIPT_NAME = 'coles_crawler.py'
WOOLIES_SCRIPT_NAME = 'woolworths_crawler.py'
COLES_EXCEL_FILE = 'coles_data.xlsx'
WOOLIES_EXCEL_FILE = 'woolworths_data.xlsx'

# --- 核心功能：运行脚本、读取 Excel 并返回文件路径 ---
def run_scrapers_and_get_data():
    """
    依次运行 Coles 和 Woolworths 的爬虫脚本，
    然后尝试读取生成的 Excel 文件并返回 Pandas DataFrames 以及文件路径。
    """
    coles_df = pd.DataFrame() # 初始化为空 DataFrame
    woolies_df = pd.DataFrame() # 初始化为空 DataFrame
    run_status = [] # 用于记录运行状态
    coles_filepath = None # 初始化文件路径为 None
    woolies_filepath = None # 初始化文件路径为 None

    # --- 运行 Coles 爬虫 ---
    run_status.append(f"[{time.strftime('%H:%M:%S')}] 开始运行 {COLES_SCRIPT_NAME}...")
    print(f"开始运行 {COLES_SCRIPT_NAME}...")
    try:
        result_coles = subprocess.run(
            [sys.executable, COLES_SCRIPT_NAME],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=600
        )
        print(f"--- {COLES_SCRIPT_NAME} 标准输出 ---")
        print(result_coles.stdout)
        print(f"--- {COLES_SCRIPT_NAME} 标准错误 ---")
        print(result_coles.stderr)
        print(f"--- {COLES_SCRIPT_NAME} 结束 ---")
        run_status.append(f"[{time.strftime('%H:%M:%S')}] {COLES_SCRIPT_NAME} 运行成功。")

        # 检查 Coles Excel 文件是否存在
        if os.path.exists(COLES_EXCEL_FILE):
            coles_filepath = COLES_EXCEL_FILE # 设置文件路径供下载
            try:
                coles_df = pd.read_excel(COLES_EXCEL_FILE)
                run_status.append(f"[{time.strftime('%H:%M:%S')}] 成功加载 {COLES_EXCEL_FILE}。")
                print(f"成功加载 {COLES_EXCEL_FILE}。")
            except Exception as e:
                error_msg = f"[{time.strftime('%H:%M:%S')}] 加载 {COLES_EXCEL_FILE} 出错: {e}"
                run_status.append(error_msg)
                print(error_msg)
                coles_df = pd.DataFrame({"错误": [f"无法加载 {COLES_EXCEL_FILE}: {e}"]})
                # 文件存在但无法读取，仍然提供下载路径让用户自行检查
        else:
            run_status.append(f"[{time.strftime('%H:%M:%S')}] 未找到 {COLES_EXCEL_FILE} 文件。脚本可能未生成数据或提前结束。")
            print(f"未找到 {COLES_EXCEL_FILE} 文件。")
            coles_df = pd.DataFrame({"信息": [f"{COLES_SCRIPT_NAME} 运行完成但未生成 {COLES_EXCEL_FILE}"]})

    except subprocess.CalledProcessError as e:
        error_msg = f"[{time.strftime('%H:%M:%S')}] 运行 {COLES_SCRIPT_NAME} 失败 (返回码 {e.returncode})。\n标准输出:\n{e.stdout}\n标准错误:\n{e.stderr}"
        run_status.append(error_msg)
        print(error_msg)
        coles_df = pd.DataFrame({"错误": [f"运行 {COLES_SCRIPT_NAME} 失败: {e.stderr[:500]}..."]})
    except subprocess.TimeoutExpired as e:
        error_msg = f"[{time.strftime('%H:%M:%S')}] 运行 {COLES_SCRIPT_NAME} 超时。\n标准输出:\n{e.stdout}\n标准错误:\n{e.stderr}"
        run_status.append(error_msg)
        print(error_msg)
        coles_df = pd.DataFrame({"错误": [f"运行 {COLES_SCRIPT_NAME} 超时"]})
    except Exception as e:
        error_msg = f"[{time.strftime('%H:%M:%S')}] 运行 {COLES_SCRIPT_NAME} 时发生未知错误: {e}"
        run_status.append(error_msg)
        print(error_msg)
        coles_df = pd.DataFrame({"错误": [f"运行 {COLES_SCRIPT_NAME} 时发生未知错误: {e}"]})

    # --- 运行 Woolworths 爬虫 ---
    run_status.append(f"\n[{time.strftime('%H:%M:%S')}] 开始运行 {WOOLIES_SCRIPT_NAME}...")
    print(f"开始运行 {WOOLIES_SCRIPT_NAME}...")
    try:
        result_woolies = subprocess.run(
            [sys.executable, WOOLIES_SCRIPT_NAME],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=600
        )
        print(f"--- {WOOLIES_SCRIPT_NAME} 标准输出 ---")
        print(result_woolies.stdout)
        print(f"--- {WOOLIES_SCRIPT_NAME} 标准错误 ---")
        print(result_woolies.stderr)
        print(f"--- {WOOLIES_SCRIPT_NAME} 结束 ---")
        run_status.append(f"[{time.strftime('%H:%M:%S')}] {WOOLIES_SCRIPT_NAME} 运行成功。")

        # 检查 Woolworths Excel 文件是否存在
        if os.path.exists(WOOLIES_EXCEL_FILE):
            woolies_filepath = WOOLIES_EXCEL_FILE # 设置文件路径供下载
            try:
                woolies_df = pd.read_excel(WOOLIES_EXCEL_FILE)
                run_status.append(f"[{time.strftime('%H:%M:%S')}] 成功加载 {WOOLIES_EXCEL_FILE}。")
                print(f"成功加载 {WOOLIES_EXCEL_FILE}。")
            except Exception as e:
                error_msg = f"[{time.strftime('%H:%M:%S')}] 加载 {WOOLIES_EXCEL_FILE} 出错: {e}"
                run_status.append(error_msg)
                print(error_msg)
                woolies_df = pd.DataFrame({"错误": [f"无法加载 {WOOLIES_EXCEL_FILE}: {e}"]})
                # 文件存在但无法读取，仍然提供下载路径
        else:
            run_status.append(f"[{time.strftime('%H:%M:%S')}] 未找到 {WOOLIES_EXCEL_FILE} 文件。脚本可能未生成数据或提前结束。")
            print(f"未找到 {WOOLIES_EXCEL_FILE} 文件。")
            woolies_df = pd.DataFrame({"信息": [f"{WOOLIES_SCRIPT_NAME} 运行完成但未生成 {WOOLIES_EXCEL_FILE}"]})

    except subprocess.CalledProcessError as e:
        error_msg = f"[{time.strftime('%H:%M:%S')}] 运行 {WOOLIES_SCRIPT_NAME} 失败 (返回码 {e.returncode})。\n标准输出:\n{e.stdout}\n标准错误:\n{e.stderr}"
        run_status.append(error_msg)
        print(error_msg)
        woolies_df = pd.DataFrame({"错误": [f"运行 {WOOLIES_SCRIPT_NAME} 失败: {e.stderr[:500]}..."]})
    except subprocess.TimeoutExpired as e:
        error_msg = f"[{time.strftime('%H:%M:%S')}] 运行 {WOOLIES_SCRIPT_NAME} 超时。\n标准输出:\n{e.stdout}\n标准错误:\n{e.stderr}"
        run_status.append(error_msg)
        print(error_msg)
        woolies_df = pd.DataFrame({"错误": [f"运行 {WOOLIES_SCRIPT_NAME} 超时"]})
    except Exception as e:
        error_msg = f"[{time.strftime('%H:%M:%S')}] 运行 {WOOLIES_SCRIPT_NAME} 时发生未知错误: {e}"
        run_status.append(error_msg)
        print(error_msg)
        woolies_df = pd.DataFrame({"错误": [f"运行 {WOOLIES_SCRIPT_NAME} 时发生未知错误: {e}"]})

    run_status.append(f"\n[{time.strftime('%H:%M:%S')}] 所有脚本执行完毕。")
    print("所有脚本执行完毕。")

    # 返回状态文本、两个 DataFrame 和两个文件路径
    return "\n".join(run_status), coles_df, woolies_df, coles_filepath, woolies_filepath

# --- 创建 Gradio 界面 ---
with gr.Blocks() as demo:
    gr.Markdown("# Coles & Woolworths 半价商品爬虫")
    gr.Markdown("点击下面的按钮运行爬虫脚本。脚本需要 **几分钟** 时间执行（取决于网络速度和网站结构），请耐心等待。")
    gr.Markdown("**注意:** 爬虫脚本依赖于特定的网站结构，如果 Coles 或 Woolworths 网站更新，脚本可能会失效。")
    gr.Markdown("**重要提示:** Coles 爬虫脚本 (`coles_crawler.py`) 中可能硬编码了 Chrome 用户配置路径。如果遇到权限或路径错误，请检查并修改 `coles_crawler.py` 中的 `user_data_dir` 变量。") # 稍微修改提示

    run_button = gr.Button("🚀 运行爬虫并显示结果")

    with gr.Row():
        status_output = gr.Textbox(label="运行日志", lines=10, interactive=False, scale=2) # 增加 scale 使日志框更宽

    with gr.Row():
        with gr.Column():
            gr.Markdown("## Coles 半价商品")
            coles_output_df = gr.DataFrame(label="Coles Data")
            # 添加 Coles 下载文件组件
            coles_download = gr.File(label=f"下载 {COLES_EXCEL_FILE}", interactive=False)
        with gr.Column():
            gr.Markdown("## Woolworths 半价商品")
            woolies_output_df = gr.DataFrame(label="Woolworths Data")
            # 添加 Woolworths 下载文件组件
            woolies_download = gr.File(label=f"下载 {WOOLIES_EXCEL_FILE}", interactive=False)

    # 当按钮被点击时，执行 run_scrapers_and_get_data 函数
    # 输出会更新到 status_output, coles_output_df, woolies_output_df, coles_download, woolies_download
    run_button.click(
        fn=run_scrapers_and_get_data,
        inputs=None, # 没有输入
        outputs=[status_output, coles_output_df, woolies_output_df, coles_download, woolies_download] # 增加两个文件输出
    )

# --- 启动 Gradio 应用 ---
if __name__ == "__main__":
    # share=True 会创建一个公开链接，但请注意安全风险
    # In a secure environment, you might remove share=True
    demo.launch() # 默认不在 Colab 等环境中创建分享链接