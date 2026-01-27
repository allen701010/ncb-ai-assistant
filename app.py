import streamlit as st
from google import genai
from google.genai import types

# 頁面配置
st.set_page_config(page_title="NCB CAN HELP - 實驗動物專業助理", layout="wide")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 側邊欄設定
with st.sidebar:
    st.title("⚙️ 設定中心")
api_key = st.secrets["GEMINI_API_KEY"]("輸入 Gemini API Key", type="password")
    thinking_budget = st.slider("思考預算 (Thinking Budget)", 1024, 8192, 2048)
    st.markdown("---")
    st.info("本機器人已內建《實驗動物照護及使用指引》完整邏輯 [cite: 91, 111]")

# 注入文件的核心內容與邏輯 
SYSTEM_INSTRUCTION = """
你是 'NCB CAN HELP' AI 顧問，專門解讀《實驗動物照護及使用指引》。

【核心規範文字】
1. 3Rs 精神：
   - 替代 (Replacement)：採取不需使用動物的方法，包括電腦系統（絕對取代）或以演化程度較低動物取代脊椎動物（相對取代） [cite: 98]。
   - 減量 (Reduction)：使用較少量動物獲取所需資訊，或利用一定量動物獲取最大限度資訊 [cite: 99]。
   - 精緻化 (Refinement)：改良飼養或實驗操作程序，以減少或消除動物的疼痛與緊迫 [cite: 100]。

2. 疼痛評估 (附件二)：
   - 評估指標：體重、外觀、臨床症狀、先天性行為、對刺激反應 [cite: 887, 1191]。
   - 大鼠嚴重疼痛：持續性拱背、明顯皮毛粗糙、呼吸困難、活力明顯下降、社會化行為嚴重退縮 [cite: 924, 1142]。
   - 處置建議：分數加總達 15-20 分時，應考慮給予安樂死 [cite: 1193, 1221]。

3. 環境標準 (附件三)：
   - 小鼠、大鼠、倉鼠、天竺鼠建議溫度：20-26°C 。
   - 兔子建議溫度：16-22°C 。
   - 換氣率：每小時 10~15 次 [cite: 433]。

4. 安樂死方法 (附件二)：
   - 二氧化碳 (CO2)：需使用高壓桶裝氣體，禁止使用乾冰 [cite: 993]。
   - 頸椎脫臼：限小於 200g 大鼠或 1kg 以下兔子，且需由技術精湛人員執行 [cite: 1029]。
   - 禁忌：嚴禁直接沖下水道、直接放入冰箱慢慢冷凍致死 [cite: 1088]。
"""

st.title("🐾 NCB 可以提供協助")
st.subheader("實驗動物照顧及使用指引 AI 顧問")

# 顯示對話歷史紀錄
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 處理用戶輸入
if prompt := st.chat_input("您可以詢問：'3R 原則的定義？' 或 '大鼠拱背屬於哪一級疼痛？'"):
    
    if not api_key:
        st.error("請先在左側輸入 API Key！")
        st.stop()

    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        client = genai.Client(api_key=api_key)
        
        with st.chat_message("assistant"):
            with st.spinner("AI 正在查閱指引文件內容..."):
                response = client.models.generate_content(
                    model='gemini-2.5-flash-preview-09-2025',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
                        temperature=0.1,
                    )
                )
                
                # 安全獲取並顯示思考路徑 (解決 Candidate 報錯問題)
                try:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'thought') and candidate.thought:
                        with st.expander("查看 AI 思考路徑 (Hybrid Reasoning)"):
                            st.write(candidate.thought)
                except Exception:
                    pass
                
                full_response = response.text
                st.markdown(full_response)
                st.session_state.chat_history.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"連線或執行發生錯誤：{str(e)}")

st.markdown("---")

st.caption("⚠️ 免責聲明：本 AI 顧問內容僅供參考，不代表官方行政處分。所有動物實驗處置應以機構 IACUC 核准版本與獸醫師診斷為準 [cite: 142, 171]。")
