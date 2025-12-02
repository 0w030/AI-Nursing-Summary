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
    你的任務是嚴格依據提供的病患資料（護理紀錄、生命徵象、檢驗數值），撰寫一份結構清晰且客觀的「急診病程摘要 (ER Summary)」。

    【摘要撰寫規則】：
    1. **絕對客觀**：僅陳述資料中顯示的事實。嚴禁進行診斷推測、臆測病因或撰寫資料中未提及的內容。
    2. **數據佐證**：提及異常時，必須附上具體數值與時間點。
    3. **用語專業**：使用台灣醫療慣用的繁體中文與英文術語 (如: GCS, SpO2, IV drip)。

    【摘要結構】：
    1. **【病況概述】**：
       - 整合「護理紀錄」中的主訴 (Subject) 與檢傷時的狀態。
       - 簡述病人是如何到院的（如：119送入、自行步入）。

    2. **【客觀評估與重要發現】**：
       - 檢視「檢驗報告」：列出數值異常（過高/過低）的項目及其數值。若數值正常則簡述為「無明顯異常」。
       - 檢視「生命徵象」：指出生命徵象的變化趨勢（例如：血壓由 80/50 回升至 110/70，或持續發燒中）。
       - **注意**：僅列出異常發現，不要解釋其成因（除非護理紀錄中有醫師確診紀錄）。

    3. **【處置與結果】**：
       - 依據「護理紀錄」的時間序，總結病人接受了哪些具體處置（如：給藥、檢查、會診、留置導尿管等）。
       - 描述處置後的反應或處置當下的病人狀態。
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