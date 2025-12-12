# app.py

import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, time

# 引入後端模組
from db.patient_service import get_patient_full_history, get_all_patients_overview
from db.template_service import get_all_templates, create_template, update_template
from ai.ai_summarizer import generate_nursing_summary, SYSTEM_PROMPTS

# --- 設定網頁 ---
st.set_page_config(page_title="AI 醫療模板系統", layout="wide", page_icon="🏥")

# ==========================================
# 輔助函數
# ==========================================
def format_time_str(raw_time):
    if not raw_time or len(str(raw_time)) < 12: return raw_time
    s = str(raw_time)
    return f"{s[:4]}-{s[4:6]}-{s[6:8]} {s[8:10]}:{s[10:12]}"

@st.cache_data(ttl=60)
def load_patient_list():
    raw_list = get_all_patients_overview()
    for p in raw_list:
        p['最早紀錄_顯示'] = format_time_str(p['最早紀錄'])
        p['最晚紀錄_顯示'] = format_time_str(p['最晚紀錄'])
        p['label'] = f"{p['病歷號']} (共 {p['資料筆數']} 筆資料)"
    return raw_list

patients_list = load_patient_list()

# ==========================================
# 側邊欄：全域導航
# ==========================================
with st.sidebar:
    st.title("🏥 醫療摘要系統")
    app_mode = st.radio("請選擇功能模式：", ["🚀 摘要生成器", "🎨 模板設計師"], index=0)
    st.divider()

# ==============================================================================
# 模式 A：摘要生成器 (使用者模式)
# ==============================================================================
if app_mode == "🚀 摘要生成器":
    st.header("🚀 AI 急診病程摘要生成")
    
    # 1. 選擇病患
    st.subheader("1. 選擇病患")
    options = ["請選擇..."] + [p['label'] for p in patients_list]
    selected_label = st.selectbox("病患清單：", options, index=0)
    
    target_patient_id = None
    selected_info = None
    if selected_label != "請選擇...":
        selected_info = next((p for p in patients_list if p['label'] == selected_label), None)
        target_patient_id = selected_info['病歷號']
        st.success(f"已選定：{target_patient_id}")

    # 2. 選擇模板
    st.subheader("2. 選擇摘要模板")
    db_templates = get_all_templates() 
    template_names = list(db_templates.keys())
    
    if not template_names:
        st.error("資料庫中沒有模板，請先切換到「模板設計師」建立模板！")
        st.stop()
        
    selected_template_name = st.selectbox("請選擇適用情境：", template_names, index=0)
    
    # 3. 呈現風格
    style_option = st.radio("呈現風格：", ["列點式 (Bullet Points)", "短文式 (Narrative)"], horizontal=True)

    # 4. 關注點
    st.subheader("3. 重點關注項目")
    focus_options = ["生命徵象趨勢", "檢驗報告異常值", "護理處置經過", "病患主訴", "管路狀況", "意識狀態(GCS)"]
    selected_focus_areas = []
    st.write("勾選 AI 加強分析點：")
    for option in focus_options:
        if st.checkbox(option):
            selected_focus_areas.append(option)

    # 5. 時間篩選
    with st.expander("⏳ 時間範圍篩選 (選填)"):
        use_time_filter = st.checkbox("啟用篩選")
        start_dt_str = None
        if use_time_filter:
            c1, c2 = st.columns(2)
            d1 = c1.date_input("開始日期", datetime.now())
            t1 = c2.time_input("開始時間", time(0,0))
            start_dt_str = f"{d1.year}{d1.month:02d}{d1.day:02d}{t1.hour:02d}{t1.minute:02d}00"

    # 6. 執行按鈕
    if target_patient_id:
        if st.button("✨ 開始生成摘要", type="primary", use_container_width=True):
            load_dotenv()
            if not os.getenv("GROQ_API_KEY"):
                st.error("未設定 API Key")
                st.stop()
                
            with st.spinner("正在分析資料並撰寫摘要..."):
                p_data = get_patient_full_history(target_patient_id, start_time=start_dt_str)
                
                style_instruction = ""
                if style_option == "短文式 (Narrative)":
                    style_instruction = "\n\n**【格式要求】**：請整合為一篇流暢的短文，禁止使用列點。"
                else:
                    style_instruction = "\n\n**【格式要求】**：請務必使用列點方式呈現，保持條理。"
                
                base_prompt = db_templates[selected_template_name]
                final_system_prompt = base_prompt + style_instruction

                summary = generate_nursing_summary(
                    target_patient_id, 
                    p_data, 
                    selected_template_name,
                    custom_system_prompt=final_system_prompt,
                    focus_areas=selected_focus_areas
                )
                
                st.markdown("### 📋 生成結果")
                st.markdown("---")
                st.markdown(summary)

