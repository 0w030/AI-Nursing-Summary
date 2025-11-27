# /data/metadata.py

# 資料欄位中文對照表
# 修正說明：已將所有資料表的中文用語統一以「急診檢驗檢查主檔」為標準。
# 例如：TRINO 統一為「急診號」，VISITDT 統一為「急診日期」。

COLUMN_MAPPING = {
    # ==========================================
    # 1. DB_ADM_ORDER_ER (主檔 - 標準用語來源)
    # ==========================================
    "CHAD1CASENO": "急診號",
    "CHAD1MRNO": "病歷號",
    "CHAD4GREQNO": "檢驗申請號",
    "CHAD4CDATE": "採檢日期時間",
    "CHAD1ORDNO": "醫囑代碼",
    "CHAD4ORDNAME": "醫囑名稱",
    "CHTEAMNAM": "開單科別",
    "CHAD4SPECT": "檢體類別",
    "CHAD4DCDATE": "取消日期",
    "CHAD4STAT": "狀態",
    "CHAD4REP1": "報告註記",
    "CHRCPDTM": "收件時間",
    "CHREPORTDATE": "報告日期",
    "CHTEXT": "報告內容",
    "SOURCETYPE": "來源類別",

    # ==========================================
    # 2. DB_ADM_LABORDER_ER (急診檢驗頭檔)
    # ==========================================
    "CHCASENO": "急診號",
    "CHMRNO": "病歷號",
    "CHGREQNO": "申請序號",
    "CHAPPDTM": "申請時間",
    "CHLREQNO": "檢驗單號",
    "CHORDNO": "醫囑代碼",
    "CHORDNAM": "醫囑名稱",
    "CHSTAT": "狀態碼",
    "CHSPECI": "檢體",
    "ORDSEQ": "醫囑序號",
    "CHTAPPDT": "申請日期",
    "CHRCONNAME": "容器名稱",
    "CONCODE": "容器代碼",
    "LABMCHNO": "儀器編號",
    "LABUNIFNO": "檢驗統一編號",
    "LABCLASS": "檢驗類別",
    "ORDPROCDTTM": "處理時間",

    # ==========================================
    # 3. DB_ADM_LABDATA_ER (急診檢驗明細)
    # ==========================================
    "CHITEMNO": "項目代碼",
    "CHHEAD": "項目名稱",
    "CHVAL": "結果值",
    "CHUNIT": "單位",
    "CHCOMMT": "註記",
    "CHNL": "參考值下限",
    "CHNH": "參考值上限",
    "CHITEMSEQ": "項目序號",
    "CHSIGNDTTM": "簽核時間",
    "CHLABAPCODE": "簽核人員代碼",

    # ==========================================
    # 4. ENSDATA (急診護理紀錄) & v_ai_hisensnes (生理監測)
    # ==========================================
    # 這裡將 TRINO 與 VISITDT 統一用語
    "TRINO": "急診號",      # 修正：原為「急診編號」，現統一為「急診號」
    "PATID": "病歷號",
    "VISITDT": "急診日期",  # 修正：原為「就診日」，現統一為「急診日期」
    "SEQ": "序號",
    "SUBJECT": "主訴",
    "PROCDTTM": "記錄時間",
    "DIAGNOSIS": "診斷",
    "CLOSE": "結案",
    "FIINISH": "完成",

    # 生理數值欄位
    "EWEIGHT": "體重",
    "ETEMPUTER": "體溫",
    "ETREGION": "體溫測量部位",
    "EPLUSE": "脈搏",
    "EBREATHE": "呼吸",
    "EPRESSURE": "收縮壓",
    "EDIASTOLIC": "舒張壓",
    "ESAO2": "血氧(SaO2)",
    "GCS_E": "昏迷指數_眼",
    "GCS_V": "昏迷指數_聲",
    "GCS_M": "昏迷指數_動",
    "PUPIL_L": "左眼瞳孔",
    "PUPIL_R": "右眼瞳孔",
    "ENESKIND": "檢傷級數"
}

def get_chinese_name(column_name):
    """
    傳入英文欄位名稱，返回中文描述。
    如果不區分大小寫查找，若找不到則返回原英文名稱。
    """
    if not column_name:
        return ""
    
    col = str(column_name).strip().upper()
    return COLUMN_MAPPING.get(col, column_name)