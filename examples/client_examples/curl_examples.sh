#!/bin/bash

# LLM One API 的 curl 调用示例

API_BASE="http://localhost:8000"
API_KEY="sk-your-api-key"

echo "=== 聊天补全（非流式） ==="
curl "${API_BASE}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'

echo -e "\n\n=== 聊天补全（流式） ==="
curl "${API_BASE}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -N \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Count to 5"}
    ],
    "stream": true
  }'

echo -e "\n\n=== 文本补全 ==="
curl "${API_BASE}/v1/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "model": "gpt-3.5-turbo",
    "prompt": "Once upon a time",
    "max_tokens": 50
  }'

echo -e "\n\n=== 列出模型 ==="
curl "${API_BASE}/v1/models" \
  -H "Authorization: Bearer ${API_KEY}"

echo -e "\n\n=== 健康检查 ==="
curl "${API_BASE}/health"

