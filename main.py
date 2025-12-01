# main.py

import sys
import os
from dotenv import load_dotenv

# 引入我們剛剛建立的查詢服務 (針對真實資料表)
from db.patient_service import get_patient_full_history

# 引入 AI 模組 (先保留引用，暫不執行，或是稍後再打開)
from ai.ai_summarizer import generate_nursing_summary

# 設定真實存在的病歷號 (來自您的 CSV)
TEST_PATIENT_ID = '0002452972' 

def main():
    print(f"=== 啟動 AI 護理摘要系統 (目標病歷號: {TEST_PATIENT_ID}) ===")

    # 1. 環境初始化 (只做最基本的載入變數)
    load_dotenv()
    
    # 2. 從資料庫撈取完整病程 (使用新的 patient_service)
    print("1. 正在從 Railway 資料庫撈取病歷資料...")
    patient_data = get_patient_full_history(TEST_PATIENT_ID)

    if not patient_data:
        print("❌ 錯誤：找不到該病患資料，請確認 ID 是否正確。")
        return

    # 顯示撈取結果統計
    n_count = len(patient_data['nursing'])
    v_count = len(patient_data['vitals'])
    l_count = len(patient_data['labs'])
    print(f"✅ 撈取成功！資料統計：")
    print(f"   - 護理紀錄: {n_count} 筆")
    print(f"   - 生理監測: {v_count} 筆")
    print(f"   - 檢驗報告: {l_count} 筆")

    # 3. (AI 部分) 呼叫 ChatGPT
    # 如果您暫時不想跑 AI，可以把下面這幾行註解掉
    if os.getenv("OPENAI_API_KEY"):
        print("\n2. 正在呼叫 AI 生成摘要 (這可能需要幾秒鐘)...")
        summary = generate_nursing_summary(TEST_PATIENT_ID, patient_data)
        
        print("\n" + "="*40)
        print("       🚑 急診病程摘要 (AI Generated)")
        print("="*40)
        print(summary)
        print("="*40)
    else:
        print("\n⚠️ 未偵測到 OPENAI_API_KEY，跳過 AI 摘要生成步驟。")

if __name__ == '__main__':
    main()