# /data/data_processor.py

import json
from datetime import datetime
from db.db_connector import get_db_connection

# 模擬的結構化檢查報告數據
MOCK_REPORTS_DATA = [
    {
        "patient_id": "P001",
        "examination_date": "2024-10-15",
        "report_type": "血液常規",
        "structured_data_json": {
            "WBC": 15.2, "RBC": 4.2, "Hb": 12.0, "備註": "白血球明顯偏高，可能為急性感染。"
        }
    },
    {
        "patient_id": "P001",
        "examination_date": "2024-10-22",
        "report_type": "血液常規",
        "structured_data_json": {
            "WBC": 10.1, "RBC": 4.1, "Hb": 11.8, "備註": "白血球下降，抗生素治療有效。"
        }
    },
    {
        "patient_id": "P001",
        "examination_date": "2024-11-05",
        "report_type": "生化檢查",
        "structured_data_json": {
            "Liver_Enzyme": 35, "Kidney_Function": 0.9, "Glucose": 95, "備註": "所有生化指標均正常。"
        }
    }
]

def insert_mock_data():
    """將模擬資料插入到 examination_reports 資料表中"""
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            for data in MOCK_REPORTS_DATA:
                # 插入資料
                query = sql.SQL("""
                    INSERT INTO examination_reports 
                    (patient_id, examination_date, report_type, structured_data)
                    VALUES (%s, %s, %s, %s);
                """)
                
                # 將 Python 字典轉換為 JSON 字串，以便 PostgreSQL 的 JSONB 欄位接受
                json_data = json.dumps(data["structured_data_json"])
                
                cur.execute(query, (
                    data["patient_id"],
                    data["examination_date"],
                    data["report_type"],
                    json_data
                ))
        
        conn.commit()
        print(f"成功插入 {len(MOCK_REPORTS_DATA)} 筆模擬報告數據。")
        
    except psycopg2.Error as e:
        print(f"插入模擬數據失敗: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    # 測試插入模擬數據
    insert_mock_data()