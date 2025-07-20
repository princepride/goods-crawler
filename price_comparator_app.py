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
    """
    if coles_matched_file is None or woolworths_matched_file is None:
        return pd.DataFrame(), None, "错误：请同时上传Coles和Woolworths的匹配文件。"

    try:
        df_coles = pd.read_excel(coles_matched_file.name)
        df_ww = pd.read_excel(woolworths_matched_file.name)
    except Exception as e:
        return pd.DataFrame(), None, f"文件读取失败: {e}"

    if price_col_name_c not in df_coles.columns:
        return pd.DataFrame(), None, f"错误：在您上传的Coles文件中找不到价格列 '{price_col_name_c}'"
    if price_col_name_w not in df_ww.columns:
        return pd.DataFrame(), None, f"错误：在您上传的Woolworths文件中找不到价格列 '{price_col_name_w}'"
    
    merged_df = pd.merge(
        df_coles,
        df_ww,
        on='条形码',
        how='outer',
        suffixes=('_Coles', '_Woolworths')
    )

    suffixed_price_c = f"{price_col_name_c}_Coles"
    suffixed_price_w = f"{price_col_name_w}_Woolworths"
    
    effective_price_c = suffixed_price_c if suffixed_price_c in merged_df.columns else price_col_name_c
    effective_price_w = suffixed_price_w if suffixed_price_w in merged_df.columns else price_col_name_w
    
    if effective_price_c not in merged_df.columns:
         return pd.DataFrame(), None, f"严重错误：合并后在表格中找不到Coles的价格列 '{effective_price_c}'"
    if effective_price_w not in merged_df.columns:
         return pd.DataFrame(), None, f"严重错误：合并后在表格中找不到Woolworths的价格列 '{effective_price_w}'"

    # --- 新增修改：清理价格文本中的货币符号和逗号 ---
    # 使用 .astype(str) 确保该列为字符串类型，然后用 .str.replace 清理
    # 正则表达式 r'\$' 用来匹配美元符号，r',' 用来匹配逗号
    merged_df[effective_price_c] = merged_df[effective_price_c].astype(str).str.replace(r'\$', '', regex=True).str.replace(r',', '', regex=True)
    merged_df[effective_price_w] = merged_df[effective_price_w].astype(str).str.replace(r'\$', '', regex=True).str.replace(r',', '', regex=True)
    # --- 修改结束 ---

    # 现在，对清理后的纯净字符串进行数字转换
    merged_df[effective_price_c] = pd.to_numeric(merged_df[effective_price_c], errors='coerce')
    merged_df[effective_price_w] = pd.to_numeric(merged_df[effective_price_w], errors='coerce')
    
    conditions = [
        (merged_df[effective_price_c] < merged_df[effective_price_w]),
        (merged_df[effective_price_c] > merged_df[effective_price_w]),
        (merged_df[effective_price_c] == merged_df[effective_price_w]),
        (merged_df[effective_price_c].notna() & merged_df[effective_price_w].isna()),
        (merged_df[effective_price_c].isna() & merged_df[effective_price_w].notna())
    ]
    
    choices = ['Coles', 'Woolworths', '价格相同', '仅Coles有售', '仅Woolworths有售']
    merged_df['便宜的平台'] = np.select(conditions, choices, default='价格未知')
    merged_df['差价'] = (merged_df[effective_price_c] - merged_df[effective_price_w]).abs()
    
    name_col_c = '产品名称_Coles' if '产品名称_Coles' in merged_df.columns else '产品名称'
    name_col_w = '产品名称_Woolworths' if '产品名称_Woolworths' in merged_df.columns else '产品名称'

    final_cols = [
        '最佳匹配_Barcode', '商品描述',
        name_col_c, effective_price_c,
        name_col_w, effective_price_w,
        '便宜的平台', '差价'
    ]
    
    display_cols = [col for col in final_cols if col in merged_df.columns]
    final_df = merged_df[display_cols]
    
    final_df = final_df.rename(columns={
        name_col_c: 'Coles_产品名称',
        effective_price_c: 'Coles_价格',
        name_col_w: 'Woolworths_产品名称',
        effective_price_w: 'Woolworths_价格'
    })

    if '差价' in final_df.columns:
        final_df['差价'] = final_df['差价'].round(2)

    output_path = "final_price_comparison.xlsx"
    final_df.to_excel(output_path, index=False)

    return final_df, output_path, "比价完成！结果如下，您也可以下载Excel文件。"

# --- 创建 Gradio 界面 (这部分无需改变) ---
with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🛒 商品比价工具 (基于匹配结果)")
    gr.Markdown(
        "**操作流程:**\n"
        "1. 上传由上一步脚本生成的 `coles_matches.xlsx` 和 `woolworths_matches.xlsx` 文件。\n"
        "2. 确认两个文件中的价格列名称是否正确。\n"
        "3. 点击“开始比价”。"
    )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### **上传文件**")
            coles_file = gr.File(label="上传 Coles 匹配文件 (coles_matches.xlsx)")
            ww_file = gr.File(label="上传 Woolworths 匹配文件 (woolworths_matches.xlsx)")
        
        with gr.Column(scale=1):
            gr.Markdown("### **确认价格列名**")
            gr.Markdown("请确保这里的列名与您Excel文件中的价格列完全一致。")
            price_c = gr.Textbox(label="Coles 文件中的价格列名", value="现价")
            price_w = gr.Textbox(label="Woolworths 文件中的价格列名", value="现价")

    run_button = gr.Button("🚀 开始比价", variant="primary")
    status_text = gr.Textbox(label="状态", interactive=False)
    
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