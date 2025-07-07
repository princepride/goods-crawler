# import pandas as pd
# from nltk.translate.bleu_score import sentence_bleu
# from nltk.tokenize import word_tokenize
# import warnings
# import tqdm
# from multiprocessing import Pool, cpu_count
# warnings.filterwarnings('ignore', category=UserWarning)
# def _process_single_product(args):
#     candidate_name, original_input_row, reference_data_tuples, reference_barcode_column, reference_desc_column = args
#     candidate_tokens = word_tokenize(candidate_name)
#     scores = []
#     for ref_tokens, barcode, original_description in reference_data_tuples:
#         bleu_score = sentence_bleu([ref_tokens], candidate_tokens, weights=(0.5, 0.5, 0, 0))
#         scores.append({
#             'bleu_score': bleu_score,
#             'Barcode': barcode,
#             'Description': original_description
#         })
#     top_match = sorted(scores, key=lambda x: x['bleu_score'], reverse=True)[0]
#     result_row = original_input_row.to_dict() # 将原始行转换为字典
#     result_row['最佳匹配_Barcode'] = top_match['Barcode']
#     result_row['最佳匹配_Description'] = top_match['Description']
#     return result_row
# def find_top_bleu_matches(
#     input_file_path: str,
#     reference_file_path: str,
#     input_column_name: str = '产品名称',
#     reference_barcode_column: str = 'Barcode',
#     reference_desc_column: str = 'Description'
# ) -> pd.DataFrame:
#     try:
#         input_df = pd.read_excel(input_file_path)
#         reference_df = pd.read_excel(reference_file_path, dtype={reference_barcode_column: str})
#     except FileNotFoundError as e:
#         return pd.DataFrame()
#     reference_df[reference_desc_column] = reference_df[reference_desc_column].astype(str).str.lower()
#     input_df[input_column_name] = input_df[input_column_name].astype(str).str.lower() # 确保用于匹配的列是小写
#     reference_data_tuples = list(zip(
#         reference_df[reference_desc_column].apply(word_tokenize),
#         reference_df[reference_barcode_column],
#         reference_df[reference_desc_column]
#     ))
#     all_results = []
#     tasks = [
#         (row[input_column_name], row, reference_data_tuples, reference_barcode_column, reference_desc_column)
#         for index, row in input_df.iterrows()
#     ]
#     with Pool(cpu_count()) as pool:
#         for result_row in tqdm.tqdm(pool.imap(_process_single_product, tasks), total=len(tasks), desc="处理产品名称"):
#             all_results.append(result_row)
#     final_df = pd.DataFrame(all_results)
#     if '最佳匹配_Barcode' in final_df.columns:
#         final_df['最佳匹配_Barcode'] = final_df['最佳匹配_Barcode'].astype(str)

#     return final_df

# if __name__ == '__main__':
#     INPUT_FILE = 'coles_data.xlsx'
#     DATABASE_FILE = 'Item Barcode.xlsx'
#     results_df = find_top_bleu_matches(
#         input_file_path=INPUT_FILE,
#         reference_file_path=DATABASE_FILE
#     )
#     if not results_df.empty:
#         output_file_name = 'coles_matches.xlsx'
#         results_df.to_excel(output_file_name, index=False)
#     INPUT_FILE = 'woolworths_data.xlsx'
#     DATABASE_FILE = 'Item Barcode.xlsx'
#     results_df = find_top_bleu_matches(
#         input_file_path=INPUT_FILE,
#         reference_file_path=DATABASE_FILE
#     )
#     if not results_df.empty:
#         output_file_name = 'woolworths_matches.xlsx'
#         results_df.to_excel(output_file_name, index=False)

import pandas as pd
from nltk.translate.bleu_score import sentence_bleu
from nltk.tokenize import word_tokenize
import warnings
import tqdm
from multiprocessing import Pool, cpu_count
import re # 引入正则表达式库用于高效提取数字

warnings.filterwarnings('ignore', category=UserWarning)

# --- 新增辅助函数 ---
def _extract_digits(text: str) -> set:
    """从字符串中提取所有数字，并以集合形式返回。"""
    # re.findall(r'\d', text) 会找到所有独立的数字字符
    # 例如 "可乐500ml" -> {'5', '0'}
    return set(re.findall(r'\d', str(text)))

