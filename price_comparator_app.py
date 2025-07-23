import pandas as pd
import gradio as gr
import numpy as np

def compare_matched_files(
    coles_matched_file,
    woolworths_matched_file,
    price_col_name_c,
    price_col_name_w
):
    """
    Gradio调用的主函数，用于读取两个已匹配的Excel文件并进行比价。
    此版本新增了对“产品链接”字段的支持，并修复了因条形码重复导致输出行数爆炸的问题。
    """
    if coles_matched_file is None or woolworths_matched_file is None:
        return pd.DataFrame(), None, "错误：请同时上传Coles和Woolworths的匹配文件。"

    try:
        df_coles = pd.read_excel(coles_matched_file.name)
        df_ww = pd.read_excel(woolworths_matched_file.name)
    except Exception as e:
        return pd.DataFrame(), None, f"文件读取失败: {e}"

    # --- 核心检查 ---
    if '条形码' not in df_coles.columns or '条形码' not in df_ww.columns:
        return pd.DataFrame(), None, "错误：一个或两个文件中都缺少'条形码'列。"
    if price_col_name_c not in df_coles.columns:
        return pd.DataFrame(), None, f"错误：在Coles文件中找不到价格列 '{price_col_name_c}'"
    if price_col_name_w not in df_ww.columns:
        return pd.DataFrame(), None, f"错误：在Woolworths文件中找不到价格列 '{price_col_name_w}'"

    # --- 关键修复：合并前处理重复的条形码 ---
    df_coles.dropna(subset=['条形码'], inplace=True)
    df_ww.dropna(subset=['条形码'], inplace=True)

    initial_rows_c = len(df_coles)
    initial_rows_w = len(df_ww)
    df_coles = df_coles.drop_duplicates(subset=['条形码'], keep='first')
    df_ww = df_ww.drop_duplicates(subset=['条形码'], keep='first')
    unique_rows_c = len(df_coles)
    unique_rows_w = len(df_ww)

    status_update = (
        f"Coles: 找到 {initial_rows_c} 行, 去重后得到 {unique_rows_c} 个独立商品。\n"
        f"Woolworths: 找到 {initial_rows_w} 行, 去重后得到 {unique_rows_w} 个独立商品。\n"
        "正在基于唯一的条形码进行合并..."
    )

    # --- 合并数据 ---
    merged_df = pd.merge(
        df_coles,
        df_ww,
        on='条形码',
        how='outer',
        suffixes=('_Coles', '_Woolworths')
    )

    # --- 清理和转换价格列 ---
    price_c_suffixed = f"{price_col_name_c}_Coles"
    price_w_suffixed = f"{price_col_name_w}_Woolworths"

    for col in [price_c_suffixed, price_w_suffixed]:
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(
                merged_df[col].astype(str).str.replace(r'[$,]', '', regex=True),
                errors='coerce'
            )

    # --- 比价逻辑 ---
    conditions = [
        (merged_df[price_c_suffixed] < merged_df[price_w_suffixed]),
        (merged_df[price_c_suffixed] > merged_df[price_w_suffixed]),
        (merged_df[price_c_suffixed] == merged_df[price_w_suffixed]),
        (merged_df[price_c_suffixed].notna() & merged_df[price_w_suffixed].isna()),
        (merged_df[price_c_suffixed].isna() & merged_df[price_w_suffixed].notna())
    ]
    choices = ['Coles', 'Woolworths', '价格相同', '仅Coles有售', '仅Woolworths有售']
    merged_df['便宜的平台'] = np.select(conditions, choices, default='价格未知')
    merged_df['差价'] = (merged_df[price_c_suffixed] - merged_df[price_w_suffixed]).abs().round(2)

    # --- 准备最终输出的DataFrame ---
    # 动态找到所需列，并处理合并后可能不存在的情况
    name_col_c = next((col for col in merged_df.columns if '产品名称' in col and col.endswith('_Coles')), '产品名称_Coles')
    name_col_w = next((col for col in merged_df.columns if '产品名称' in col and col.endswith('_Woolworths')), '产品名称_Woolworths')
    link_col_c = next((col for col in merged_df.columns if '产品链接' in col and col.endswith('_Coles')), '产品链接_Coles')
    link_col_w = next((col for col in merged_df.columns if '产品链接' in col and col.endswith('_Woolworths')), '产品链接_Woolworths')
    
    # 为保证列的完整性，如果某些列不存在则创建空列
    cols_to_check = [name_col_c, name_col_w, price_c_suffixed, price_w_suffixed, link_col_c, link_col_w]
    for col in cols_to_check:
        if col not in merged_df.columns:
            merged_df[col] = np.nan if '价格' in col else 'N/A'

    # 整理最终显示的列
    final_df = merged_df[[
        '条形码',
        name_col_c,
        price_c_suffixed,
        link_col_c,
        name_col_w,
        price_w_suffixed,
        link_col_w,
        '便宜的平台',
        '差价'
    ]].copy()

    # 重命名列以获得更清晰的展示效果
    final_df.rename(columns={
        name_col_c: 'Coles_产品名称',
        price_c_suffixed: 'Coles_价格',
        link_col_c: 'Coles_产品链接',
        name_col_w: 'Woolworths_产品名称',
        price_w_suffixed: 'Woolworths_价格',
        link_col_w: 'Woolworths_产品链接'
    }, inplace=True)

    # --- 保存并返回结果 ---
    output_path = "final_price_comparison.xlsx"
    final_df.to_excel(output_path, index=False)

    final_status = status_update + f"\n合并完成！共生成 {len(final_df)} 行对比数据。结果如下，您也可以下载Excel文件。"
    
    return final_df, output_path, final_status

# --- 创建 Gradio 界面 (这部分无需改变) ---
with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🛒 商品比价工具 (基于匹配结果)")
    gr.Markdown(
        "**操作流程:**\n"
        "1. 上传两个平台包含“条形码”、“价格”和“产品链接”的Excel文件。\n"
        "2. 确认两个文件中的价格列名称是否正确 (链接列会自动识别)。\n"
        "3. 点击“开始比价”。工具会自动处理重复商品，只比较唯一项。"
    )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### **上传文件**")
            coles_file = gr.File(label="上传 Coles 文件")
            ww_file = gr.File(label="上传 Woolworths 文件")
        
        with gr.Column(scale=1):
            gr.Markdown("### **确认价格列名**")
            gr.Markdown("请确保这里的列名与您Excel文件中的价格列完全一致。")
            price_c = gr.Textbox(label="Coles 文件中的价格列名", value="现价")
            price_w = gr.Textbox(label="Woolworths 文件中的价格列名", value="现价")

    run_button = gr.Button("🚀 开始比价", variant="primary")
    status_text = gr.Textbox(label="状态", interactive=False, lines=4)
    
    gr.Markdown("### **比价结果**")
    result_df = gr.DataFrame(label="比较结果表格")
    download_button = gr.File(label="下载比价结果 (Excel)", interactive=False)

    run_button.click(
        fn=compare_matched_files,
        inputs=[coles_file, ww_file, price_c, price_w],
        outputs=[result_df, download_button, status_text]
    )

if __name__ == "__main__":
    app.launch()
