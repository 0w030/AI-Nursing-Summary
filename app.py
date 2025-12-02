# app.py

import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

# 引入後端模組
from db.patient_service import get_patient_full_history, get_all_patients_overview
from ai.ai_summarizer import generate_nursing_summary

# --- 設定網頁 ---
st.set_page_config(page_title="AI 急診護理摘要系統", layout="wide", page_icon="🚑")

# ==========================================
# 輔助函數：時間格式美化
# ==========================================
def format_time_str(raw_time):
    """
    將資料庫原始時間字串 (YYYYMMDDHHMMSS) 轉為易讀格式 (YYYY-MM-DD HH:MM)
    """
    if not raw_time or len(str(raw_time)) < 12:
        return raw_time # 如果格式不對，就回傳原值
    
    s = str(raw_time)
    # 格式化為: 2025-11-15 15:30
    return f"{s[:4]}-{s[4:6]}-{s[6:8]} {s[8:10]}:{s[10:12]}"

# ==========================================
# 1. 載入資料庫現有病患
# ==========================================
@st.cache_data(ttl=60)
def load_patient_list():
    raw_list = get_all_patients_overview()
    # 在這裡先幫資料做「美顏」，把時間格式化
    for p in raw_list:
        p['原始最早'] = p['最早紀錄'] # 保留原始格式用於排序或邏輯
        p['原始最晚'] = p['最晚紀錄']
        p['最早紀錄_顯示'] = format_time_str(p['最早紀錄'])
        p['最晚紀錄_顯示'] = format_time_str(p['最晚紀錄'])
    return raw_list

patients_list = load_patient_list()

# 製作下拉選單選項
patient_options = [f"{p['病歷號']} (共{p['資料筆數']}筆)" for p in patients_list]
id_map = {f"{p['病歷號']} (共{p['資料筆數']}筆)": p['病歷號'] for p in patients_list}

# ==========================================
# 2. 側邊欄設計
# ==========================================
with st.sidebar:
    st.title("🚑 控制面板")
    
    st.subheader("1. 選擇病患")
    input_mode = st.radio("輸入方式", ["從清單選擇", "手動輸入 ID"], horizontal=True)
    
    target_patient_id = ""
    
    if input_mode == "從清單選擇":
        if patient_options:
            selected_option = st.selectbox("請選擇病患", patient_options)
            target_patient_id = id_map[selected_option]
            
            # 顯示該病患的時間資訊 (使用美化後的時間)
            selected_info = next((p for p in patients_list if p['病歷號'] == target_patient_id), None)
            if selected_info:
                st.info(
                    f"📅 資料區間：\n\n"
                    f"**{selected_info['最早紀錄_顯示']}**\n⬇\n"
                    f"**{selected_info['最晚紀錄_顯示']}**"
                )
        else:
            st.warning("資料庫中無資料。")
            target_patient_id = st.text_input("請手動輸入病歷號")
    else:
        target_patient_id = st.text_input("請手動輸入病歷號", value="0002452972")

    st.subheader("2. 時間篩選 (選用)")
    use_time_filter = st.checkbox("啟用時間篩選", value=False)
    start_dt_str = None
    end_dt_str = None
    
    if use_time_filter:
        col1, col2 = st.columns(2)
        with col1:
            d1 = st.date_input("開始日期", datetime(2025, 11, 15))
            t1 = st.time_input("開始時間", datetime.strptime("15:00", "%H:%M").time())
        with col2:
            d2 = st.date_input("結束日期", datetime(2025, 11, 15))
            t2 = st.time_input("結束時間", datetime.strptime("17:00", "%H:%M").time())
            
        start_dt_str = f"{d1.year}{d1.month:02d}{d1.day:02d}{t1.hour:02d}{t1.minute:02d}00"
        end_dt_str = f"{d2.year}{d2.month:02d}{d2.day:02d}{t2.hour:02d}{t2.minute:02d}00"

    st.divider()
    run_btn = st.button("🚀 開始生成摘要", type="primary", use_container_width=True)

# ==========================================
# 3. 主畫面邏輯
# ==========================================
st.title("🏥 AI 急診病程摘要生成系統")

