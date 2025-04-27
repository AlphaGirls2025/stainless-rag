from re import split
from flask import Flask, request, jsonify
import boto3
import json
from werkzeug.utils import secure_filename

from lib import s3, tractpdf, opensearch, knowledgebase

app = Flask(__name__)

# 建立 Bedrock Runtime client、Agent Runtime client、Textract client
brt = boto3.client("bedrock-runtime", region_name="us-east-1")
bart = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
textract = boto3.client('textract', region_name='us-east-1')

# Knowledge Base IDs
knowledge_base_ids = [
    "FSZ5KXW7FT",
    "CE1KPWLQBC",
    "ALVPHIH9ZC",
    "YQVYVZJI42"
]

def extract_text_from_image(file_bytes):
    """ 使用 Textract 的 DetectDocumentText 從圖片提取文字 """
    response = textract.detect_document_text(
        Document={'Bytes': file_bytes}
    )
    extracted_text = ""
    for block in response.get('Blocks', []):
        if block['BlockType'] == 'LINE':
            extracted_text += block['Text'] + "\n"
    return extracted_text.strip()

@app.route("/find_similar_steel", methods=["POST"])
def find_similar_steel():
    model_id = "amazon.nova-pro-v1:0"

    # ⚡ 支援 JSON 或 form-data
    if request.content_type.startswith('multipart/form-data'):
        user_query = request.form.get("query", "")
        uploaded_file = request.files.get("file")
    else:
        data = request.json
        user_query = data.get("query")
        uploaded_file = None

    if not user_query and not uploaded_file:
        return jsonify({"error": "Missing query or file"}), 400

    # ⚡ 如果有圖片，使用 Textract 抽取文字，並加到 query 前面
    if uploaded_file:
        file_bytes = uploaded_file.read()
        extracted_text = extract_text_from_image(file_bytes)
        user_query = extracted_text + "\n" + (user_query or "")

    # Step 1: 抽出型號
    model_prompt = f"""
    你是一位專業的不鏽鋼助理，請從下面的問題中找出使用者提到的「鋼種型號」，只需要回覆鋼種名稱（例如: 316Ti 或 S31635 或 SUS316Ti）。
    
    問題：
    {user_query}
    """
    model_invoke = {
        "messages": [{"role": "user", "content": [{"text": model_prompt}]}],
        "modelId": model_id,
        "inferenceConfig": {"temperature": 0.2, "topP": 0.9, "maxTokens": 100}
    }
    model_response = brt.converse(**model_invoke)
    model_name = model_response["output"]["message"]["content"][0]["text"].strip()

    if not model_name:
        return jsonify({"error": "Could not extract steel model from query"}), 400
    
    # Step 2: 查型號成分資料
    composition_texts = []
    for kb_id in knowledge_base_ids:
        response = bart.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": model_name},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 3}}
        )
        for doc in response.get("retrievalResults", []):
            text = doc.get("content", {}).get("text", "")
            if text and any(ele in text for ele in ["C", "Cr", "Ni", "Mo", "Mn", "Si", "N", "P", "S"]):
                composition_texts.append(text.strip())

    if not composition_texts:
        return jsonify({"error": "Could not find composition information"}), 404

    composition_info = "\n\n".join(composition_texts)

    # Step 4: 查詢成分類似鋼種
    similar_context_parts = []
    for kb_id in knowledge_base_ids:
        response = bart.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": composition_info},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5}}
        )
        for doc in response.get("retrievalResults", []):
            text = doc.get("content", {}).get("text", "")
            if text:
                similar_context_parts.append(text.strip())

    if not similar_context_parts:
        return jsonify({"error": "Could not find similar steels by vector search"}), 404

    context = "\n\n".join(similar_context_parts)

    # Step 5: 組 Prompt
    number_prompt = f"""
    你是一位專業的不鏽鋼材料工程師，擅長分析各種不鏽鋼鋼種的化學成分差異，並根據成分組成推薦成分類似的鋼種。

    請依照以下規則回答問題：

    （規則內容省略，因為你的原prompt已經很完整）

    【鋼種成分資料】
    {context}

    【問題】
    {user_query}

    請用**簡單清楚且條列的中文**作答。
    """

    invoke_request = {
        "messages": [{"role": "user", "content": [{"text": number_prompt}]}],
        "modelId": model_id,
        "inferenceConfig": {"temperature": 0.0, "topP": 0.9, "maxTokens": 1024}
    }

    try:
        invoke_response = brt.converse(**invoke_request)
        final_answer = invoke_response["output"]["message"]["content"][0]["text"]
        return jsonify({
            "query_model": model_name,
            "answer": final_answer
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
UPLOAD_FOLDER = "uploaded_pdfs"

@app.route("/update_pdf_knowledgebase", methods=["POST"])
def update_pdf_knowledgebase():
    data = request.json
    pdf_file_path = data.get("pdf_file_path")

    # split pdf file
    split_pdf_path = "./data/split_pdf_new/"
    split_pdfs = tractpdf.split_pdf_pages(pdf_file_path, split_pdf_path)
    
    # upload to s3 bucket
    s3_bucket_name = "aiwave-hackathon-team"
    for pdf_file_path in split_pdfs:
        s3.upload_file_to_s3(s3_bucket_name, pdf_file_path, "split_pdf_new/" + pdf_file_path.split("/")[-1])

    # update knowledge base
    knowledge_base_id = "YQVYVZJI42"
    ingestion_job_id, status = knowledgebase.refresh_data_source(
        knowledge_base_id=knowledge_base_id,
        s3_bucket_arn=s3.get_s3_bucket_arn(s3_bucket_name),
        s3_prefix="split_pdf_new/",
        data_source_name="S3_new_pdf"
    )

    if status == "COMPLETE":
        return jsonify({"message": f"Knowledge Base updated successfully!"}), 200
    elif status == "FAIL":
        return jsonify({"error": "Failed to update Knowledge Base"}), 500


@app.route("/ask", methods=["POST"])
def ask():
    if request.content_type.startswith('multipart/form-data'):
        user_query = request.form.get("query", "")
        uploaded_file = request.files.get("file")
    else:
        data = request.json
        user_query = data.get("query")
        uploaded_file = None

    if not user_query and not uploaded_file:
        return jsonify({"error": "Missing query or file"}), 400

    if uploaded_file:
        file_bytes = uploaded_file.read()
        extracted_text = extract_text_from_image(file_bytes)
        user_query = extracted_text + "\n" + (user_query or "")

    # Step 1: 檢索 Knowledge Base
    context_parts = []
    for kb_id in knowledge_base_ids:
        response = bart.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": user_query},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5}}
        )
        for doc in response.get("retrievalResults", []):
            text = doc.get("content", {}).get("text", "")
            if text:
                context_parts.append(text.strip())

    context = "\n\n".join(context_parts)

    # Step 2: 準備 Prompt
    prompt = f"""
    你是一位專業的不鏽鋼顧問，請根據以下資料回答使用者問題。

    （規則內容省略）

    [資料]
    {context}

    [問題]
    {user_query}
    """

    # Step 3: 呼叫 LLM
    invoke_request = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "modelId": "amazon.nova-pro-v1:0",
        "inferenceConfig": {"temperature": 0.2, "topP": 0.9, "maxTokens": 1024}
    }

    invoke_response = brt.converse(**invoke_request)
    final_answer = invoke_response["output"]["message"]["content"][0]["text"]

    return jsonify({"answer": final_answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
