# /ai/ai_summarizer.py

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from data.metadata import get_chinese_name

load_dotenv()

# ==========================================
# 定義不同的 System Prompts (模板)
# ==========================================
SYSTEM_PROMPTS = {
    "general": """
    你是一位專業的急診專科護理師或醫師。
    你的任務是嚴格依據提供的病患資料（護理紀錄、生命徵象、檢驗數值），撰寫一份結構清晰且客觀的「急診病程摘要 (ER Summary)」。

    【摘要撰寫規則】：
    1. **絕對客觀**：僅陳述資料中顯示的事實。嚴禁進行診斷推測、臆測病因或撰寫資料中未提及的內容。
    2. **數據佐證**：提及異常時，必須附上具體數值與時間點。
    3. **用語專業**：使用台灣醫療慣用的繁體中文與英文術語 (如: GCS, SpO2, IV drip)。

    【摘要結構】：
    1. **【病況概述】**：整合主訴與檢傷狀態，簡述到院方式。
    2. **【客觀評估與重要發現】**：
       - 列出異常檢驗數值。
       - 指出生命徵象變化趨勢。
    3. **【處置與結果】**：依時間序總結處置（給藥、檢查、會診等）及反應。
    """,

    "soap": """
    你是一位專業護理人員，請依據提供的病歷資料，撰寫一份標準的 **SOAP 格式護理摘要**。
    
    請嚴格遵守以下格式進行輸出 (使用 Markdown)：

    ### **S (Subjective 主觀資料)**
    - 整合病患主訴 (Subject) 與感受。
    - 描述病患自述的不適症狀。

    ### **O (Objective 客觀資料)**
    - **生命徵象**：分析變化趨勢，特別標註異常值 (如 BP < 90/60, SpO2 < 95%)。
    - **檢驗/檢查**：列出關鍵異常數據 (如 WBC, Troponin-I, Glu 等)。
    - **護理觀察**：病患外觀、意識狀態 (GCS)、管路留置情況。
    - **I/O**：若有相關紀錄，描述輸入輸出平衡狀況。

    ### **A (Assessment 評估)**
    - 綜合上述資料，評估目前主要健康問題。
    - 分析數據變化的臨床意義 (例如：給藥後血壓回升)。
    - 潛在風險評估 (如：跌倒風險、感染風險)。

    ### **P (Plan 計劃)**
    - **持續護理**：目前的治療處置 (IV, Oxygen, Meds)。
    - **監測項目**：後續需密切觀察的指標 (如 SpO2, GCS)。
    - **預防措施**：如預防跌倒、管路照護衛教。

    ---
    **⚠️ 警示事項**
    - 列出最需要交班或特別注意的危急數值或異常狀況。

    **撰寫原則**：
    - 保持客觀、精確。
    - 僅根據提供的資料撰寫，不可臆測。
    - 重點標註異常數據 (使用粗體)。
    """
}

def generate_nursing_summary(patient_id, patient_data, template_type="general"):
    """
    接收病患的完整結構化資料，發送給 AI 生成摘要。
    
    Args:
        patient_id: 病歷號
        patient_data: 資料字典
        template_type: 摘要模板類型 ('general' 或 'soap')
    """
    if not patient_data:
        return "錯誤：無資料可分析。"

    # === 資料截斷邏輯 (避免 Token 爆量) ===
    LIMIT_NURSING = 20
    LIMIT_LABS = 30
    LIMIT_VITALS = 20

    nursing_list = patient_data.get('nursing', [])
    labs_list = patient_data.get('labs', [])
    vitals_list = patient_data.get('vitals', [])

    if len(nursing_list) > LIMIT_NURSING: nursing_list = nursing_list[-LIMIT_NURSING:]
    if len(labs_list) > LIMIT_LABS: labs_list = labs_list[-LIMIT_LABS:]
    if len(vitals_list) > LIMIT_VITALS: vitals_list = vitals_list[-LIMIT_VITALS:]

    # === 建構 User Prompt (資料內容) ===
    data_text = f"=== 病患 ID: {patient_id} 急診病程資料 (部分摘錄) ===\n\n"

    data_text += f"【護理紀錄 / 主訴】(最新 {len(nursing_list)} 筆)\n"
    for item in nursing_list:
        data_text += f"- 時間: {item.get('PROCDTTM', 'NA')}\n"
        data_text += f"  主訴: {item.get('SUBJECT', 'NA')}\n"
        data_text += f"  診斷: {item.get('DIAGNOSIS', 'NA')}\n"
    
    data_text += f"\n【生理徵象】(最新 {len(vitals_list)} 筆)\n"
    for item in vitals_list:
        data_text += f"- 時間: {item.get('PROCDTTM')} | "
        data_text += f"體溫: {item.get('ETEMPUTER')} | 脈搏: {item.get('EPLUSE')} | "
        data_text += f"BP: {item.get('EPRESSURE')}/{item.get('EDIASTOLIC')} | SpO2: {item.get('ESAO2')} | GCS: {item.get('GCS')}\n"

    data_text += f"\n【檢驗報告】(最新 {len(labs_list)} 筆)\n"
    for item in labs_list:
        data_text += f"- 時間: {item.get('CHRCPDTM')} | 項目: {item.get('CHHEAD')} | 數值: {item.get('CHVAL')} {item.get('CHUNIT')} (參考: {item.get('REF_RANGE')})\n"

    # === 選擇 System Prompt ===
    # 如果找不到對應的 key，預設使用 'general'
    selected_system_prompt = SYSTEM_PROMPTS.get(template_type, SYSTEM_PROMPTS["general"])

    # ==========================================================
    # 🔍 [DEBUG] 這裡會把傳給 AI 的內容印在終端機
    # ==========================================================
    print("\n" + "="*50)
    print(f"🚀 [DEBUG] 正在發送給 Groq API 的資料 (Template: {template_type})")
    print("-" * 50)
    print("【System Prompt (AI 的角色設定)】:")
    print(selected_system_prompt)
    print("-" * 50)
    print("【User Prompt (餵給 AI 的病歷資料)】:")
    print(data_text)
    print("="*50 + "\n")
    # ==========================================================

    # === 呼叫 AI API (Groq) ===
    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"), 
        base_url="https://api.groq.com/openai/v1"
    )
    
    try:
        # print(f"--- 呼叫 Groq AI (Template: {template_type}) ---") # 已由上方 DEBUG 取代
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": selected_system_prompt},
                {"role": "user", "content": data_text}
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ API 錯誤: {e}") # 增加錯誤列印
        return f"AI 生成失敗: {e}"