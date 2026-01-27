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
    # 自動讀取 Secrets 中的金鑰
    api_key = st.secrets.get("GEMINI_API_KEY") or st.text_input("輸入 Gemini API Key", type="password")
    
    # --- 新增：API 診斷功能 ---
    if st.button("🔍 檢查 API 連線狀態"):
        if not api_key:
            st.error("找不到 API Key！請檢查 Secrets 設定。")
        else:
            try:
                test_client = genai.Client(api_key=api_key)
                models = test_client.models.list()
                st.success("✅ 連線成功！API 金鑰有效。")
                # 檢查是否支援 Gemini 3
                model_names = [m.name for m in models]
                if any("gemini-3-flash" in name for name in model_names):
                    st.info("🎯 已確認您的帳戶支援 Gemini 3 Flash。")
                else:
                    st.warning("⚠️ 目前帳戶未見 Gemini 3，若運行出錯建議改回 gemini-2.0-flash-exp。")
            except Exception as e:
                st.error(f"❌ 連線失敗：{str(e)}")
    
    # --- 新增：清除紀錄按鈕 (降低 TPM 消耗) ---
    if st.button("🧹 清除對話紀錄"):
        st.session_state.chat_history = []
        st.rerun()
        
    st.markdown("---")
    st.info("💡 提示：若遇到 429 錯誤，請點擊上方清除按鈕並稍候一分鐘。")

# 4. 鎖定指引核心內容
SYSTEM_INSTRUCTION = """你是 'NCB CAN HELP' AI 助理，根據 2018 版《實驗動物照護及使用指引》回答。
核心知識：
1. 3Rs精神：替代 (Replacement)、減量 (Reduction)、精緻化 (Refinement)。
2. 環境標準：小鼠大鼠溫度 20-26°C，換氣 10-15 次/小時。
3. 疼痛評估：參考附件二，分數達 15-20 分應考慮人道安樂死。
4. 安樂死禁忌：CO2 須高壓桶裝，嚴禁乾冰。禁止空氣注射、溺斃、燒死。"""

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

# 6. 處理輸入 (改用 Gemini 3 Flash Preview)
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
            with st.spinner("Gemini 3 正在查閱指引..."):
                response = client.models.generate_content(
                    model='gemini-3-flash-preview', 
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.1
                    )
                )
                st.markdown(response.text)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
    except Exception as e:
        if "429" in str(e):
            st.error("⚠️ 流量上限：請點擊左側「清除對話紀錄」並稍候。")
        elif "404" in str(e):
            st.error("❌ 模型 ID 錯誤：請確認您的帳戶是否支援 gemini-3-flash-preview。")
        else:
            st.error(f"發生錯誤：{e}")

st.markdown("---")
st.caption("⚠️ 免責聲明：本 AI 提供資訊僅供參考，所有處置應以機構 IACUC 核准版本為準。")