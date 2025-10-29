# /ai/ai_summarizer.py

import os
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

def format_reports_to_prompt(reports_data: list) -> str:
    """
    將多筆報告數據格式化成一個連貫的 Prompt 文本，適合送給 ChatGPT。
    """
    if not reports_data:
        return "找不到任何報告數據，無法生成摘要。"

    prompt_parts = [
        "請擔任一位資深的臨床醫生。您的任務是根據以下病患的歷史檢查報告，生成一份連貫的病程摘要。\n",
        "摘要應涵蓋以下重點：\n",
        "1. 病程時間軸：按日期順序，指出關鍵檢查結果的變化趨勢。\n",
        "2. 異常重點：突顯在不同時間點出現的異常或值得關注的指標。\n",
        "3. 簡短結論：對整體病程變化給出一個簡潔的總結。\n\n",
        "--- 結構化報告數據開始 ---\n"
    ]

    # 迭代每一筆報告數據
    for report in reports_data:
        # 將 JSONB 數據轉換為格式化的字串
        structured_data_str = json.dumps(report['data'], indent=2, ensure_ascii=False)
        
        report_text = f"""
日期: {report['date']}
檢查類型: {report['type']}
報告ID: {report['report_id']}
結構化結果:
{structured_data_str}
----------------------------------
"""
        prompt_parts.append(report_text)
    
    prompt_parts.append("--- 結構化報告數據結束 ---\n\n")
    prompt_parts.append("請開始生成連貫的病程摘要：")
    
    return "".join(prompt_parts)


def generate_summary(prompt_text: str) -> str:
    """
    呼叫 OpenAI API，生成摘要。
    """
    if not os.getenv("OPENAI_API_KEY"):
        return "錯誤: OPENAI_API_KEY 未設定。"

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "您是一位專業且客觀的醫療報告分析師。"},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.3, # 設置較低的溫度以確保摘要內容客觀和準確
            max_tokens=1000 
        )
        
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"OpenAI API 呼叫失敗: {e}")
        return f"AI 摘要生成錯誤: {e}"


if __name__ == '__main__':
    # 測試 Prompt 格式化
    sample_reports = [
        {'report_id': 1, 'date': '2025-05-01', 'type': '血液檢查', 'data': {"WBC": 12.5, "RBC": 4.8, "備註": "輕微發炎"}},
        {'report_id': 2, 'date': '2025-05-15', 'type': '血液檢查', 'data': {"WBC": 8.1, "RBC": 4.9, "備註": "指標趨於穩定"}}
    ]
    test_prompt = format_reports_to_prompt(sample_reports)
    print("--- 測試生成的 Prompt ---")
    print(test_prompt)
    
    # 實際呼叫 API 測試 (需要有效的 API Key)
    # print("\n--- 測試 AI 摘要生成 ---")
    # test_summary = generate_summary(test_prompt)
    # print(test_summary)