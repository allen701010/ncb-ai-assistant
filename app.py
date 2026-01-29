import streamlit as st
from google import genai
from google.genai import types

# 1. 頁面配置
st.set_page_config(page_title="NCB CAN HELP - 實驗動物專業助理", layout="wide")

# 2. 初始化對話紀錄
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 3. 側邊欄設定
with st.sidebar:
    st.title("⚙️ 設定中心")
    # 從 Secrets 讀取金鑰
    api_key = st.secrets.get("GEMINI_API_KEY") or st.text_input("輸入 Gemini API Key", type="password")
    
    # 診斷與清理工具
    col_diag, col_clear = st.columns(2)
    with col_diag:
        if st.button("🔍 檢查連線"):
            if api_key:
                try:
                    test_client = genai.Client(api_key=api_key)
                    models = test_client.models.list()
                    st.success("✅ 連線成功")
                except Exception as e: st.error(f"連線失敗: {e}")
            else: st.warning("請先設定 Key")
    
    with col_clear:
        if st.button("🧹 清除紀錄"):
            st.session_state.chat_history = []
            st.rerun()
            
    st.markdown("---")
    st.info("💡 提示：本助理會優先使用免費額度，若流量過載將自動切換至高階模型。")

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

# 6. 自動路由處理邏輯
user_input = st.chat_input("詢問指引內容...")
prompt = user_input or quick_query

if prompt:
    if not api_key:
        st.error("請在 Secrets 設定 GEMINI_API_KEY！")
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
        client = genai.Client(api_key=api_key)
        response = None
        used_model = ""

        with st.chat_message("assistant"):
            with st.spinner("查閱指引中..."):
                for model_id in model_priority:
                    try:
                        res = client.models.generate_content(
                            model=model_id,
                            contents=prompt,
                            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.1)
                        )
                        response = res
                        used_model = model_id
                        break
                    except Exception as e:
                        # 只有遇到配額用盡(429)或模型不存在(404)時才顯示提示並切換
                        if "429" in str(e) or "404" in str(e):
                            st.warning(f"⚠️ {model_id} 目前無法使用（配額用盡或維護中），正在自動切換至下一順位模型...")
                            continue
                        else: raise e

                if response:
                    st.caption(f"✨ 驅動模型: {used_model}")
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                else:
                    st.error("❌ 所有模型配額皆已耗盡，請點擊「清除紀錄」並等一分鐘後再試。")

    except Exception as e:
        st.error(f"發生錯誤：{e}")

st.markdown("---")
st.caption("⚠️ 免責聲明：本 AI 提供資訊僅供參考，不代表官方行政處分。")