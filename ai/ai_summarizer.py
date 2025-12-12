# /ai/ai_summarizer.py

import os
from openai import OpenAI
from dotenv import load_dotenv
# 引入剛剛寫好的模板服務
from db.template_service import get_all_templates

load_dotenv()

def generate_nursing_summary(patient_id, patient_data, template_name, custom_system_prompt=None, focus_areas=None):
    """
    接收病患結構化資料，發送給 AI 生成摘要。
    
    Args:
        patient_id: 病歷號
        patient_data: 資料字典
        template_name: 模板名稱 (對應資料庫中的 template_name)
        custom_system_prompt: (選用) 自定義 Prompt (優先權最高)
        focus_areas: list of str，使用者指定的重點關注項目
    """
    if not patient_data:
        return "錯誤：無資料可分析。"

    # === 1. 從資料庫獲取所有模板 ===
    # 這取代了原本寫死的 SYSTEM_PROMPTS 字典
    db_templates = get_all_templates()
    
    # 確保有模板可用 (若資料庫連線失敗或無資料，使用備用預設值)
    if not db_templates:
        base_system_prompt = "你是專業醫療人員，請撰寫病程摘要。"
        print("⚠️ 警告：無法從資料庫讀取模板，使用預設值。")
    else:
        # 嘗試根據名稱獲取內容，若找不到則預設用第一個抓到的
        base_system_prompt = db_templates.get(template_name)
        if not base_system_prompt:
            # 如果指定的名稱找不到，就隨便抓一個當備用
            base_system_prompt = next(iter(db_templates.values()))

    # === 2. 決定最終使用的 System Prompt ===
    # 優先順序：使用者手動編輯 > 資料庫模板
    if custom_system_prompt:
        selected_system_prompt = custom_system_prompt
    else:
        selected_system_prompt = base_system_prompt

    # === 3. 加入關注項目 (Focus Areas) ===
    if focus_areas and len(focus_areas) > 0:
        focus_instruction = f"""
        
**【⚠️ 特別指令：重點關注項目】**
使用者要求你特別詳細分析以下面向，請務必在摘要中包含相關細節，並將其優先呈現：
- {", ".join(focus_areas)}
        """
        selected_system_prompt += focus_instruction

    # === 4. 資料截斷 (避免 Token 爆量) ===
    LIMIT_NURSING = 25
    LIMIT_LABS = 40
    LIMIT_VITALS = 25

    nursing_list = patient_data.get('nursing', [])
    labs_list = patient_data.get('labs', [])
    vitals_list = patient_data.get('vitals', [])

    if len(nursing_list) > LIMIT_NURSING: nursing_list = nursing_list[-LIMIT_NURSING:]
    if len(labs_list) > LIMIT_LABS: labs_list = labs_list[-LIMIT_LABS:]
    if len(vitals_list) > LIMIT_VITALS: vitals_list = vitals_list[-LIMIT_VITALS:]

    # === 5. 建構 User Prompt (資料內容) ===
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

    # === Debug 輸出 ===
    print("\n" + "="*50)
    print(f"🚀 [DEBUG] Template: {template_name} | Custom: {bool(custom_system_prompt)}")
    print("-" * 50)
    print(selected_system_prompt[-500:]) 
    print("="*50 + "\n")

    # === 6. 呼叫 AI API (Groq) ===
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