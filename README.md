# LLM One API

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**统一的大模型中转服务** - 兼容 OpenAI API 格式，支持多种 LLM 提供商

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🔌 **OpenAI 兼容** | 完全兼容 OpenAI API 格式，无缝切换 |
| ⚖️ **负载均衡** | 多上游服务器，自动故障转移，支持权重分配 |
| 💰 **成本计算** | 自动统计 Token 使用和成本 |
| 🔐 **认证系统** | 灵活的 API Key 管理 |
| 🔌 **插件化** | 易于扩展的插件系统 |
| 🚀 **高性能** | 基于 FastAPI，支持异步和流式响应 |

## 🚀 快速开始

### 1. 安装

```bash
git clone https://github.com/yourusername/llm-one-api.git
cd llm-one-api
pip install -e .
```

### 2. 配置

创建 `config.yaml`：

```yaml
# 认证配置
auth:
  simple:
    api_keys:
      - "sk-your-api-key"

# 模型配置
models:
  gpt-3.5-turbo:
    api_base: "https://api.openai.com/v1"
    api_key: "sk-your-openai-key"
    timeout: 60

plugins:
  auth: "simple"
  model_route: "config"
  stats: ["log"]
```

### 3. 启动

```bash
python -m llm_one_api.run_server --config config.yaml
```

### 4. 使用

```python
import openai

openai.api_base = "http://localhost:8000/v1"
openai.api_key = "sk-your-api-key"

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

或使用 curl：

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello!"}]}'
```

## 📖 文档

| 文档 | 说明 |
|------|------|
| [快速开始](docs/QUICKSTART.md) | 5分钟快速上手指南 |
| [负载均衡](docs/LOAD_BALANCING.md) | 配置多上游服务器和负载均衡 |
| [成本统计](docs/STATISTICS.md) | Token 使用和成本统计 |
| [价格配置](docs/MODEL_PRICING.md) | 配置模型价格，自动计算成本 |
| [配置示例](examples/config_examples/) | 各种场景的配置示例 |
| [插件开发](examples/custom_plugin/) | 开发自定义插件 |

## 🔧 主要功能

### 支持的接口

- ✅ `/v1/chat/completions` - 聊天补全（支持流式）
- ✅ `/v1/completions` - 文本补全
- ✅ `/v1/embeddings` - 文本嵌入
- ✅ `/v1/models` - 模型列表

### 负载均衡配置

```yaml
models:
  gpt-3.5-turbo:
    upstreams:
      - api_base: "https://api1.example.com/v1"
        api_key: "key1"
        weight: 2  # 67% 流量
      - api_base: "https://api2.example.com/v1"
        api_key: "key2"
        weight: 1  # 33% 流量
    load_balance_strategy: "weighted"  # 支持: weighted, round_robin, random
```

### 成本统计

```yaml
models:
  gpt-3.5-turbo:
    api_base: "https://api.openai.com/v1"
    api_key: "sk-xxx"
    max_tokens: 4096
    price_per_1k_prompt_tokens: 0.0015   # 输入价格
    price_per_1k_completion_tokens: 0.002  # 输出价格
```

日志会自动显示成本：
```
📊 响应统计 | 模型=gpt-3.5-turbo | 输入Token=100 | 输出Token=50 | 💰成本=$0.000250
```

## 🔌 插件开发

创建自定义认证插件：

```python
from llm_one_api.plugins.interfaces import AuthPlugin, AuthResult

class MyAuthPlugin(AuthPlugin):
    async def authenticate(self, api_key: str) -> AuthResult:
        if self.validate_key(api_key):
            return AuthResult(success=True, user_id="user123")
        return AuthResult(success=False, message="Invalid key")
```

在 `setup.py` 中注册：

```python
entry_points={
    'llm_one_api.auth': [
        'myauth = my_plugin.auth:MyAuthPlugin',
    ],
}
```

更多示例：[examples/custom_plugin/](examples/custom_plugin/)

## 🏗️ 架构

```
Client → Auth → API Routes → Model Router → Forwarder → Upstream LLM
                                               ↓
                                          Stats Plugin
```

## 📦 命令行选项

```bash
python -m llm_one_api.run_server --help

# 常用选项：
--config CONFIG          # 配置文件路径（默认：config.yaml）
--host HOST              # 监听地址（默认：0.0.0.0）
--port PORT              # 监听端口（默认：8000）
--workers WORKERS        # Worker 数量（默认：4）
--log-level LEVEL        # 日志级别（默认：INFO）
--dev                    # 开发模式（自动重载）
```

## 🧪 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black llm_one_api/
isort llm_one_api/
```

## 📄 许可证

[MIT License](LICENSE)

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [httpx](https://www.python-httpx.org/) - HTTP 客户端
- [loguru](https://github.com/Delgan/loguru) - 日志库

---

💡 **提示**: 查看 [docs/QUICKSTART.md](docs/QUICKSTART.md) 了解更多详细信息
