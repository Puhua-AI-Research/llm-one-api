# 快速开始

5分钟快速上手 LLM One API

## 安装

```bash
git clone https://github.com/yourusername/llm-one-api.git
cd llm-one-api
pip install -e .
```

## 配置

创建 `config.yaml`:

```yaml
auth:
  simple:
    api_keys:
      - "sk-test-key"

models:
  gpt-3.5-turbo:
    api_base: "https://api.openai.com/v1"
    api_key: "sk-your-openai-key"  # 替换为你的 OpenAI Key
    timeout: 60

plugins:
  auth: "simple"
  model_route: "config"
  stats: ["log"]
```

## 启动服务

```bash
# 开发模式（自动重载）
python -m llm_one_api.run_server --dev

# 生产模式
python -m llm_one_api.run_server --config config.yaml --port 8000 --workers 4
```

看到这个输出说明启动成功：
```
✅ LLM One API 启动成功！
🌐 访问地址: http://0.0.0.0:8000
```

## 测试请求

### 使用 curl

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### 使用 Python

```python
import openai

openai.api_base = "http://localhost:8000/v1"
openai.api_key = "sk-test-key"

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

### 流式响应

```python
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "讲个笑话"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.get("content"):
        print(chunk.choices[0].delta.content, end="")
```

## 常用配置

### 配置多个模型

```yaml
models:
  gpt-3.5-turbo:
    api_base: "https://api.openai.com/v1"
    api_key: "sk-openai-key"
  
  claude-3-sonnet:
    api_base: "https://api.anthropic.com/v1"
    api_key: "sk-anthropic-key"
```

### 启用统计

```yaml
plugins:
  stats: ["log", "memory"]

stats:
  log:
    format: "text"  # 或 "json"
```

日志会显示：
```
📊 响应统计 | 模型=gpt-3.5-turbo | 输入Token=10 | 输出Token=20 | 总Token=30
```

## 下一步

- **负载均衡**: 配置多个上游服务器 → [负载均衡文档](LOAD_BALANCING.md)
- **成本统计**: 自动计算 API 成本 → [价格配置文档](MODEL_PRICING.md)
- **插件开发**: 开发自定义插件 → [插件开发指南](../examples/custom_plugin/)

## 常见问题

### 服务启动失败？

检查：
1. Python 版本 >= 3.8
2. 已安装依赖：`pip install -e .`
3. 配置文件格式正确
4. 端口未被占用

### 请求返回 404？

检查：
1. API Base 地址是否正确
2. API Key 是否有效
3. 模型名称是否正确

### 如何查看日志？

```bash
# 设置日志级别为 DEBUG
python -m llm_one_api.run_server --log-level DEBUG
```

---

**需要帮助？** 查看 [完整文档](README.md) 或提交 [Issue](https://github.com/yourusername/llm-one-api/issues)
