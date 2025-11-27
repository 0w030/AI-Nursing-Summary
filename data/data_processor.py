import csv
import os
import random
import psycopg2
from db.db_connector import get_db_connection

# =========================================================
# 1. 匯入急診檢驗明細 (DB_ADM_LABDATA_ER)
# =========================================================
def import_lab_data_er():
    """匯入急診檢驗明細 (22欄位)"""
    csv_filename = 'DB_ADM_LABDATA_ER-急診檢驗明細.csv'
    csv_filepath = os.path.join(os.path.dirname(__file__), csv_filename)
    
    print(f"--- [1/5] 開始匯入 {csv_filename} ---")
    conn = get_db_connection()
    if not conn: return

    try:
        with open(csv_filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = []
            for row in reader:
                # 處理空字串和 (null)
                cleaned = [None if val.strip() in ['(null)', ''] else val for val in row]
                # 補齊至 22 欄
                while len(cleaned) < 22: cleaned.append(None)
                data.append(tuple(cleaned[:22]))

        if data:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO DB_ADM_LABDATA_ER (
                        CHAD1CASENO, CHMRNO, CHGREQNO, CHAPPDTM, CHRCPDTM, 
                        CHLREQNO, CHORDNO, CHITEMNO, CHHEAD, CHTEAMNAM, 
                        CHSTAT, CHSPECI, CHVAL, CHUNIT, CHCOMMT, 
                        CHNL, CHNH, CHITEMSEQ, CHREPORTDATE, CHTEXT, 
                        CHSIGNDTTM, CHLABAPCODE
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
                cur.executemany(query, data)
            conn.commit()
            print(f"✅ 成功匯入 {len(data)} 筆資料到 DB_ADM_LABDATA_ER")
        else:
            print("⚠️ 檔案為空")

    except Exception as e:
        print(f"❌ 匯入失敗: {e}")
    finally:
        conn.close()

# =========================================================
# 2. 匯入急診檢驗頭檔 (DB_ADM_LABORDER_ER)
# =========================================================
def import_lab_order_er():
    """匯入急診檢驗頭檔 (20欄位)"""
    csv_filename = 'DB_ADM_LABORDER_ER-急診檢驗頭檔.csv'
    csv_filepath = os.path.join(os.path.dirname(__file__), csv_filename)
    
    print(f"--- [2/5] 開始匯入 {csv_filename} ---")
    conn = get_db_connection()
    if not conn: return

    try:
        with open(csv_filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = []
            for row in reader:
                cleaned = [None if val.strip() in ['(null)', ''] else val for val in row]
                while len(cleaned) < 20: cleaned.append(None)
                data.append(tuple(cleaned[:20]))

        if data:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO DB_ADM_LABORDER_ER (
                        CHCASENO, CHMRNO, CHGREQNO, CHAPPDTM, CHLREQNO, CHORDNO, CHORDNAM, 
                        CHTEAMNAM, CHSTAT, CHSPECI, SOURCETYPE, ORDSEQ, CHTAPPDT, CHRCPDTM, 
                        CHRCONNAME, CONCODE, LABMCHNO, LABUNIFNO, LABCLASS, ORDPROCDTTM
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
                cur.executemany(query, data)
            conn.commit()
            print(f"✅ 成功匯入 {len(data)} 筆資料到 DB_ADM_LABORDER_ER")
        else:
            print("⚠️ 檔案為空")

    except Exception as e:
        print(f"❌ 匯入失敗: {e}")
    finally:
        conn.close()

# =========================================================
# 3. 匯入急診生理監測 (v_ai_hisensnes) - 含數值模擬
# =========================================================
def import_vital_signs():
    """匯入急診生理監測 (18欄位) - 自動填補正常生理數值"""
    csv_filename = 'v_ai_hisensnes-急診生理監測-.csv'
    csv_filepath = os.path.join(os.path.dirname(__file__), csv_filename)
    
    print(f"--- [3/5] 開始匯入 {csv_filename} (模擬正常數值填補) ---")
    conn = get_db_connection()
    if not conn: return

    try:
        with open(csv_filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = []
            
            for row in reader:
                cleaned_row = [val.strip() for val in row]
                while len(cleaned_row) < 18: cleaned_row.append('')

                # === 開始模擬數值邏輯 ===
                # 3: EWEIGHT (體重) 55-78
                if cleaned_row[3] in ['', '(null)']: cleaned_row[3] = str(random.randint(55, 78))
                # 4: ETEMPUTER (體溫) 36.2-37.0
                if cleaned_row[4] in ['', '(null)']: cleaned_row[4] = str(round(random.uniform(36.2, 37.0), 1))
                # 5: ETREGION (部位) 預設 '2'
                if cleaned_row[5] in ['', '(null)']: cleaned_row[5] = '2'
                # 6: EPLUSE (脈搏) 65-95
                if cleaned_row[6] in ['', '(null)']: cleaned_row[6] = str(random.randint(65, 95))
                # 7: EBREATHE (呼吸) 14-18
                if cleaned_row[7] in ['', '(null)']: cleaned_row[7] = str(random.randint(14, 18))
                # 8: EPRESSURE (收縮壓) 110-135
                if cleaned_row[8] in ['', '(null)']: cleaned_row[8] = str(random.randint(110, 135))
                # 9: EDIASTOLIC (舒張壓) 70-85
                if cleaned_row[9] in ['', '(null)']: cleaned_row[9] = str(random.randint(70, 85))
                # 10: ESAO2 (血氧) 97-99
                if cleaned_row[10] in ['', '(null)']: cleaned_row[10] = str(random.randint(97, 99))
                # 11-13: GCS 4/5/6
                if cleaned_row[11] in ['', '(null)']: cleaned_row[11] = '4'
                if cleaned_row[12] in ['', '(null)']: cleaned_row[12] = '5'
                if cleaned_row[13] in ['', '(null)']: cleaned_row[13] = '6'
                # 14-15: PUPIL 2.5/3.0
                if cleaned_row[14] in ['', '(null)']: cleaned_row[14] = str(random.choice([2.5, 3.0]))
                if cleaned_row[15] in ['', '(null)']: cleaned_row[15] = str(random.choice([2.5, 3.0]))
                # 16: ENESKIND (檢傷) 預設 '3'
                if cleaned_row[16] in ['', '(null)']: cleaned_row[16] = '3'
                # === 結束模擬 ===

                data.append(tuple(cleaned_row[:18]))

        if data:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO v_ai_hisensnes (
                        TRINO, PATID, VISITDT, EWEIGHT, ETEMPUTER, ETREGION, EPLUSE, 
                        EBREATHE, EPRESSURE, EDIASTOLIC, ESAO2, GCS_E, GCS_V, GCS_M, 
                        PUPIL_L, PUPIL_R, ENESKIND, PROCDTTM
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
                cur.executemany(query, data)
            conn.commit()
            print(f"✅ 成功匯入 {len(data)} 筆資料到 v_ai_hisensnes")
        else:
            print("⚠️ 檔案為空")

    except Exception as e:
        print(f"❌ 匯入失敗: {e}")
    finally:
        conn.close()

# =========================================================
# 4. 匯入急診護理紀錄 (ENSDATA)
# =========================================================
def import_nursing_records():
    """匯入急診護理紀錄 (9欄位)"""
    csv_filename = 'ENSDATA-急診護理紀錄.csv'
    csv_filepath = os.path.join(os.path.dirname(__file__), csv_filename)
    
    print(f"--- [4/5] 開始匯入 {csv_filename} ---")
    conn = get_db_connection()
    if not conn: return

    try:
        with open(csv_filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = []
            for row in reader:
                cleaned = [None if val.strip() in ['(null)', ''] else val for val in row]
                while len(cleaned) < 9: cleaned.append(None)
                data.append(tuple(cleaned[:9]))

        if data:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO ENSDATA (
                        TRINO, PATID, VISITDT, SEQ, SUBJECT, PROCDTTM, 
                        DIAGNOSIS, CLOSE, FIINISH
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
                cur.executemany(query, data)
            conn.commit()
            print(f"✅ 成功匯入 {len(data)} 筆資料到 ENSDATA")
        else:
            print("⚠️ 檔案為空")

    except Exception as e:
        print(f"❌ 匯入失敗: {e}")
    finally:
        conn.close()

# =========================================================
# 5. 匯入急診檢驗檢查主檔 (DB_ADM_ORDER_ER)
# =========================================================
def import_adm_order_er():
    """匯入急診檢驗檢查主檔 (15欄位)"""
    csv_filename = 'DB_ADM_ORDER_ER-急診檢驗檢查主檔.csv'
    csv_filepath = os.path.join(os.path.dirname(__file__), csv_filename)
    
    print(f"--- [5/5] 開始匯入 {csv_filename} ---")
    conn = get_db_connection()
    if not conn: return

    try:
        with open(csv_filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = []
            for row in reader:
                cleaned = [None if val.strip() in ['(null)', ''] else val for val in row]
                while len(cleaned) < 15: cleaned.append(None)
                data.append(tuple(cleaned[:15]))

        if data:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO DB_ADM_ORDER_ER (
                        CHAD1CASENO, CHAD1MRNO, CHAD4GREQNO, CHAD4CDATE, CHAD1ORDNO, 
                        CHAD4ORDNAME, CHTEAMNAM, CHAD4SPECT, CHAD4DCDATE, CHAD4STAT, 
                        CHAD4REP1, CHRCPDTM, CHREPORTDATE, CHTEXT, SOURCETYPE
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
                cur.executemany(query, data)
            conn.commit()
            print(f"✅ 成功匯入 {len(data)} 筆資料到 DB_ADM_ORDER_ER")
        else:
            print("⚠️ 檔案為空")

    except Exception as e:
        print(f"❌ 匯入失敗: {e}")
    finally:
        conn.close()

# =========================================================
# 主程式執行入口
# =========================================================
if __name__ == '__main__':
    print("=== 開始執行資料匯入作業 ===")
    
    # 執行所有匯入函數
    import_lab_data_er()
    import_lab_order_er()
    import_vital_signs()
    import_nursing_records()
    import_adm_order_er()
    
    print("=== 所有匯入作業完成 ===")