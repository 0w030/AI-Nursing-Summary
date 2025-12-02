# /ai/ai_summarizer.py

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from data.metadata import get_chinese_name

load_dotenv()

def generate_nursing_summary(patient_id, patient_data):
    """
    接收病患的完整結構化資料，發送給 OpenAI 生成護理摘要。
    """
    if not patient_data:
        return "錯誤：無資料可分析。"

    # 1. 建構 Prompt 內容
    # 將 Python 字典轉換成易讀的文字格式
    
    data_text = f"=== 病患 ID: {patient_id} 急診病程資料 ===\n\n"

    # A. 護理紀錄
    data_text += "【護理紀錄 / 主訴】\n"
    for item in patient_data.get('nursing', []):
        data_text += f"- 時間: {item['PROCDTTM']}\n"
        data_text += f"  主訴: {item['SUBJECT']}\n"
        data_text += f"  診斷: {item['DIAGNOSIS']}\n"
    
    # B. 生理監測
    data_text += "\n【生理徵象 (Vital Signs)】\n"
    for item in patient_data.get('vitals', []):
        data_text += f"- 時間: {item['PROCDTTM']} | "
        # 使用 metadata 翻譯欄位名稱 (這裡示範手動組裝，比較簡潔)
        data_text += f"體溫: {item['ETEMPUTER']} | 脈搏: {item['EPLUSE']} | "
        data_text += f"BP: {item['EPRESSURE']}/{item['EDIASTOLIC']} | SpO2: {item['ESAO2']} | GCS: {item['GCS']}\n"

    # C. 檢驗報告
    data_text += "\n【檢驗報告 (Lab Data)】\n"
    for item in patient_data.get('labs', []):
        data_text += f"- 時間: {item['CHRCPDTM']} | 項目: {item['CHHEAD']} | 數值: {item['CHVAL']} {item['CHUNIT']} (參考: {item['REF_RANGE']})\n"

    # 2. 設定 System Prompt (AI 的角色與任務)
    system_prompt = """
    你是一位專業的急診專科護理師或醫師。
    你的任務是閱讀該病患在急診的完整病程資料（包含護理紀錄、生命徵象、檢驗數值），
    並撰寫一份結構清晰的「急診病程摘要 (ER Summary)」。

    摘要要求：
    1. 【病況概述】：簡述病人主訴及檢傷狀況。
    2. 【重要發現】：
       - 指出生命徵象的異常趨勢（例如：血壓是否持續下降、有無發燒）。
       - 標記關鍵的異常檢驗數值（例如：WBC過高、肌酸酐異常），並解讀其臨床意義。
    3. 【處置與結果】：根據護理紀錄，總結病人接受了哪些處置，以及病情的後續變化。
    4. 語氣專業、客觀，使用台灣醫療慣用術語。
    """

    # 3. 呼叫 AI API (修改為 Groq)
    # 使用 OpenAI SDK，但指向 Groq 的伺服器地址
    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"), 
        base_url="https://api.groq.com/openai/v1"
    )
    
    try:
        print("--- 正在呼叫 Groq AI (Llama 3) 生成摘要... ---")
        response = client.chat.completions.create(
            # 指定 Groq 支援的模型名稱 (Llama 3.3 70B 是目前最強的免費開源模型)
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data_text}
            ],
            temperature=0.3, # 低溫，保持客觀
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 生成失敗: {e}"