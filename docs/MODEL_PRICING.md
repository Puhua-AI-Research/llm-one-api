# 模型价格和限制配置

LLM One API 支持在配置中添加模型的价格和限制信息，系统会自动计算每次请求的成本并在日志中上报。

## 📋 目录

- [功能特性](#功能特性)
- [配置说明](#配置说明)
- [价格计算](#价格计算)
- [日志输出](#日志输出)
- [常见模型价格](#常见模型价格)
- [最佳实践](#最佳实践)

## 🎯 功能特性

### 1. 模型限制配置

- **max_tokens**: 模型支持的最大 token 数（总计）
- **max_input_tokens**: 最大输入 token 数
- **max_output_tokens**: 最大输出 token 数

### 2. 价格配置

- **price_per_1k_prompt_tokens**: 输入价格（美元/1K tokens）
- **price_per_1k_completion_tokens**: 输出价格（美元/1K tokens）

### 3. 自动成本计算

系统会根据实际使用的 tokens 自动计算成本：

```
成本 = (输入tokens / 1000) × 输入价格 + (输出tokens / 1000) × 输出价格
```

## 🔧 配置说明

### 两种配置方式

所有可选信息（价格、限制等）都会被统一存储在 `metadata` 中，支持两种配置方式：

#### 方式1：直接写在模型配置下（推荐）

```yaml
models:
  gpt-3.5-turbo:
    api_base: "https://api.openai.com/v1"
    api_key: "your-api-key"
    
    # 直接写在这里，系统会自动放入 metadata
    max_tokens: 4096
    max_input_tokens: 3072
    max_output_tokens: 1024
    price_per_1k_prompt_tokens: 0.0015
    price_per_1k_completion_tokens: 0.002
```

**优点**：简洁明了，易于阅读和维护

#### 方式2：显式放在 metadata 中

```yaml
models:
  gpt-4:
    api_base: "https://api.openai.com/v1"
    api_key: "your-api-key"
    
    # 显式放在 metadata 中
    metadata:
      max_tokens: 8192
      price_per_1k_prompt_tokens: 0.03
      price_per_1k_completion_tokens: 0.06
      
      # 可以添加任何自定义字段
      model_version: "gpt-4-0613"
      provider: "OpenAI"
      custom_field: "any value"
```

**优点**：更灵活，可以添加任何自定义字段

### 完整配置示例

```yaml
server:
  host: "0.0.0.0"
  port: 8000

plugins:
  auth: "simple"
  model_route: "config"
  stats: ["log", "memory"]

stats:
  log:
    format: "text"  # text 格式会显示成本

models:
  # 方式1：直接写在配置下（推荐）
  gpt-3.5-turbo:
    api_base: "https://api.openai.com/v1"
    api_key: "your-openai-api-key"
    max_tokens: 4096
    price_per_1k_prompt_tokens: 0.0015
    price_per_1k_completion_tokens: 0.002
  
  # 方式2：显式使用 metadata
  gpt-4:
    api_base: "https://api.openai.com/v1"
    api_key: "your-openai-api-key"
    metadata:
      max_tokens: 8192
      price_per_1k_prompt_tokens: 0.03
      price_per_1k_completion_tokens: 0.06
      model_version: "gpt-4-0613"  # 自定义字段
  
  # 混合使用也可以
  claude-3-sonnet:
    api_base: "https://api.anthropic.com/v1"
    api_key: "your-anthropic-api-key"
    max_tokens: 200000  # 直接写
    metadata:
      price_per_1k_prompt_tokens: 0.003
      price_per_1k_completion_tokens: 0.015
      provider: "Anthropic"  # 自定义字段
```

## 💰 价格计算

### 计算公式

```python
# 输入成本
prompt_cost = (prompt_tokens / 1000) * price_per_1k_prompt_tokens

# 输出成本
completion_cost = (completion_tokens / 1000) * price_per_1k_completion_tokens

# 总成本
total_cost = prompt_cost + completion_cost
```

### 计算示例

假设使用 GPT-3.5-turbo：
- 输入 tokens: 100
- 输出 tokens: 50
- 输入价格: $0.0015 / 1K tokens
- 输出价格: $0.002 / 1K tokens

```
输入成本 = (100 / 1000) × 0.0015 = $0.00015
输出成本 = (50 / 1000) × 0.002 = $0.0001
总成本 = $0.00025
```

## 📊 日志输出

### 文本格式日志

启用文本格式时（`format: "text"`），每次请求的日志会显示成本：

```
📊 响应统计 | 模型=gpt-3.5-turbo | 用户=user-123 | 耗时=1.23s | 
输入Token=100 | 输出Token=50 | 总Token=150 | 流式=False | 
💰成本=$0.000250 | 限制=4096tokens
```

### JSON 格式日志

启用 JSON 格式时（`format: "json"`），成本信息会包含在 JSON 中：

```json
{
  "event": "response",
  "model": "gpt-3.5-turbo",
  "user": "user-123",
  "duration": 1.23,
  "tokens": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  },
  "model_info": {
    "max_tokens": 4096,
    "max_input_tokens": 3072,
    "max_output_tokens": 1024
  },
  "cost": {
    "prompt_cost": 0.00015,
    "completion_cost": 0.0001,
    "total_cost": 0.00025,
    "currency": "USD"
  }
}
```

### 内存统计汇总

服务关闭时，会显示总成本统计：

```
📊 内存统计插件 - 最终统计数据
============================================================
总请求数: 100

模型: gpt-3.5-turbo
  ├─ 总请求数: 80
  ├─ 输入 Token (prompt): 8,000
  ├─ 输出 Token (completion): 4,000
  ├─ 总 Token: 12,000
  ├─ 总耗时: 95.50s
  ├─ 平均 Token/请求: 150.0
  ├─ 平均耗时/请求: 1.19s
  ├─ 总成本: $0.020000 USD
  ├─ 平均成本/请求: $0.000250 USD
  ├─ Token 限制: 总=4096, 输入=3072, 输出=1024
  └─ 完成

模型: gpt-4
  ├─ 总请求数: 20
  ├─ 输入 Token (prompt): 3,000
  ├─ 输出 Token (completion): 1,500
  ├─ 总 Token: 4,500
  ├─ 总成本: $0.180000 USD
  ├─ 平均成本/请求: $0.009000 USD
  └─ 完成

💰 总成本: $0.200000 USD
============================================================
```

## 📋 常见模型价格

### OpenAI 模型（2024年价格）

| 模型 | 输入价格 | 输出价格 | 最大Tokens |
|------|---------|---------|-----------|
| gpt-3.5-turbo | $0.0015 / 1K | $0.002 / 1K | 4,096 |
| gpt-4 | $0.03 / 1K | $0.06 / 1K | 8,192 |
| gpt-4-turbo | $0.01 / 1K | $0.03 / 1K | 128,000 |
| gpt-4o | $0.005 / 1K | $0.015 / 1K | 128,000 |

### Anthropic 模型

| 模型 | 输入价格 | 输出价格 | 最大Tokens |
|------|---------|---------|-----------|
| claude-3-haiku | $0.00025 / 1K | $0.00125 / 1K | 200,000 |
| claude-3-sonnet | $0.003 / 1K | $0.015 / 1K | 200,000 |
| claude-3-opus | $0.015 / 1K | $0.075 / 1K | 200,000 |

**注意**: 价格可能会变动，请查看官方最新价格。

## 💡 最佳实践

### 1. 定期更新价格

```bash
# 从官方文档获取最新价格
# OpenAI: https://openai.com/pricing
# Anthropic: https://www.anthropic.com/pricing
```

### 2. 成本监控

```yaml
# 启用详细的统计日志
stats:
  log:
    format: "text"  # 实时显示成本
  memory:
    max_records: 10000  # 保存更多记录用于分析
```

### 3. 按用户追踪成本

结合认证插件，可以追踪每个用户的成本：

```yaml
plugins:
  auth: "simple"
  stats: ["log", "memory"]

# 日志会包含用户信息和成本
# 📊 响应统计 | 用户=user-123 | 💰成本=$0.000250
```

### 4. 成本优化建议

#### 选择合适的模型
- **简单任务**: 使用 GPT-3.5-turbo 或 Claude Haiku
- **复杂任务**: 使用 GPT-4 或 Claude Sonnet
- **需要长上下文**: 使用 GPT-4-turbo 或 Claude

#### 优化 Token 使用
```python
# 减少不必要的输出
request = {
    "model": "gpt-3.5-turbo",
    "messages": [...],
    "max_tokens": 100  # 限制输出长度
}

# 使用更精确的提示词
# ❌ 不好：请详细解释...
# ✅ 好：用一句话解释...
```

#### 启用缓存（如果支持）
```yaml
models:
  gpt-3.5-turbo:
    # 一些模型支持缓存来降低成本
    cache_enabled: true
```

### 5. 成本告警

可以结合自定义插件实现成本告警：

```python
class CostAlertPlugin(StatsPlugin):
    async def record_response(self, response_info):
        cost = response_info.get("cost", {}).get("total_cost", 0)
        if cost > 0.01:  # 单次请求超过 $0.01
            logger.warning(f"⚠️ 高成本请求: ${cost:.6f}")
```

### 6. 成本分析

使用内存统计插件获取详细数据：

```python
# 从 API 获取统计数据
import requests

response = requests.get("http://localhost:8000/v1/stats/models/gpt-3.5-turbo")
stats = response.json()

print(f"总成本: ${stats['total_cost']:.6f}")
print(f"平均成本: ${stats['avg_cost']:.6f}")
```

## 🔗 相关文档

- [统计功能](STATISTICS.md)
- [配置说明](QUICKSTART.md)
- [插件开发](../examples/custom_plugin/README.md)

## 📝 配置示例文件

- [examples/config_examples/with_pricing.yaml](../examples/config_examples/with_pricing.yaml) - 带价格配置的完整示例

## ❓ 常见问题

### Q: 价格信息是必须的吗？

A: 不是。所有价格和限制信息都是可选的，如果不配置，系统只会记录 token 使用量，不会计算成本。

### Q: 两种配置方式有什么区别？

A: 
- **方式1**（直接写）：系统会自动将这些字段提取并放入 metadata
- **方式2**（显式 metadata）：直接写在 metadata 中，可以添加任何自定义字段
- 两种方式可以混用，最终都会合并到 metadata 中统一管理

### Q: 价格信息会影响请求吗？

A: 不会。价格信息只用于统计和日志，不会影响实际的 API 请求。

### Q: 如何验证成本计算是否正确？

A: 可以查看日志中的详细成本分解（prompt_cost + completion_cost = total_cost），并与官方账单对比。

### Q: 支持其他货币吗？

A: 目前只支持美元（USD）。价格配置时请统一使用美元。

### Q: 可以按时间段统计成本吗？

A: 可以通过解析日志中的 timestamp 字段来实现时间段统计，或者开发自定义统计插件。

---

**提示**: 定期检查和更新价格信息，确保成本统计的准确性！

