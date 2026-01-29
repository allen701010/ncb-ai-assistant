import streamlit as st
from google import genai
from google.genai import types
from openai import OpenAI

# 1. 頁面配置
st.set_page_config(page_title="NCB CAN HELP - 實驗動物專業助理", layout="wide")

# 2. 初始化對話紀錄
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 3. 側邊欄設定
with st.sidebar:
    st.title("⚙️ 設定中心")
    # 從 Secrets 讀取金鑰
    gemini_api_key = st.secrets.get("GEMINI_API_KEY") or st.text_input("輸入 Gemini API Key", type="password", key="gemini_key")
    openrouter_api_key = st.secrets.get("OPENROUTER_API_KEY") or st.text_input("輸入 OpenRouter API Key (備援)", type="password", key="openrouter_key")
    
    # 診斷與清理工具
    col_diag, col_clear = st.columns(2)
    with col_diag:
        if st.button("🔍 檢查連線"):
            status_msgs = []
            # 檢查 Gemini
            if gemini_api_key:
                try:
                    test_client = genai.Client(api_key=gemini_api_key)
                    models = test_client.models.list()
                    status_msgs.append("✅ Gemini 連線成功")
                except Exception as e:
                    status_msgs.append(f"❌ Gemini 連線失敗: {e}")
            else:
                status_msgs.append("⚠️ 未設定 Gemini Key")
            
            # 檢查 OpenRouter
            if openrouter_api_key:
                try:
                    test_or_client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=openrouter_api_key
                    )
                    # 簡單測試連線
                    test_or_client.models.list()
                    status_msgs.append("✅ OpenRouter 連線成功")
                except Exception as e:
                    status_msgs.append(f"❌ OpenRouter 連線失敗: {e}")
            else:
                status_msgs.append("⚠️ 未設定 OpenRouter Key (備援)")
            
            for msg in status_msgs:
                if "✅" in msg:
                    st.success(msg)
                elif "❌" in msg:
                    st.error(msg)
                else:
                    st.warning(msg)
    
    with col_clear:
        if st.button("🧹 清除紀錄"):
            st.session_state.chat_history = []
            st.rerun()
            
    st.markdown("---")
    st.info("💡 提示：本助理優先使用 Gemini 免費額度，若配額用盡將自動切換至 OpenRouter 備援。")

# 4. 指引核心內容鎖定
SYSTEM_INSTRUCTION = """你是 'NCB CAN HELP' AI 助理，根據 2018 版《實驗動物照護及使用指引》回答。
1. 3Rs精神：替代、減量、精緻化。
2. 環境：小鼠大鼠溫度 20-26°C，換氣 10-15 次/小時。
3. 疼痛：分數達 15-20 分應考慮人道安樂死。
4. 禁忌：CO2 須高壓桶裝，嚴禁乾冰。"""

st.title("🐾 NCB 可以提供協助")
st.subheader("實驗動物照顧及使用指引 AI 顧問 (自動路由版)")

# 5. 快速查詢按鈕
st.write("### 💡 快速查詢")
btn_cols = st.columns(4)
queries = [
    ("🌡️ 環境溫度規範", "請列出常見實驗動物的環境建議溫度範圍。"),
    ("🧬 3R 原則定義", "請解釋指引中替代、減量及精緻化的定義。"),
    ("⚖️ 疼痛分級標準", "根據指引附件二，如何評估大鼠疼痛等級？"),
    ("🚫 安樂死禁忌", "指引禁止哪些不人道安樂死？CO2有限制嗎？")
]
quick_query = None
for i, (label, q_text) in enumerate(queries):
    if btn_cols[i].button(label): quick_query = q_text

# 顯示歷史紀錄
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# 6. API 呼叫函數
def call_gemini_api(client, model_id, prompt, system_instruction):
    """使用 Google Gemini API 呼叫"""
    res = client.models.generate_content(
        model=model_id,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.1)
    )
    return res.text

def call_openrouter_api(api_key, model_id, prompt, system_instruction):
    """使用 OpenRouter API 呼叫 (OpenAI 相容格式)"""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
    
    # OpenRouter 的 Gemini 模型名稱對應
    openrouter_model_map = {
        'gemini-2.0-flash-exp': 'google/gemini-2.0-flash-exp:free',
        'gemini-3-flash-preview': 'google/gemini-2.5-flash-preview',
        'gemini-3-pro-preview': 'google/gemini-2.5-pro-preview'
    }
    
    or_model = openrouter_model_map.get(model_id, 'google/gemini-2.0-flash-exp:free')
    
    response = client.chat.completions.create(
        model=or_model,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    return response.choices[0].message.content

# 7. 自動路由處理邏輯
user_input = st.chat_input("詢問指引內容...")
prompt = user_input or quick_query

if prompt:
    if not gemini_api_key and not openrouter_api_key:
        st.error("請設定至少一個 API Key (Gemini 或 OpenRouter)！")
        st.stop()
    
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # 定義路由優先順序
    model_priority = [
        'gemini-2.0-flash-exp',      # 1. 免費優先
        'gemini-3-flash-preview',    # 2. 付費 Flash 備援
        'gemini-3-pro-preview'       # 3. 最終 Pro 方案
    ]

    try:
        response_text = None
        used_model = ""
        api_source = ""
        gemini_exhausted = False

        with st.chat_message("assistant"):
            with st.spinner("查閱指引中..."):
                # 階段一：優先嘗試 Gemini API
                if gemini_api_key:
                    client = genai.Client(api_key=gemini_api_key)
                    for model_id in model_priority:
                        try:
                            response_text = call_gemini_api(client, model_id, prompt, SYSTEM_INSTRUCTION)
                            used_model = model_id
                            api_source = "Gemini"
                            break
                        except Exception as e:
                            error_str = str(e)
                            # 配額用盡(429)或模型不存在(404)時切換下一個模型
                            if "429" in error_str or "404" in error_str:
                                st.warning(f"⚠️ Gemini {model_id} 目前無法使用，嘗試下一個模型...")
                                continue
                            else:
                                raise e
                    
                    # 如果所有 Gemini 模型都失敗，標記為 exhausted
                    if not response_text:
                        gemini_exhausted = True
                        st.warning("⚠️ Gemini API 配額已用盡，正在切換至 OpenRouter 備援...")
                
                # 階段二：如果 Gemini 配額用盡或無 Key，使用 OpenRouter
                if (gemini_exhausted or not gemini_api_key) and openrouter_api_key:
                    for model_id in model_priority:
                        try:
                            response_text = call_openrouter_api(openrouter_api_key, model_id, prompt, SYSTEM_INSTRUCTION)
                            used_model = model_id
                            api_source = "OpenRouter"
                            break
                        except Exception as e:
                            error_str = str(e)
                            if "429" in error_str or "404" in error_str or "rate" in error_str.lower():
                                st.warning(f"⚠️ OpenRouter {model_id} 目前無法使用，嘗試下一個模型...")
                                continue
                            else:
                                raise e

                if response_text:
                    source_icon = "🔷" if api_source == "Gemini" else "🟠"
                    st.caption(f"✨ 驅動模型: {used_model} ({source_icon} {api_source})")
                    st.markdown(response_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                else:
                    st.error("❌ 所有 API 配額皆已耗盡，請稍後再試或檢查您的 API Key 設定。")

    except Exception as e:
        st.error(f"發生錯誤：{e}")

st.markdown("---")
st.caption("⚠️ 免責聲明：本 AI 提供資訊僅供參考，不代表官方行政處分。")