# --- 修改核心匹配逻辑函数 ---
def _process_single_product(args):
    """
    处理单个产品，应用新的匹配规则：
    如果待匹配项含数字，则优先选择BLEU排名前10中，首个同样含数字的项。
    """
    candidate_name, original_input_row, reference_data_tuples, reference_barcode_column, reference_desc_column = args
    candidate_tokens = word_tokenize(candidate_name)
    
    scores = []
    # 第一次遍历：计算所有参考项的BLEU分数
    for ref_tokens, barcode, original_description in reference_data_tuples:
        bleu_score = sentence_bleu([ref_tokens], candidate_tokens, weights=(0.5, 0.5, 0, 0))
        scores.append({
            'bleu_score': bleu_score,
            'Barcode': barcode,
            'Description': original_description
        })

    # 如果没有任何分数，提前返回
    if not scores:
        return None

    # 按BLEU分数从高到低排序
    sorted_scores = sorted(scores, key=lambda x: x['bleu_score'], reverse=True)

    # --- 新的匹配规则逻辑 ---
    # 默认的最佳匹配永远是BLEU分数最高的那个（作为备选）
    best_match = sorted_scores[0]
    
    # 提取待匹配项中的数字
    candidate_digits = _extract_digits(candidate_name)
    
    # 只有当待匹配项中确实含有数字时，才启用新规则
    if candidate_digits:
        # 遍历BLEU分数排名前3的候选项
        for potential_match in sorted_scores[:3]:
            reference_digits = _extract_digits(potential_match['Description'])
            
            # 检查两个数字集合是否有交集（即，是否有任何一个共同的数字）
            if candidate_digits & reference_digits:
                # 找到了！将此项设为最佳匹配
                best_match = potential_match
                # 跳出循环，因为我们只需要最先出现的那一个
                break
    
    # --- 逻辑结束 ---

    # 将最终选定的 best_match 信息添加到结果中
    result_row = original_input_row.to_dict()
    result_row['最佳匹配_Barcode'] = best_match['Barcode']
    result_row['最佳匹配_Description'] = best_match['Description']
    return result_row

# vvvvvv 以下函数及主程序部分无需任何修改 vvvvvv

def find_top_bleu_matches(
    input_file_path: str,
    reference_file_path: str,
    input_column_name: str = '产品名称',
    reference_barcode_column: str = 'Barcode',
    reference_desc_column: str = 'Description'
) -> pd.DataFrame:
    try:
        input_df = pd.read_excel(input_file_path)
        reference_df = pd.read_excel(reference_file_path, dtype={reference_barcode_column: str})
    except FileNotFoundError as e:
        print(f"错误：找不到文件 {e.filename}")
        return pd.DataFrame()
        
    reference_df[reference_desc_column] = reference_df[reference_desc_column].astype(str).str.lower()
    input_df[input_column_name] = input_df[input_column_name].astype(str).str.lower()
    
    reference_data_tuples = list(zip(
        reference_df[reference_desc_column].apply(word_tokenize),
        reference_df[reference_barcode_column],
        reference_df[reference_desc_column]
    ))
    
    all_results = []
    tasks = [
        (row[input_column_name], row, reference_data_tuples, reference_barcode_column, reference_desc_column)
        for index, row in input_df.iterrows()
    ]
    
    # 确保在Windows等系统上多进程能正常工作
    # 需要将nltk.download('punkt')放在主程序块中
    
    with Pool(cpu_count()) as pool:
        for result_row in tqdm.tqdm(pool.imap(_process_single_product, tasks), total=len(tasks), desc="处理产品名称"):
            if result_row: # 确保只添加非None的结果
                all_results.append(result_row)
                
    final_df = pd.DataFrame(all_results)
    if '最佳匹配_Barcode' in final_df.columns:
        final_df['最佳匹配_Barcode'] = final_df['最佳匹配_Barcode'].astype(str)

    return final_df

if __name__ == '__main__':
    INPUT_FILE = 'coles_data.xlsx'
    DATABASE_FILE = 'Item Barcode.xlsx'
    results_df = find_top_bleu_matches(
        input_file_path=INPUT_FILE,
        reference_file_path=DATABASE_FILE
    )
    if not results_df.empty:
        output_file_name = 'coles_matches.xlsx'
        results_df.to_excel(output_file_name, index=False)
        print(f"匹配完成，结果已保存至 {output_file_name}")

    INPUT_FILE = 'woolworths_data.xlsx'
    DATABASE_FILE = 'Item Barcode.xlsx'
    results_df = find_top_bleu_matches(
        input_file_path=INPUT_FILE,
        reference_file_path=DATABASE_FILE
    )
    if not results_df.empty:
        output_file_name = 'woolworths_matches.xlsx'
        results_df.to_excel(output_file_name, index=False)
        print(f"匹配完成，结果已保存至 {output_file_name}")