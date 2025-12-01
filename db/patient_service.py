# /db/patient_service.py

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__)) # 取得目前檔案路徑 (db資料夾)
parent_dir = os.path.dirname(current_dir)              # 取得上一層路徑 (專案根目錄)
sys.path.append(parent_dir)                 # 加入搜尋路徑

import psycopg2
from db.db_connector import get_db_connection

def get_patient_full_history(patient_id):
    """
    根據病歷號 (PATID/CHMRNO)，從資料庫撈取該病患的所有急診相關數據。
    整合了：護理紀錄、生理監測、檢驗結果。
    
    Args:
        patient_id (str): 病患的病歷號 (例如 '2452972')
        
    Returns:
        dict: 包含 nursing, vitals, labs 三個列表的字典。若無資料或錯誤則回傳 None。
    """
    conn = get_db_connection()
    if not conn:
        print("❌ 無法建立連線，無法查詢病患資料。")
        return None

    # 初始化回傳結構
    patient_data = {
        "nursing": [],  # 護理紀錄
        "vitals": [],   # 生理監測
        "labs": []      # 檢驗報告
    }

    try:
        with conn.cursor() as cur:
            # ---------------------------------------------------
            # 1. 查詢護理紀錄 (ENSDATA)
            # ---------------------------------------------------
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
                    "記錄時間": row[0],
                    "主訴": row[1],
                    "診斷": row[2]
                })

            # ---------------------------------------------------
            # 2. 查詢生理監測 (v_ai_hisensnes)
            # ---------------------------------------------------
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
                    "記錄時間": row[0],
                    "體溫": row[1],
                    "脈搏": row[2],
                    "呼吸": row[3],
                    "血壓": f"{row[4]}/{row[5]}", # 收縮壓/舒張壓
                    "血氧": row[6],
                    "GCS": f"E{row[7]}V{row[8]}M{row[9]}"
                })

            # ---------------------------------------------------
            # 3. 查詢檢驗結果 (DB_ADM_LABDATA_ER)
            # 注意：檢驗表通常使用 CHMRNO 作為病歷號
            # ---------------------------------------------------
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
                    "收件時間": row[0],
                    "項目名稱": row[1],
                    "數值": row[2],
                    "單位": row[3],
                    "參考區間": f"{row[4]}~{row[5]}"
                })

        # 簡單統計
        n_count = len(patient_data['nursing'])
        v_count = len(patient_data['vitals'])
        l_count = len(patient_data['labs'])
        print(f"✅ 查詢完成！共找到：護理 {n_count} 筆, 生理 {v_count} 筆, 檢驗 {l_count} 筆")
        
        return patient_data

    except psycopg2.Error as e:
        print(f"❌ 資料庫查詢失敗: {e}")
        return None
    finally:
        conn.close()

# ==========================================
# 單獨測試區塊 (可以直接執行此檔案來測試查詢)
# ==========================================
if __name__ == "__main__":
    # 測試用的病歷號 (請替換成您資料庫裡實際存在的 ID)
    TEST_ID = '0002452972' 
    
    print(f"--- 測試查詢模組: 病患 {TEST_ID} ---")
    data = get_patient_full_history(TEST_ID)
    
    if data:
        import json
        # 印出前幾筆看看結構對不對
        print("\n--- 護理紀錄範例 (前1筆) ---")
        print(json.dumps(data['nursing'][:1], indent=2, ensure_ascii=False))
        
        print("\n--- 生理監測範例 (前1筆) ---")
        print(json.dumps(data['vitals'][:1], indent=2, ensure_ascii=False))
        
        print("\n--- 檢驗報告範例 (前1筆) ---")
        print(json.dumps(data['labs'][:1], indent=2, ensure_ascii=False))