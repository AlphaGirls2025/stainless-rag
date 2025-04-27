import streamlit as st
import requests

st.title("🔩不鏽鋼顧問問答系統")

# 選擇功能
# mode = st.radio("請選擇功能：", ["一般問答", "找相似鋼種"])
mode = st.selectbox(
    '請選擇一個選項：',
    ('一般問答', '找相似鋼種(已知型號)')
)

# 輸入框
user_query = st.text_area("請輸入你的問題：", height=100)

# 送出按鈕
if st.button("送出問題"):
    if user_query.strip():
        with st.spinner("正在查詢中，請稍候..."):
            try:
                if mode == "一般問答":
                    # 呼叫 /ask API
                    response = requests.post(
                        "http://localhost:5000/ask",
                        json={"query": user_query}
                    )
                else:
                    # 呼叫 /find_similar_steel API
                    response = requests.post(
                        "http://localhost:5000/find_similar_steel",
                        json={"query": user_query}
                    )

                if response.status_code == 200 and mode == "一般問答":
                    result = response.json()
                    st.success("回答如下：")
                    st.write(result["answer"])
                elif  response.status_code == 200 and mode == "找相似鋼種(已知型號)":
                    # result = "假裝的 RESPONSE"
                    result = response.json()
                    st.success("回答如下：")
                    st.write(result["answer"])
                else:
                    st.error(f"查詢失敗，錯誤代碼 {response.status_code}")
            except Exception as e:
                st.error(f"無法連線到伺服器：{e}")
    else:
        st.warning("請輸入問題後再送出。")