# --- 首頁儀表板 (還沒按生成按鈕時顯示) ---
if not run_btn:
    st.markdown("### 📊 資料庫病患總覽")
    st.info("請從左側選擇一位病患並點擊「開始生成摘要」。")
    
    if patients_list:
        # 整理要在表格顯示的欄位 (只顯示美化後的時間)
        display_data = []
        for p in patients_list:
            display_data.append({
                "病歷號": p['病歷號'],
                "最早就診時間": p['最早紀錄_顯示'], # 使用美化版
                "最後紀錄時間": p['最晚紀錄_顯示'], # 使用美化版
                "資料筆數": p['資料筆數']
            })
            
        df_overview = pd.DataFrame(display_data)
        
        st.dataframe(
            df_overview, 
            use_container_width=True,
            column_config={
                "病歷號": st.column_config.TextColumn("病歷號", help="Patient ID"),
                "資料筆數": st.column_config.ProgressColumn(
                    "資料量", 
                    format="%d 筆", 
                    min_value=0, 
                    max_value=max(p['資料筆數'] for p in patients_list)
                ),
            }
        )
    else:
        st.warning("目前資料庫中沒有任何護理紀錄資料。")

# --- 執行摘要生成 ---
else:
    if not target_patient_id:
        st.error("請先輸入或選擇一個病歷號！")
        st.stop()

    load_dotenv()
    # 檢查 API Key
    api_ready = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_ready:
        st.error("❌ 未偵測到 API Key (Groq/OpenAI)，請檢查 .env 檔案！")
        st.stop()

    status_box = st.status(f"🔍 正在搜尋病患 ID: **{target_patient_id}** ...", expanded=True)

    # 1. 撈取資料
    patient_data = get_patient_full_history(
        target_patient_id, 
        start_time=start_dt_str, 
        end_time=end_dt_str
    )

    if not patient_data or (len(patient_data['nursing']) + len(patient_data['vitals']) + len(patient_data['labs']) == 0):
        status_box.update(label="❌ 找不到資料", state="error")
        st.error(f"找不到病患 {target_patient_id} 的資料，或該時段無資料。")
    else:
        # 統計
        n_count = len(patient_data['nursing'])
        v_count = len(patient_data['vitals'])
        l_count = len(patient_data['labs'])
        status_box.write(f"✅ 資料撈取成功！(護理: {n_count} | 生理: {v_count} | 檢驗: {l_count})")

        # 2. 顯示分頁
        tab1, tab2, tab3 = st.tabs(["📝 AI 生成摘要", "📊 原始資料預覽", "📈 生命徵象趨勢"])

        with tab1:
            status_box.write("🤖 正在呼叫 AI 模型進行分析...")
            summary = generate_nursing_summary(target_patient_id, patient_data)
            status_box.update(label="✅ 摘要生成完成！", state="complete", expanded=False)
            
            st.markdown("### 📋 急診病程摘要")
            st.markdown("---")
            st.markdown(summary)
            
            st.download_button(
                label="📥 下載摘要文字檔",
                data=summary,
                file_name=f"summary_{target_patient_id}.txt",
                mime="text/plain"
            )

        with tab2:
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**🩺 護理紀錄 ({n_count})**")
                st.dataframe(patient_data['nursing'], use_container_width=True)
                st.write(f"**💓 生理監測 ({v_count})**")
                st.dataframe(patient_data['vitals'], use_container_width=True)
            with c2:
                st.write(f"**🧪 檢驗報告 ({l_count})**")
                st.dataframe(patient_data['labs'], use_container_width=True)

        with tab3:
            if v_count > 0:
                df_vitals = pd.DataFrame(patient_data['vitals'])
                if 'PROCDTTM' in df_vitals.columns:
                    try:
                        df_vitals['Time'] = pd.to_datetime(df_vitals['PROCDTTM'], format='%Y%m%d%H%M%S', errors='coerce')
                        df_vitals = df_vitals.dropna(subset=['Time']).set_index('Time')
                        
                        st.write("**生命徵象趨勢圖**")
                        cols_to_plot = []
                        # 嘗試轉數值並繪圖
                        for col in ['EPLUSE', 'ESAO2', 'ETEMPUTER']:
                            if col in df_vitals.columns:
                                df_vitals[col] = pd.to_numeric(df_vitals[col], errors='coerce')
                                cols_to_plot.append(col)
                            
                        if cols_to_plot:
                            st.line_chart(df_vitals[cols_to_plot])
                        else:
                            st.info("數值格式無法解析，無法繪圖。")
                    except:
                        st.warning("時間格式解析失敗。")
            else:
                st.info("無生理監測資料。")