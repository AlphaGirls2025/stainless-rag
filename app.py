from flask import Flask, request, jsonify
import boto3
import json

app = Flask(__name__)

# 建立 Bedrock Runtime client 和 Agent Runtime client
brt = boto3.client("bedrock-runtime", region_name="us-east-1")
bart = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

# Knowledge Base IDs
knowledge_base_ids = [
    "FSZ5KXW7FT",
    "CE1KPWLQBC",
    "ALVPHIH9ZC"
]


@app.route("/find_similar_steel", methods=["POST"])
def find_similar_steel():
    model_id = "amazon.nova-pro-v1:0"
    data = request.json
    user_query = data.get("query")

    if not user_query:
        return jsonify({"error": "Missing query"}), 400

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
    
    # Step 2: 查型號的成分資料
    composition_texts = []
    for kb_id in knowledge_base_ids:
        response = bart.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": model_name},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 3}}
        )
        for doc in response.get("retrievalResults", []):
            text = doc.get("content", {}).get("text", "")
            if text and any(element in text for element in ["C", "Cr", "Ni", "Mo", "Mn", "Si", "N", "P", "S"]):
                composition_texts.append(text.strip())

    if not composition_texts:
        return jsonify({"error": "Could not find composition information"}), 404

    # print(composition_texts)
    composition_info = "\n\n".join(composition_texts)

    # # Step 4: 用向量去 Knowledge Base 搜成分類似的鋼種
    similar_context_parts = []
    for kb_id in knowledge_base_ids:
        response = bart.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": composition_info},  # 這裡是 vector，不是 text！
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5}}
        )

        for doc in response.get("retrievalResults", []):
            text = doc.get("content", {}).get("text", "")
            if text:
                similar_context_parts.append(text.strip())

    if not similar_context_parts:
        return jsonify({"error": "Could not find similar steels by vector search"}), 404

    context = "\n\n".join(similar_context_parts)

    # Step 5: 組 prompt，請 LLM 根據成分類似鋼種比較
    number_prompt = f"""
    你是一位專業的不鏽鋼材料工程師，擅長分析各種不鏽鋼鋼種的化學成分差異，並根據成分組成推薦成分類似的鋼種。

    請依照以下規則回答問題：

    規則：
    1. 請以鋼種的化學成分（如 C, Cr, Ni, Mo, Mn, Si, N, P, S 等元素的含量）為主要依據，來評估鋼種之間的相似性。
    2. 成分類似，指的是主要元素（如 Cr, Ni, Mo 等）的比例範圍高度重疊或接近。
    3. 若元素含量略有差異，請同時考慮是否在合理可接受的工業替代範圍內。
    4. 回答時，**必須列出每個推薦鋼種的成分數值（如 Cr: 24–26%, Ni: 6–8%, Mo: 3–5%）**。
    5. 不需要考慮機械性質（如硬度、抗拉強度等），僅考慮化學成分。

    回答格式範例：

    - 推薦相似鋼種：
    - 316L
        - 成分：Cr: 16.0–18.0%, Ni: 10.0–14.0%, Mo: 2.0–3.0%, Mn: 2.0%, Si: 1.0%, C: 0.03%, P: 0.045%, S: 0.03%
        - 說明：Cr、Ni、Mo 含量與目標鋼種316Ti非常接近
    - 317L
        - 成分：Cr: 18.0–20.0%, Ni: 11.0–15.0%, Mo: 3.0–4.0%, ...
        - 說明：較高的 Mo 含量，適合作為抗腐蝕性替代品
    - 321
        - 成分：Cr: 17.0–19.0%, Ni: 9.0–12.0%, C: 0.08%, ...
        - 說明：Cr 含量類似，但以Ti穩定化，略有不同

    現在請根據以下鋼種的成分資料，回答問題。

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
        # print(final_answer)
        return jsonify({
            "query_model": model_name,
            "answer": final_answer
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_query = data.get("query")

    if not user_query:
        return jsonify({"error": "Missing query"}), 400

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
    # print(context)

    # Step 2: 準備 Prompt
    prompt = f"""
    你是一位專業的不鏽鋼顧問，請根據以下資料回答使用者問題。

    請特別注意：
    - 檔案中若提及"ASTM"或"SAE"，代表美國標準（美規）不鏽鋼，文件語言為英語。
    - 若提及"EN"，代表歐洲標準（歐規）不鏽鋼，文件語言為英語。
    - 若提及"JIS"或"JP"，代表日本標準（日規）不鏽鋼，文件語言為日語。
    - 當需要比較鋼種時，請依據其化學成分（如Cr、Ni、C等元素含量）進行比較。
    - 不鏽鋼化學成分中，若標示為一個數字，表示該元素的最大值；若標示為一個範圍（例如 16.0–18.0），表示允許成分範圍。
    - "ASTM A276∕A276M" 棒材 (Bar)
    - "JIS G4303" 棒材 (Bar)
    - "EN 10088-3" 棒材 (Bar)、線材 (wire/wire rods)等…


    請用**簡單清楚的中文**回答下列問題。

    [資料]
    {context}

    [問題]
    {user_query}
    """

    # Step 3: 呼叫 LLM
    invoke_request = {
        "messages": [
            {"role": "user", "content": [{"text": prompt}]}
        ],
        "modelId": "amazon.nova-pro-v1:0",
        # "modelId": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "inferenceConfig": {"temperature": 0.2, "topP": 0.9, "maxTokens": 1024}
    }

    invoke_response = brt.converse(**invoke_request)

    final_answer = invoke_response["output"]["message"]["content"][0]["text"]

    return jsonify({"answer": final_answer})

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=5000, debug=True)
    app.run(host="0.0.0.0", port=5000)
