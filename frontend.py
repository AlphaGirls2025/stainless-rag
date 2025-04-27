import streamlit as st
import requests

st.title("🔩不鏽鋼顧問問答系統")

# 選擇功能
mode = st.selectbox(
    '請選擇一個選項：',
    ('一般問答', '找相似鋼種(已知型號)')
)

# 輸入框
user_query = st.text_area("請輸入你的問題：", height=100)

# 上傳圖片
uploaded_file = st.file_uploader("如果有圖片，可以在這裡上傳（只支援 JPG 或 PNG）", type=["png", "jpg", "jpeg"])

# 送出按鈕
if st.button("送出問題"):
    if user_query.strip():
        # 先檢查圖片格式
        if uploaded_file:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            if file_extension not in ["jpg", "jpeg", "png"]:
                st.error("請上傳正確格式的圖片（只支援 JPG 或 PNG）")
                st.stop()

        with st.spinner("正在查詢中，請稍候..."):
            try:
                files = None
                data = {"query": user_query}

                if uploaded_file:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}

                if mode == "一般問答":
                    url = "http://localhost:5000/ask"
                else:
                    url = "http://localhost:5000/find_similar_steel"

                if files:
                    response = requests.post(url, data=data, files=files)
                else:
                    response = requests.post(url, json=data)

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
