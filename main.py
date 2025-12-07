# main.py

import sys
import os
from dotenv import load_dotenv
from db.patient_service import get_patient_full_history
from ai.ai_summarizer import generate_nursing_summary

# 設定病歷號
TEST_PATIENT_ID = '0002452972' 

# === 【新增】 時間篩選設定 ===
# 格式：YYYYMMDDHHMMSS (例如：2025年11月15日 15點00分00秒)
# 如果設為 None，代表不限制
FILTER_START_TIME = None
FILTER_END_TIME   = '20251115153000'

def main():
    print(f"=== 啟動 AI 護理摘要系統 ===")
    print(f"目標: {TEST_PATIENT_ID}")
    print(f"區間: {FILTER_START_TIME} ~ {FILTER_END_TIME}")

    load_dotenv()
    
    # 1. 撈取資料 (帶入時間參數)
    print("\n1. 正在撈取指定時間內的資料...")
    patient_data = get_patient_full_history(
        TEST_PATIENT_ID, 
        start_time=FILTER_START_TIME, 
        end_time=FILTER_END_TIME
    )

    if not patient_data:
        print("錯誤：找不到資料。")
        return

    # 顯示統計
    n_count = len(patient_data['nursing'])
    v_count = len(patient_data['vitals'])
    l_count = len(patient_data['labs'])
    
    print(f"撈取成功！")
    print(f"   - 護理: {n_count} 筆")
    print(f"   - 生理: {v_count} 筆")
    print(f"   - 檢驗: {l_count} 筆")
    
    # 如果資料還是太多，可以提示使用者
    total_records = n_count + v_count + l_count
    if total_records == 0:
        print("此時段無資料，結束程式。")
        return

    # 2. 呼叫 AI
    if os.getenv("GROQ_API_KEY"):
        print("\n2. 正在呼叫 Groq AI 生成摘要...")
        summary = generate_nursing_summary(TEST_PATIENT_ID, patient_data)
        
        print("\n" + "="*40)
        print("       急診病程摘要 (AI Generated)")
        print("="*40)
        print(summary)
        print("="*40)
    else:
        print("\n未偵測到 GROQ_API_KEY。")

if __name__ == '__main__':
    main()