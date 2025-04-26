import boto3
import json

# 建立 Bedrock Runtime client (for LLM 推理)
brt = boto3.client("bedrock-runtime", region_name="us-east-1")

# 建立 Bedrock Agent Runtime client (for Knowledge Base 檢索)
bart = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

# 設定你的多個 Knowledge Base ID
knowledge_base_ids = [
    "FSZ5KXW7FT",
    "CE1KPWLQBC",
    "ALVPHIH9ZC"
]

# 設定你想問的問題
user_query = "請介紹 ASTM A276 鋼種316Ti"

# Step 1. 呼叫多個 Bedrock Knowledge Base 查詢相關文件
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

# 整理所有檢索結果
context = "\n\n".join(context_parts)

# Step 2. 準備 Prompt，夾 context + 問題
prompt = f"""
你是專業不鏽鋼顧問，請根據以下資料回答使用者問題。

[資料]
{context}

[問題]
{user_query}

請用簡單清楚的中文回答。
"""

# Step 3. 呼叫 Bedrock Claude 3 (Sonnet) 生成回答
invoke_request = {
    "messages": [
        {"role": "user", "content": [{"text": prompt}]}
    ],
    "modelId": "amazon.nova-pro-v1:0",
    "inferenceConfig": {"temperature": 0.5, "topP": 0.9, "maxTokens": 1024}
}

invoke_response = brt.converse(**invoke_request)

# 取得 LLM 回答內容
final_answer = invoke_response["output"]["message"]["content"][0]["text"]

# Step 4. 顯示結果
print("====== LLM回答 ======")
print(final_answer)
