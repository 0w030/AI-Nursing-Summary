# /db/db_connector.py

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

# 載入環境變數
load_dotenv()

def get_db_connection():
    """從環境變數建立並返回一個 PostgreSQL 連線物件"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        return conn
    except psycopg2.Error as e:
        print(f"資料庫連線失敗: {e}")
        return None

def fetch_reports_by_patient(patient_id):
    """
    根據病患 ID 讀取其所有檢查報告。
    返回報告列表，並依照日期升序排列。
    """
    conn = get_db_connection()
    if not conn:
        return []

    reports = []
    try:
        with conn.cursor() as cur:
            # 查詢報告：選擇 ID, 日期, 類型, 和結構化資料
            query = sql.SQL("""
                SELECT report_id, examination_date, report_type, structured_data
                FROM examination_reports
                WHERE patient_id = %s
                ORDER BY examination_date ASC;
            """)
            cur.execute(query, (patient_id,))
            
            # 將結果轉換為字典列表以便後續處理
            for row in cur.fetchall():
                reports.append({
                    'report_id': row[0],
                    'date': row[1].strftime('%Y-%m-%d'),
                    'type': row[2],
                    'data': row[3]  # JSONB 資料
                })
        
    except psycopg2.Error as e:
        print(f"讀取報告失敗: {e}")
    finally:
        conn.close()
    
    return reports

def save_summary(report_id, summary_text):
    """
    將 AI 生成的摘要寫回資料庫的指定報告 ID 欄位。
    """
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            # 更新資料庫
            query = sql.SQL("""
                UPDATE examination_reports
                SET generated_summary = %s, summary_generation_date = NOW()
                WHERE report_id = %s;
            """)
            cur.execute(query, (summary_text, report_id))
        
        conn.commit()
        print(f"報告 {report_id} 摘要儲存成功。")
        return True
        
    except psycopg2.Error as e:
        print(f"儲存摘要失敗: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ----------------------------------------------------
# 輔助函數：執行 SQL 腳本 (用於建立資料表)
# ----------------------------------------------------

def execute_sql_script(filepath):
    """執行指定的 SQL 腳本 (例如 schema.sql)"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        with conn.cursor() as cur:
            # 使用 execute_batch 執行多個 SQL 語句
            cur.execute(sql_script)
        
        conn.commit()
        print(f"SQL 腳本 {filepath} 執行成功。")
        return True
        
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {filepath}")
        return False
    except psycopg2.Error as e:
        print(f"執行 SQL 腳本失敗: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    # 測試連線
    print("--- 測試資料庫連線 ---")
    conn = get_db_connection()
    if conn:
        print("連線成功！")
        conn.close()
    else:
        print("連線失敗，請檢查 .env 設定。")