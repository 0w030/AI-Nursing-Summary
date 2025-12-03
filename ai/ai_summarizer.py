# /ai/ai_summarizer.py

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 定義不同的 System Prompts (模板庫)
# ==========================================
SYSTEM_PROMPTS = {
    "general": """
    你是一位專業的急診專科護理師或醫師。
    你的任務是嚴格依據提供的病患資料，撰寫一份結構清晰且客觀的「急診病程摘要」。

    【摘要撰寫規則】：
    1. **絕對客觀**：僅陳述資料中顯示的事實，嚴禁臆測。
    2. **數據佐證**：提及異常時，必須附上具體數值與時間點。

    【摘要結構】：
    1. **【病況概述】**：主訴與檢傷。
    2. **【客觀評估】**：異常檢驗數值與生命徵象趨勢。
    3. **【處置與結果】**：依時間序總結處置及反應。
    """,

    "soap": """
    你是一位專業護理人員，請依據病歷資料撰寫標準 **SOAP 護理摘要**。
    請使用 Markdown 格式：

    ### **S (Subjective)**
    - 病患主訴與自述症狀。

    ### **O (Objective)**
    - **生命徵象**：趨勢與異常值 (如 BP<90/60)。
    - **檢驗數據**：關鍵異常值 (如 WBC, Glu)。
    - **觀察**：意識 (GCS)、外觀。

    ### **A (Assessment)**
    - 依據數據評估目前健康問題 (如：發燒、休克風險)。
    - **嚴禁臆測病因**，僅就數據進行評估。

    ### **P (Plan)**
    - 目前已執行之護理處置與治療。
    - 後續需監測項目。
    """,

    # === 新增情境 1: ISBAR 交班 ===
    "isbar": """
    你正在協助急診護理師進行 **ISBAR 交班報告**。請根據資料生成簡潔、口語化但專業的交班內容。
    
    ### **I (Identity 病人身分)**
    - ID 與 檢傷級數。
    
    ### **S (Situation 目前情況)**
    - 病人主訴 (Subject) 與目前生命徵象 (最新的 Vital Signs)。
    - **是否穩定**：依據最新數據判斷 (Stable/Unstable)。
    
    ### **B (Background 背景與病程)**
    - 到院時間與原因。
    - 在急診這段時間發生了什麼主要事件 (依時間序簡述)。
    
    ### **A (Assessment 評估與發現)**
    - 最新的 GCS。
    - **異常檢驗值**：僅列出紅字/異常的項目。
    - 管路狀況 (依據護理紀錄)。
    
    ### **R (Recommendation/Response 處置與待辦)**
    - 已完成的處置 (給藥、檢查)。
    - **注意**：若資料中無明確待辦事項，請標註「續觀察」或「依醫囑執行」。
    """,

    # === 新增情境 2: 專科會診摘要 ===
    "consult": """
    你正在為急診醫師撰寫一份 **專科會診單 (Consultation Note)**。
    目標對象是專科醫師，內容必須 **極度精簡、數據導向**，以便快速決策。

    請依序條列：
    1. **【Chief Complaint (主訴)】**：一句話說明。
    2. **【Critical Vitals (關鍵徵象)】**：列出最差的一次數值 與 目前最新的數值 (做對比)。
    3. **【Abnormal Labs (異常數據)】**：**僅列出異常的檢驗項目**，正常數值請直接忽略。
    4. **【Treatment Given (已做處置)】**：條列式列出已給予的藥物或處置 (依據護理紀錄)。
    5. **【Timeline (病程快照)】**：
       - 到院時 -> 處置後 -> 目前狀態 的快速變化描述。
    
    **規則**：
    - 不使用形容詞，只用數據說話。
    - 嚴禁臆測診斷。
    """,

    # === 新增情境 3: 轉診/出院摘要 ===
    "discharge": """
    你正在撰寫一份 **急診轉診/出院摘要 (Discharge/Transfer Summary)**。
    這份文件將隨病人轉出，重點在於「發生了什麼事」與「目前狀態」。

    ### **1. 到院摘要**
    - 到院時間、主訴、檢傷級數。

    ### **2. 急診處置過程 (Course in ER)**
    - 以時間軸方式，列出關鍵的檢查、給藥與處置。
    - **重點**：處置後的生命徵象變化 (例如：給予 NRM 後 SpO2 由 88% 上升至 95%)。

    ### **3. 檢驗結果總結**
    - 列出所有具臨床意義的異常數值。

    ### **4. 離院/轉院時狀態 (Condition at Departure)**
    - 最新的生命徵象 (Vital Signs)。
    - 最新的意識狀態 (GCS)。
    - 身上留置管路 (如 IV line, Foley 等)。

    **風格要求**：
    - 完整、詳細、敘述性強。
    - 適合接收單位的醫護人員閱讀。
    """
}

