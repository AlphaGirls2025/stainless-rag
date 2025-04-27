import streamlit as st
import requests, os, time


# Admin 帳號密碼設定
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Session state
if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False
if 'admin_login_mode' not in st.session_state:
    st.session_state['admin_login_mode'] = False  # 控制是否進入 admin login 畫面

# Admin 登入頁面
def admin_login():
    col1, col2 = st.columns([8, 1])
    with col1:
        st.markdown("## 不鏽鋼顧問問答系統 - 管理員頁面")  # 改用markdown，標題size也可以調
    with col2:
        if st.button("⬅️ Back"):
            st.session_state['admin_login_mode'] = False
            st.rerun()

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state['is_admin'] = True
            st.session_state['admin_login_mode'] = False
            st.success("Admin login successful!")
            st.rerun()
        else:
            st.error("Invalid admin credentials")


# Admin Page
def admin_page():
    # 設定檔案存放資料夾
    UPLOAD_FOLDER = "uploaded_pdfs"

    # 確認資料夾存在
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    col1, col2 = st.columns([8,1])
    with col1:
        st.markdown("## Admin Page")
    with col2:
        if st.button("🚪 Exit"):
            st.session_state['is_admin'] = False
            st.rerun()

    st.divider()

    st.markdown("### 📄 更新 PDF 文件給 Chatbot 向量資料庫")
    st.info("僅支援 PDF 格式，請選擇要上傳的文件。")

    uploaded_file = st.file_uploader(
        "選擇你的 PDF 檔案",
        type=["pdf"],
        accept_multiple_files=False,
        label_visibility="collapsed"  # 隱藏系統預設 label
    )
    # 用一個 placeholder 來動態顯示「上傳中、成功」的狀態
    status_placeholder = st.empty()

    if uploaded_file is not None:
        if uploaded_file.type != "application/pdf":
            st.error("只允許上傳 PDF 格式的檔案。")
        else:
            # 存檔
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # 顯示更新中的小動畫
            with status_placeholder.container():
                st.info("🔄 正在更新向量資料庫，請稍候...")

            # 模擬處理 (實際可以放更新你的 vector database 的程式碼)
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # 可以加上你的 ingestion 邏輯，比如：
            response = requests.post(
                        "http://localhost:5000/update_pdf_knowledgebase",
                        json={"pdf_file_path": file_path}
                    )

            # 模擬資料庫更新花時間
            time.sleep(2)

            # 更新完成，顯示成功
            with status_placeholder.container():
                st.success(f"✅ 成功上傳並更新 \"{uploaded_file.name}\" 至向量資料庫！")
    else:
        st.markdown("請上傳一個 .pdf 檔案。")

# User Page
def user_page():
    # 用columns做標題和按鈕水平排列
    col1, col2 = st.columns([8, 1])
    with col1:
        st.markdown("## 不鏽鋼顧問問答系統")  # 改用markdown，標題size也可以調
    with col2:
        if st.button("🔒 Admin"):   # 按鈕在右邊
            st.session_state['admin_login_mode'] = True
            st.rerun()

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


# 主程式
if st.session_state['admin_login_mode']:
    admin_login()
elif st.session_state['is_admin']:
    admin_page()
else:
    user_page()
