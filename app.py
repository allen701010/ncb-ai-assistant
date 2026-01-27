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
    api_key = st.secrets.get("GEMINI_API_KEY") or st.text_input("輸入 Gemini API Key", type="password")
    
    # 加入清除紀錄按鈕，有效降低 TPM 消耗
    if st.button("🧹 清除對話紀錄"):
        st.session_state.chat_history = []
        st.rerun()
        
    st.markdown("---")
    st.info("💡 提示：若遇到 429 錯誤，請點擊上方按鈕清除紀錄並稍候一分鐘。")

# 4. 鎖定指引核心內容
SYSTEM_INSTRUCTION = """你是 'NCB CAN HELP' AI 助理，專門根據 2018 版《實驗動物照護及使用指引》提供諮詢。
【核心知識點】
1. 3Rs精神：替代 (Replacement)、減量 (Reduction)、精緻化 (Refinement)。
2. 環境標準：小鼠、大鼠建議溫度 20-26°C。
3. 疼痛評估：分數達 15-20 分應考慮人道安樂死。
4. 安樂死禁忌：CO2 須使用高壓桶裝氣體，嚴禁乾冰。"""

st.title("🐾 NCB 可以提供協助")
st.subheader("實驗動物照顧及使用指引 AI 顧問")

# 5. 💡 快速查詢按鈕
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

# 顯示歷史紀錄
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]): 
        st.markdown(msg["content"])

# 6. 處理輸入 (使用最穩定模型名稱)
user_input = st.chat_input("詢問指引內容...")
prompt = user_input or quick_query

if prompt:
    if not api_key:
        st.error("請在 Secrets 設定 GEMINI_API_KEY！")
        st.stop()
    
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"): 
        st.markdown(prompt)

    try:
        client = genai.Client(api_key=api_key)
        with st.chat_message("assistant"):
            with st.spinner("AI 正在查閱指引..."):
                response = client.models.generate_content(
                    model='gemini-2.0-flash-exp', 
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.1
                    )
                )
                st.markdown(response.text)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
    except Exception as e:
        # 針對 429 錯誤提供友善提示
        if "429" in str(e):
            st.error("⚠️ 流量已達上限：請點擊左側「清除對話紀錄」並等待一分鐘後再試。")
        else:
            st.error(f"發生錯誤：{e}")

st.markdown("---")
st.caption("⚠️ 免責聲明：本 AI 僅供參考，所有處置應以機構 IACUC 核准版本為準。")