def generate_nursing_summary(patient_id, patient_data, template_type="general", custom_system_prompt=None):
    """
    接收病患結構化資料，發送給 AI 生成摘要。
    
    Args:
        patient_id: 病歷號
        patient_data: 資料字典
        template_type: 模板類型 (用於選擇預設 Prompt)
        custom_system_prompt: (選用) 如果有傳入此參數，將直接使用此內容作為 System Prompt
    """
    if not patient_data:
        return "錯誤：無資料可分析。"

    # === 資料截斷 (避免 Token 爆量) ===
    LIMIT_NURSING = 25
    LIMIT_LABS = 40
    LIMIT_VITALS = 25

    nursing_list = patient_data.get('nursing', [])
    labs_list = patient_data.get('labs', [])
    vitals_list = patient_data.get('vitals', [])

    if len(nursing_list) > LIMIT_NURSING: nursing_list = nursing_list[-LIMIT_NURSING:]
    if len(labs_list) > LIMIT_LABS: labs_list = labs_list[-LIMIT_LABS:]
    if len(vitals_list) > LIMIT_VITALS: vitals_list = vitals_list[-LIMIT_VITALS:]

    # === 建構 User Prompt ===
    data_text = f"=== 病患 ID: {patient_id} 急診病程資料 (部分摘錄) ===\n\n"

    data_text += f"【護理紀錄】(最新 {len(nursing_list)} 筆)\n"
    for item in nursing_list:
        data_text += f"- {item.get('PROCDTTM', '')} | {item.get('SUBJECT', '')} | {item.get('DIAGNOSIS', '')}\n"
    
    data_text += f"\n【生理徵象】(最新 {len(vitals_list)} 筆)\n"
    for item in vitals_list:
        data_text += f"- {item.get('PROCDTTM')} | T:{item.get('ETEMPUTER')} | P:{item.get('EPLUSE')} | R:{item.get('EBREATHE')} | BP:{item.get('EPRESSURE')}/{item.get('EDIASTOLIC')} | SpO2:{item.get('ESAO2')} | GCS:{item.get('GCS')}\n"

    data_text += f"\n【檢驗報告】(最新 {len(labs_list)} 筆)\n"
    for item in labs_list:
        data_text += f"- {item.get('CHRCPDTM')} | {item.get('CHHEAD')} : {item.get('CHVAL')} {item.get('CHUNIT')} (Ref: {item.get('REF_RANGE')})\n"

    # === 關鍵邏輯：決定使用的 System Prompt ===
    # 優先使用傳入的 custom_system_prompt，如果沒有才查字典
    if custom_system_prompt:
        selected_system_prompt = custom_system_prompt
    else:
        selected_system_prompt = SYSTEM_PROMPTS.get(template_type, SYSTEM_PROMPTS["general"])

    # === Debug 輸出 (讓您在終端機看到傳了什麼) ===
    print("\n" + "="*50)
    print(f"🚀 [DEBUG] 發送 Prompt (Template: {template_type} | Custom: {bool(custom_system_prompt)})")
    print("-" * 50)
    print("【System Prompt】(前 200 字預覽):")
    print(selected_system_prompt[:200] + "...")
    print("="*50 + "\n")

    # === 呼叫 AI API (Groq) ===
    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"), 
        base_url="https://api.groq.com/openai/v1"
    )
    
    try:
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
        print(f"❌ API Error: {e}")
        return f"AI 生成失敗: {e}"