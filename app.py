# app.py

import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, time

# 引入後端模組
from db.patient_service import get_patient_full_history, get_all_patients_overview
from ai.ai_summarizer import generate_nursing_summary

# --- 設定網頁 ---
st.set_page_config(page_title="AI 急診護理摘要系統", layout="wide", page_icon="🚑")

# ==========================================
# 輔助函數
# ==========================================
def format_time_str(raw_time):
    if not raw_time or len(str(raw_time)) < 12: return raw_time
    s = str(raw_time)
    return f"{s[:4]}-{s[4:6]}-{s[6:8]} {s[8:10]}:{s[10:12]}"

# ==========================================
# 1. 載入資料庫現有病患 (快取)
# ==========================================
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
# 2. 介面佈局
# ==========================================
st.title("🏥 AI 急診病程摘要生成系統")

# --- 頂部：選擇區塊 ---
st.markdown("### 1️⃣ 選擇病患")

options = ["請選擇..."] + [p['label'] for p in patients_list]
selected_label = st.selectbox("請從清單中選擇一位病患：", options, index=0)

target_patient_id = None
selected_info = None

if selected_label != "請選擇...":
    selected_info = next((p for p in patients_list if p['label'] == selected_label), None)
    if selected_info:
        target_patient_id = selected_info['病歷號']

# --- 中間：顯示完整清單 ---
with st.expander("📊 查看資料庫完整病患清單 (點擊展開/收合)", expanded=(target_patient_id is None)):
    if patients_list:
        df_display = pd.DataFrame(patients_list)[['病歷號', '最早紀錄_顯示', '最晚紀錄_顯示', '資料筆數']]
        df_display.columns = ['病歷號', '最早就診時間', '最後紀錄時間', '資料筆數']
        st.dataframe(
            df_display, use_container_width=True, hide_index=True,
            column_config={"資料筆數": st.column_config.ProgressColumn("資料量", format="%d", min_value=0, max_value=max(p['資料筆數'] for p in patients_list))}
        )
    else:
        st.warning("資料庫中目前沒有資料。")

# ==========================================
# 3. 側邊欄：進階設定
# ==========================================
with st.sidebar:
    st.header("⚙️ 進階設定")
    
    if selected_info:
        info_text = (
            f"**已選擇：{target_patient_id}**\n\n"
            f"📅 **最早紀錄：** {selected_info['最早紀錄_顯示']}\n\n"
            f"🕒 **最晚紀錄：** {selected_info['最晚紀錄_顯示']}"
        )
        st.success(info_text)
    
    st.divider()

    # === 新增功能：選擇摘要格式 ===
    st.subheader("📝 摘要格式")
    template_option = st.radio(
        "請選擇生成模板：",
        ["一般摘要 (General)", "SOAP 護理記錄"],
        index=0
    )
    # 將選項轉換為後端代碼
    template_map = {
        "一般摘要 (General)": "general",
        "SOAP 護理記錄": "soap"
    }
    selected_template = template_map[template_option]
    # ==========================
    
    st.divider()
    
    st.subheader("⏳ 時間篩選")
    use_time_filter = st.checkbox("啟用時間篩選", value=False)
    start_dt_str = None
    end_dt_str = None
    
    if use_time_filter:
        default_d1 = datetime.now().date()
        default_t1 = time(0, 0)
        default_d2 = datetime.now().date()
        default_t2 = time(23, 59)

        if selected_info:
            try:
                if selected_info['最早紀錄']:
                    dt_start = datetime.strptime(str(selected_info['最早紀錄']), "%Y%m%d%H%M%S")
                    default_d1 = dt_start.date()
                    default_t1 = dt_start.time().replace(minute=0, second=0)
                if selected_info['最晚紀錄']:
                    dt_end = datetime.strptime(str(selected_info['最晚紀錄']), "%Y%m%d%H%M%S")
                    default_d2 = dt_end.date()
                    default_t2 = dt_end.time() 
            except: pass

        st.markdown("**起始時間**")
        c1, c2 = st.columns(2)
        with c1: d1 = st.date_input("開始日期", default_d1)
        with c2: t1 = st.time_input("開始時間", default_t1)
        
        st.markdown("**結束時間**")
        c3, c4 = st.columns(2)
        with c3: d2 = st.date_input("結束日期", default_d2)
        with c4: t2 = st.time_input("結束時間", default_t2)
        
        start_dt_str = f"{d1.year}{d1.month:02d}{d1.day:02d}{t1.hour:02d}{t1.minute:02d}00"
        end_dt_str = f"{d2.year}{d2.month:02d}{d2.day:02d}{t2.hour:02d}{t2.minute:02d}59"

