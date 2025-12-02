# /db/patient_service.py

import sys
import os
import psycopg2

# 路徑修正區塊
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from db.db_connector import get_db_connection
from data.metadata import get_chinese_name

def get_patient_full_history(patient_id, start_time=None, end_time=None):
    """
    根據病歷號及時間範圍，從資料庫撈取病患的所有急診相關數據。
    回傳的字典 Key 統一使用英文欄位名稱，以配合 ai_summarizer 使用。

    Args:
        patient_id (str): 病歷號
        start_time (str, optional): 篩選起始時間 (YYYYMMDDHHMMSS)
        end_time (str, optional): 篩選結束時間
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
            # ==========================================
            # 1. 護理紀錄 (時間欄位: PROCDTTM)
            # ==========================================
            print(f"🔍 正在查詢病患 {patient_id} 的護理紀錄...")
            
            # 基礎 SQL
            sql_nursing = "SELECT PROCDTTM, SUBJECT, DIAGNOSIS FROM ENSDATA WHERE PATID = %s"
            params_nursing = [patient_id]

            # 動態加入時間篩選
            if start_time:
                sql_nursing += " AND PROCDTTM >= %s"
                params_nursing.append(start_time)
            if end_time:
                sql_nursing += " AND PROCDTTM <= %s"
                params_nursing.append(end_time)
            
            sql_nursing += " ORDER BY PROCDTTM ASC"

            cur.execute(sql_nursing, tuple(params_nursing))
            rows = cur.fetchall()
            for row in rows:
                patient_data["nursing"].append({
                    "PROCDTTM": row[0],
                    "SUBJECT": row[1],
                    "DIAGNOSIS": row[2]
                })

            # ==========================================
            # 2. 生理監測 (時間欄位: PROCDTTM)
            # ==========================================
            print(f"🔍 正在查詢病患 {patient_id} 的生理監測數據...")
            
            sql_vitals = """
                SELECT PROCDTTM, ETEMPUTER, EPLUSE, EBREATHE, EPRESSURE, EDIASTOLIC, ESAO2, 
                       GCS_E, GCS_V, GCS_M
                FROM v_ai_hisensnes WHERE PATID = %s
            """
            params_vitals = [patient_id]

            if start_time:
                sql_vitals += " AND PROCDTTM >= %s"
                params_vitals.append(start_time)
            if end_time:
                sql_vitals += " AND PROCDTTM <= %s"
                params_vitals.append(end_time)
            
            sql_vitals += " ORDER BY PROCDTTM ASC"

            cur.execute(sql_vitals, tuple(params_vitals))
            rows = cur.fetchall()
            for row in rows:
                patient_data["vitals"].append({
                    "PROCDTTM": row[0],
                    "ETEMPUTER": row[1],
                    "EPLUSE": row[2],
                    "EBREATHE": row[3],
                    "EPRESSURE": row[4],
                    "EDIASTOLIC": row[5],
                    "ESAO2": row[6],
                    "GCS": f"E{row[7]}V{row[8]}M{row[9]}"
                })

            # ==========================================
            # 3. 檢驗結果 (時間欄位: CHRCPDTM)
            # ==========================================
            print(f"🔍 正在查詢病患 {patient_id} 的檢驗報告...")
            
            sql_labs = """
                SELECT CHRCPDTM, CHHEAD, CHVAL, CHUNIT, CHNL, CHNH
                FROM DB_ADM_LABDATA_ER WHERE CHMRNO = %s
            """
            params_labs = [patient_id]

            if start_time:
                sql_labs += " AND CHRCPDTM >= %s"
                params_labs.append(start_time)
            if end_time:
                sql_labs += " AND CHRCPDTM <= %s"
                params_labs.append(end_time)
            
            sql_labs += " ORDER BY CHRCPDTM ASC"

            cur.execute(sql_labs, tuple(params_labs))
            rows = cur.fetchall()
            for row in rows:
                patient_data["labs"].append({
                    "CHRCPDTM": row[0],
                    "CHHEAD": row[1],
                    "CHVAL": row[2],
                    "CHUNIT": row[3],
                    "REF_RANGE": f"{row[4]}~{row[5]}"
                })

        print(f"✅ 查詢完成 (時間範圍: {start_time if start_time else '不限'} ~ {end_time if end_time else '不限'})")
        return patient_data

    except psycopg2.Error as e:
        print(f"❌ 資料庫查詢失敗: {e}")
        return None
    finally:
        conn.close()

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
            chinese_key = get_chinese_name(key)
            new_item[chinese_key] = value
        view_list.append(new_item)
    return view_list

# ==========================================
# 測試區塊
# ==========================================
if __name__ == "__main__":
    TEST_ID = '0002452972'
    
    # 測試：只查某個時段的資料 (例如只查 11/15 下午 3 點之後)
    START = '20251115150000'
    END = None # 不限制結束時間
    
    print(f"--- 測試查詢模組: 病患 {TEST_ID} (時間篩選: {START} ~ ) ---")
    
    # 1. 這裡撈出來的 data，內部還是【英文 Key】
    data = get_patient_full_history(TEST_ID, start_time=START, end_time=END)
    
    if data:
        import json
        
        # 2. 顯示中文 Key (翻譯後)
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