import streamlit as st
import requests

st.title("不鏽鋼顧問問答系統")

user_query = st.text_area("請輸入你的問題：", height=100)

if st.button("送出問題"):
    if user_query.strip():
        with st.spinner("正在查詢中，請稍候..."):
            try:
                response = requests.post(
                    "http://localhost:5000/ask",
                    json={"query": user_query}
                )
                if response.status_code == 200:
                    result = response.json()
                    st.success("回答如下：")
                    st.write(result["answer"])
                else:
                    st.error(f"查詢失敗，錯誤代碼 {response.status_code}")
            except Exception as e:
                st.error(f"無法連線到伺服器：{e}")
    else:
        st.warning("請輸入問題後再送出。")
