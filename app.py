import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="NCB CAN HELP - 實驗動物專業助理", layout="wide")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.title("⚙️ 設定中心")
    api_key = st.secrets.get("GEMINI_API_KEY") or st.text_input("輸入 Gemini API Key", type="password")
    thinking_budget = st.slider("思考預算 (Thinking Budget)", 1024, 8192, 2048)

SYSTEM_INSTRUCTION = "你是 'NCB CAN HELP' AI 顧問，專門解讀《實驗動物照護及使用指引》。"

st.title("🐾 NCB 可以提供協助")
st.subheader("實驗動物照顧及使用指引 AI 顧問")

# 💡 快速按鈕區域 (確保這段有在 GitHub 上)
st.write("### 💡 快速查詢")
col1, col2, col3, col4 = st.columns(4)
quick_query = None
with col1:
    if st.button("🌡️ 環境溫度規範"): quick_query = "請列出常見實驗動物的環境建議溫度範圍。"
with col2:
    if st.button("🧬 3R 原則定義"): quick_query = "請解釋指引中替代、減量及精緻化的定義。"
with col3:
    if st.button("⚖️ 疼痛分級標準"): quick_query = "根據指引附件二，如何評估大鼠疼痛等級？"
with col4:
    if st.button("🚫 安樂死禁忌"): quick_query = "指引禁止哪些不人道安樂死？CO2有限制嗎？"

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

user_input = st.chat_input("詢問指引內容...")
prompt = user_input or quick_query

if prompt:
    if not api_key:
        st.error("請在左側輸入 API Key 或設定 Secrets！")
        st.stop()
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    try:
        client = genai.Client(api_key=api_key)
        with st.chat_message("assistant"):
            response = client.models.generate_content(
                model='gemini-2.0-flash-thinking-exp-01-21', # 建議使用更穩定的版本
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.1)
            )
            st.markdown(response.text)
            st.session_state.chat_history.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"錯誤：{e}")