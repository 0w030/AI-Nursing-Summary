# /db/patient_service.py

import sys
import os

# 路徑修正區塊
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import psycopg2
from db.db_connector import get_db_connection
from data.metadata import get_chinese_name

def get_patient_full_history(patient_id):
    """
    根據病歷號，從資料庫撈取該病患的所有急診相關數據。
    回傳的字典 Key 統一使用英文欄位名稱，以配合 ai_summarizer 使用。
    """
    conn = get_db_connection()
    if not conn:
        print("❌ 無法建立連線，無法查詢病患資料。")
        return None

    patient_data = {
        "nursing": [],
        "vitals": [],
        "labs": []
    }

    try:
        with conn.cursor() as cur:
            # 1. 護理紀錄 (ENSDATA)
            print(f"🔍 正在查詢病患 {patient_id} 的護理紀錄...")
            query_nursing = """
                SELECT PROCDTTM, SUBJECT, DIAGNOSIS 
                FROM ENSDATA 
                WHERE PATID = %s 
                ORDER BY PROCDTTM ASC
            """
            cur.execute(query_nursing, (patient_id,))
            rows = cur.fetchall()
            for row in rows:
                patient_data["nursing"].append({
                    "PROCDTTM": row[0],  # 改回英文 Key
                    "SUBJECT": row[1],   # 改回英文 Key
                    "DIAGNOSIS": row[2]  # 改回英文 Key
                })

            # 2. 生理監測 (v_ai_hisensnes)
            print(f"🔍 正在查詢病患 {patient_id} 的生理監測數據...")
            query_vitals = """
                SELECT PROCDTTM, ETEMPUTER, EPLUSE, EBREATHE, EPRESSURE, EDIASTOLIC, ESAO2, 
                       GCS_E, GCS_V, GCS_M
                FROM v_ai_hisensnes
                WHERE PATID = %s
                ORDER BY PROCDTTM ASC
            """
            cur.execute(query_vitals, (patient_id,))
            rows = cur.fetchall()
            for row in rows:
                patient_data["vitals"].append({
                    "PROCDTTM": row[0],      # 改回英文 Key
                    "ETEMPUTER": row[1],
                    "EPLUSE": row[2],
                    "EBREATHE": row[3],
                    "EPRESSURE": row[4],
                    "EDIASTOLIC": row[5],
                    "ESAO2": row[6],
                    # GCS 特殊處理：組合成字串
                    "GCS": f"E{row[7]}V{row[8]}M{row[9]}"
                })

            # 3. 檢驗結果 (DB_ADM_LABDATA_ER)
            print(f"🔍 正在查詢病患 {patient_id} 的檢驗報告...")
            query_labs = """
                SELECT CHRCPDTM, CHHEAD, CHVAL, CHUNIT, CHNL, CHNH
                FROM DB_ADM_LABDATA_ER
                WHERE CHMRNO = %s
                ORDER BY CHRCPDTM ASC
            """
            cur.execute(query_labs, (patient_id,))
            rows = cur.fetchall()
            for row in rows:
                patient_data["labs"].append({
                    "CHRCPDTM": row[0],       # 改回英文 Key
                    "CHHEAD": row[1],
                    "CHVAL": row[2],
                    "CHUNIT": row[3],
                    # 參考區間特殊處理
                    "REF_RANGE": f"{row[4]}~{row[5]}"
                })

        print(f"✅ 查詢完成！")
        return patient_data

    except psycopg2.Error as e:
        print(f"❌ 資料庫查詢失敗: {e}")
        return None
    finally:
        conn.close()

# /db/patient_service.py 的最下方

# ... (前面的 get_patient_full_history 函數保持不變) ...

# ==========================================
# 輔助函數：僅用於顯示時將 Key 轉為中文
# ==========================================
def translate_to_chinese_view(data_list):
    """
    將資料列表中的英文 Key 翻譯成中文，僅供閱讀使用。
    """
    if not data_list:
        return []
    
    view_list = []
    for item in data_list:
        new_item = {}
        for key, value in item.items():
            # 使用 metadata.py 裡的字典進行翻譯
            chinese_key = get_chinese_name(key)
            new_item[chinese_key] = value
        view_list.append(new_item)
    return view_list

if __name__ == "__main__":
    TEST_ID = '0002452972'
    print(f"--- 測試查詢模組: 病患 {TEST_ID} ---")
    
    # 1. 這裡撈出來的 data，內部還是【英文 Key】，保證 AI 讀得懂
    data = get_patient_full_history(TEST_ID)
    
    if data:
        import json
        
        # 2. 但在印出來給您看之前，我們先用上面的函數「翻譯」一下
        print("\n--- 1. 護理紀錄 (顯示中文 Key, 前 1 筆) ---")
        chinese_view = translate_to_chinese_view(data['nursing'][:1])
        print(json.dumps(chinese_view, indent=2, ensure_ascii=False))
        
        print("\n--- 2. 生理監測 (顯示中文 Key, 前 1 筆) ---")
        chinese_view = translate_to_chinese_view(data['vitals'][:1])
        print(json.dumps(chinese_view, indent=2, ensure_ascii=False))
        
        print("\n--- 3. 檢驗報告 (顯示中文 Key, 前 1 筆) ---")
        chinese_view = translate_to_chinese_view(data['labs'][:1])
        print(json.dumps(chinese_view, indent=2, ensure_ascii=False))
        
        print(f"\n✅ 統計: 護理 {len(data['nursing'])} 筆, 生理 {len(data['vitals'])} 筆, 檢驗 {len(data['labs'])} 筆")