# ==========================================
# 4. 底部：執行與結果顯示
# ==========================================

if target_patient_id:
    st.markdown("### 2️⃣ 生成摘要")
    
    btn_label = f"🚀 開始分析：{target_patient_id}"
    if use_time_filter:
        btn_label += f" (篩選時間)"
        
    run_btn = st.button(btn_label, type="primary", use_container_width=True)

    if run_btn:
        load_dotenv()
        api_ready = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_ready:
            st.error("❌ 未偵測到 API Key (Groq/OpenAI)，請檢查 .env 檔案！")
            st.stop()

        status_box = st.status(f"🔍 正在撈取病患資料...", expanded=True)
        
        # 1. 撈取資料
        patient_data = get_patient_full_history(
            target_patient_id, 
            start_time=start_dt_str, 
            end_time=end_dt_str
        )

        if not patient_data or (len(patient_data['nursing']) + len(patient_data['vitals']) + len(patient_data['labs']) == 0):
            status_box.update(label="❌ 查無資料", state="error")
            st.error("該時段無資料，請調整篩選條件。")
        else:
            n_c = len(patient_data['nursing'])
            v_c = len(patient_data['vitals'])
            l_c = len(patient_data['labs'])
            status_box.write(f"✅ 資料撈取成功 (護理:{n_c}, 生理:{v_c}, 檢驗:{l_c})")
            
            # 顯示正在使用的模板
            status_box.write(f"🤖 正在使用 **{template_option}** 模板撰寫摘要...")
            
            # 2. 生成摘要 (傳入 template_type)
            summary = generate_nursing_summary(
                target_patient_id, 
                patient_data, 
                template_type=selected_template # <--- 關鍵參數
            )
            status_box.update(label="✅ 分析完成！", state="complete", expanded=False)

            # 3. 顯示結果
            tab1, tab2, tab3 = st.tabs(["📝 AI 生成摘要", "📂 原始數據預覽", "📈 生命徵象趨勢"])

            with tab1:
                st.markdown(f"### 📋 {template_option}")
                st.markdown("---")
                st.markdown(summary)
                st.download_button("📥 下載摘要", summary, f"summary_{target_patient_id}.txt")

            with tab2:
                st.info("以下顯示本次分析所使用的原始資料。")
                st.subheader(f"🩺 護理紀錄 ({n_c} 筆)")
                st.dataframe(patient_data['nursing'], use_container_width=True)
                st.divider()
                c_a, c_b = st.columns(2)
                with c_a:
                    st.subheader(f"💓 生理監測 ({v_c} 筆)")
                    st.dataframe(patient_data['vitals'], use_container_width=True)
                with c_b:
                    st.subheader(f"🧪 檢驗報告 ({l_c} 筆)")
                    st.dataframe(patient_data['labs'], use_container_width=True)

            with tab3:
                if v_c > 0:
                    try:
                        df_vitals = pd.DataFrame(patient_data['vitals'])
                        if 'PROCDTTM' in df_vitals.columns:
                            df_vitals['Time'] = pd.to_datetime(df_vitals['PROCDTTM'], format='%Y%m%d%H%M%S', errors='coerce')
                            df_vitals = df_vitals.dropna(subset=['Time']).set_index('Time')
                            
                            cols_to_plot = []
                            for col in ['EPLUSE', 'ESAO2', 'ETEMPUTER']:
                                if col in df_vitals.columns:
                                    df_vitals[col] = pd.to_numeric(df_vitals[col], errors='coerce')
                                    cols_to_plot.append(col)
                            
                            if cols_to_plot:
                                st.line_chart(df_vitals[cols_to_plot])
                            else:
                                st.info("無可繪製的數值資料。")
                    except: st.warning("繪圖錯誤")
                else:
                    st.info("無生理監測資料。")

else:
    st.info("👆 請先在上方選單選擇一位病患。")
    