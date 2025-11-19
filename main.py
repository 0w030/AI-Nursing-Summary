# main.py

import os
from dotenv import load_dotenv
from db.db_connector import execute_sql_script, fetch_reports_by_patient, save_summary
from ai.ai_summarizer import format_reports_to_prompt, generate_summary
from data.data_processor import insert_mock_data

# 專案設定
SCHEMA_FILE = 'sql/schema.sql'
TEST_PATIENT_ID = 'P001'

def setup_environment():
    """初始化環境設定，包括載入環境變數和建立資料表結構"""
    print("--- 1. 環境初始化 ---")
    load_dotenv()
    
    # 確保資料庫結構存在
    # 注意：首次運行時，請確保資料庫中沒有舊的同名表格，否則會失敗
    # 建議在 schema.sql 中加入 DROP TABLE IF EXISTS examination_reports;
    if execute_sql_script(SCHEMA_FILE):
        print("資料庫結構建立/檢查完成。")
        
        # 插入模擬數據（僅用於首次測試）
        # 請確保在每次測試前資料庫是清空的，避免重複插入
        insert_mock_data()
    else:
        print("環境設定失敗，請檢查資料庫連線或 SQL 腳本。")
        return False
    return True

def run_summarizer_workflow(patient_id):
    """
    執行完整的報告摘要工作流：讀取 -> 格式化 -> AI摘要 -> 儲存。
    """
    print(f"\n--- 2. 開始摘要工作流 (病患 ID: {patient_id}) ---")

    # 步驟 1: 從資料庫讀取報告數據
    reports = fetch_reports_by_patient(patient_id)
    if not reports:
        print("錯誤: 找不到該病患的任何報告。")
        return

    print(f"成功讀取 {len(reports)} 份報告。")
    
    # 步驟 2: 格式化數據為 Prompt
    prompt = format_reports_to_prompt(reports)
    print("\n--- 3. Prompt 生成完成，準備呼叫 AI ---")
    
    # 步驟 3: 呼叫 AI API 生成摘要
    summary_text = generate_summary(prompt)
    
    if summary_text.startswith("AI 摘要生成錯誤"):
        print(summary_text)
        return
    
    print("\n--- 4. AI 摘要結果 ---")
    print(summary_text)
    
    # 步驟 5: 將摘要儲存回資料庫
    # 這裡我們只將摘要儲存到第一份報告的欄位，但在實際應用中，
    # 您可能需要創建一個獨立的 '病程總結' 記錄。
    first_report_id = reports[0]['report_id']
    save_summary(first_report_id, summary_text)
    
    print("\n--- 5. 摘要工作流完成 ---")


if __name__ == '__main__':
    if setup_environment():
        run_summarizer_workflow(TEST_PATIENT_ID)