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

    # Step 2: 準備 Prompt
    prompt = f"""
    你是專業不鏽鋼顧問，請根據以下資料回答使用者問題。

    [資料]
    {context}

    [問題]
    {user_query}

    請用簡單清楚的中文回答。
    """

    # Step 3: 呼叫 LLM
    invoke_request = {
        "messages": [
            {"role": "user", "content": [{"text": prompt}]}
        ],
        "modelId": "amazon.nova-pro-v1:0",
        "inferenceConfig": {"temperature": 0.5, "topP": 0.9, "maxTokens": 1024}
    }

    invoke_response = brt.converse(**invoke_request)

    final_answer = invoke_response["output"]["message"]["content"][0]["text"]

    return jsonify({"answer": final_answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