# ==============================================================================
# 模式 B：模板設計師 (功能增強版)
# ==============================================================================
elif app_mode == "🎨 模板設計師":
    st.header("🎨 AI 模板設計中心")
    st.info("您可以透過下方的「Prompt 產生器」快速建立專業模板，或直接手動編輯。")

    db_templates = get_all_templates()
    template_list = list(db_templates.keys())

    tab_edit, tab_create = st.tabs(["✏️ 修改現有模板", "➕ 建立新模板"])

    # --- Tab 1: 修改 (保持不變) ---
    with tab_edit:
        if not template_list:
            st.warning("目前沒有任何模板。")
        else:
            edit_target = st.selectbox("選擇要修改的模板：", template_list)
            current_content = db_templates[edit_target]
            with st.form("edit_form"):
                st.write(f"正在編輯：**{edit_target}**")
                new_content = st.text_area("模板內容 (System Prompt)", value=current_content, height=400)
                if st.form_submit_button("💾 儲存修改"):
                    if update_template(edit_target, new_content):
                        st.success(f"模板「{edit_target}」已更新！")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("更新失敗。")

    # --- Tab 2: 新增 (新增 Prompt 產生器) ---
    with tab_create:
        
        st.markdown("#### 🛠️ Prompt 快速產生器")
        st.caption("選擇以下參數，自動生成專業的 System Prompt 草稿。")
        
        c1, c2, c3 = st.columns(3)
        
        # 1. 角色選擇
        role_type = c1.selectbox(
            "1. 設定角色視角", 
            ["急診專科醫師", "專業護理師", "專科護理師 (NP)", "個案管理師"]
        )
        
        # 2. 情境選擇
        scenario_type = c2.selectbox(
            "2. 設定使用情境", 
            ["急診轉住院", "急診出院/轉院", "交班報告 (ISBAR)", "專科會診", "一般病程回顧"]
        )
        
        # 3. 格式選擇
        format_type = c3.selectbox(
            "3. 設定輸出結構", 
            ["SOAP 格式", "ISBAR 格式", "條列式重點", "時間軸敘述"]
        )
        
        # 自動生成按鈕
        if st.button("⚡ 自動生成 Prompt 草稿"):
            # === 自動組裝 Prompt 邏輯 ===
            
            # A. 角色定義
            role_text = f"你是一位專業的{role_type}。"
            
            # B. 情境定義
            scenario_text = ""
            if scenario_type == "急診轉住院":
                scenario_text = "這份摘要將用於**急診轉住院**交接。請重點說明急診處置經過、目前生命徵象穩定度，以及後續住院需注意的檢查數值。"
            elif scenario_type == "急診出院/轉院":
                scenario_text = "這份摘要將作為**出院/轉院紀錄**。請總結病程、關鍵檢驗結果與離院時的狀態，供接收單位或家屬參考。"
            elif scenario_type == "交班報告 (ISBAR)":
                scenario_text = "這份摘要將用於**護理交班**。請著重於目前的病患狀況 (Status) 與待辦事項 (Pending Actions)。"
            elif scenario_type == "專科會診":
                scenario_text = "這份摘要將提供給**專科醫師會診**使用。內容必須極度精簡、數據導向，突顯異常數值以利快速決策。"
            else:
                scenario_text = "請根據提供的病患資料，撰寫一份結構清晰且客觀的病程摘要。"

            # C. 格式定義
            format_text = ""
            if format_type == "SOAP 格式":
                format_text = """
請嚴格遵守 **SOAP** 格式輸出：
### **S (Subjective)**: 病患主訴與自述症狀。
### **O (Objective)**: 生命徵象趨勢、異常檢驗數據、客觀觀察。
### **A (Assessment)**: 健康問題評估 (嚴禁臆測)。
### **P (Plan)**: 治療處置與後續計畫。"""
            elif format_type == "ISBAR 格式":
                format_text = """
請使用 **ISBAR** 格式輸出：
### **I (Identity)**: 身分與檢傷。
### **S (Situation)**: 目前主訴與狀況。
### **B (Background)**: 病史與到院經過。
### **A (Assessment)**: 評估與異常發現。
### **R (Recommendation)**: 處置與建議。"""
            else:
                format_text = """
請使用清晰的**條列式結構**，包含：
1. **【病況概述】**
2. **【重要檢查發現】** (標註異常值)
3. **【處置經過】**
4. **【目前狀態】**"""

            # D. 通用規則
            rules_text = """
**【撰寫規則】**：
1. **絕對客觀**：僅陳述資料中顯示的事實，嚴禁進行無根據的診斷推測。
2. **數據佐證**：提及異常時，必須附上具體數值。
3. **專業用語**：使用台灣醫療慣用的繁體中文與英文術語。"""

            # 組合
            full_draft = f"{role_text}\n{scenario_text}\n{format_text}\n{rules_text}"
            
            # 存入 session_state 以便填入下方的 text_area
            st.session_state.new_template_draft = full_draft
            st.success("草稿已生成！請在下方進行微調後儲存。")

        st.divider()

        # 儲存表單
        with st.form("create_form"):
            new_name = st.text_input("新模板名稱 (例如：心臟科會診摘要)")
            new_desc = st.text_input("模板說明 (選填)")
            
            # 讀取剛剛生成的草稿 (如果有的話)
            default_content = st.session_state.get("new_template_draft", "")
            
            new_content = st.text_area(
                "模板內容 (System Prompt) - 可在此手動微調", 
                value=default_content, 
                height=350,
                placeholder="請先點擊上方「⚡ 自動生成 Prompt 草稿」按鈕..."
            )
            
            if st.form_submit_button("💾 儲存新模板"):
                if new_name and new_content:
                    if create_template(new_name, new_content, new_desc):
                        st.success(f"模板「{new_name}」建立成功！")
                        st.cache_data.clear()
                        # 清除草稿
                        if "new_template_draft" in st.session_state:
                            del st.session_state.new_template_draft
                        st.rerun()
                    else:
                        st.error("建立失敗 (名稱可能重複)。")
                else:
                    st.warning("名稱與內容不得為空。")