# app.py

import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, time

# 引入後端模組
from db.patient_service import get_patient_full_history, get_all_patients_overview
from db.template_service import get_all_templates, create_template, update_template
from ai.ai_summarizer import generate_nursing_summary

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
    
    patients_list = load_patient_list()
    
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

    # 2. 選擇模板 (從資料庫動態讀取)
    st.subheader("2. 選擇摘要模板")
    # 每次重新執行都去資料庫抓最新的模板
    db_templates = get_all_templates() 
    template_names = list(db_templates.keys())
    
    if not template_names:
        st.error("資料庫中沒有模板，請先切換到「模板設計師」建立模板！")
        st.stop()
        
    selected_template_name = st.selectbox("請選擇適用情境：", template_names, index=0)
    
    # 3. 呈現風格
    style_option = st.radio("呈現風格：", ["列點式 (Bullet Points)", "短文式 (Narrative)"], horizontal=True)

    # 4. 關注點 (修改為 Checkbox 清單)
    st.subheader("3. 重點關注項目")
    st.write("勾選 AI 加強分析點：")
    
    focus_options = ["生命徵象趨勢", "檢驗報告異常值", "護理處置經過", "病患主訴", "管路狀況", "意識狀態(GCS)"]
    selected_focus_areas = []
    
    # 使用迴圈產生 Checkbox
    # 這裡可以根據 selected_template_name 來決定 default 是否勾選 (進階功能)
    # 目前先預設不勾選，讓使用者自己點
    for option in focus_options:
        if st.checkbox(option):
            selected_focus_areas.append(option)

    # 5. 時間篩選 (簡化版)
    with st.expander("⏳ 時間範圍篩選 (選填)"):
        use_time_filter = st.checkbox("啟用篩選")
        start_dt_str = None
        end_dt_str = None
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
                # 撈資料
                p_data = get_patient_full_history(target_patient_id, start_time=start_dt_str)
                
                # 準備 Prompt 附加指令
                style_instruction = ""
                if style_option == "短文式 (Narrative)":
                    style_instruction = "\n\n**【格式要求】**：請整合為一篇流暢的短文，禁止使用列點。"
                else:
                    style_instruction = "\n\n**【格式要求】**：請務必使用列點方式呈現，保持條理。"
                
                # 從資料庫取出原始模板內容
                base_prompt = db_templates[selected_template_name]
                
                # 組合最終 Prompt
                final_system_prompt = base_prompt + style_instruction

                # 呼叫 AI
                summary = generate_nursing_summary(
                    target_patient_id, 
                    p_data, 
                    selected_template_name, # 這裡傳名稱主要為了 Debug，實際內容看 custom_system_prompt
                    custom_system_prompt=final_system_prompt,
                    focus_areas=selected_focus_areas
                )
                
                st.markdown("### 📋 生成結果")
                st.markdown("---")
                st.markdown(summary)

# ==============================================================================
# 模式 B：模板設計師 (管理後台)
# ==============================================================================
elif app_mode == "🎨 模板設計師":
    st.header("🎨 AI 模板設計中心")
    st.info("在此模式下，您可以新增或修改 AI 的思考邏輯 (Prompt)，客製化不同科別的需求。")

    # 1. 讀取現有模板
    db_templates = get_all_templates()
    template_list = list(db_templates.keys())

    tab_edit, tab_create = st.tabs(["✏️ 修改現有模板", "➕ 建立新模板"])

    # --- Tab 1: 修改 ---
    with tab_edit:
        if not template_list:
            st.warning("目前沒有任何模板。")
        else:
            edit_target = st.selectbox("選擇要修改的模板：", template_list)
            
            # 讀取該模板內容
            current_content = db_templates[edit_target]
            
            with st.form("edit_form"):
                st.write(f"正在編輯：**{edit_target}**")
                new_content = st.text_area("模板內容 (System Prompt)", value=current_content, height=400)
                
                if st.form_submit_button("💾 儲存修改"):
                    if update_template(edit_target, new_content):
                        st.success(f"模板「{edit_target}」已更新！")
                        st.cache_data.clear() # 清除快取以顯示最新內容
                        st.rerun() # 重新整理頁面
                    else:
                        st.error("更新失敗，請檢查資料庫連線。")

    # --- Tab 2: 新增 ---
    with tab_create:
        with st.form("create_form"):
            new_name = st.text_input("新模板名稱 (例如：骨科術後摘要)")
            new_desc = st.text_input("模板說明 (選填)")
            new_content = st.text_area("模板內容 (System Prompt)", height=300, placeholder="你是一位專業的...")
            
            if st.form_submit_button("✨ 建立模板"):
                if new_name and new_content:
                    if create_template(new_name, new_content, new_desc):
                        st.success(f"模板「{new_name}」建立成功！")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("建立失敗 (名稱可能重複)。")
                else:
                    st.warning("名稱與內容不得為空。")