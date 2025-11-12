# 限流配置

防止 API 滥用，保护服务稳定性

## 快速开始

在 `config.yaml` 中启用限流：

```yaml
rate_limit:
  enabled: true
  requests_per_minute: 60  # 每分钟60次请求
```

重启服务后生效：
```bash
python -m llm_one_api.run_server --config config.yaml
```

## 工作原理

### 限流算法

使用**滑动窗口算法**：
- 记录每个用户最近1分钟内的请求时间戳
- 自动清理过期记录
- 超限返回 HTTP 429 状态码

### 用户识别

1. **已认证用户**：按 `user_id` 限流
2. **未认证请求**：按 IP 地址限流

### 响应头

每次响应都会包含限流信息：

```
X-RateLimit-Limit: 60        # 限制值
X-RateLimit-Remaining: 45    # 剩余次数
```

## 配置选项

```yaml
rate_limit:
  enabled: true                  # 是否启用（默认：false）
  requests_per_minute: 60        # 每分钟请求数（默认：60）
```

## 使用示例

### 场景1：开发环境

```yaml
# 开发环境不限流
rate_limit:
  enabled: false
```

### 场景2：生产环境

```yaml
# 适度限流
rate_limit:
  enabled: true
  requests_per_minute: 100
```

### 场景3：公共服务

```yaml
# 严格限流
rate_limit:
  enabled: true
  requests_per_minute: 20
```

## 超限处理

当请求超限时，返回：

```json
{
  "error": {
    "message": "请求过于频繁，请稍后再试",
    "type": "rate_limit_exceeded"
  }
}
```

**HTTP 状态码**: 429 Too Many Requests

## 客户端处理

### Python 示例

```python
import openai
import time

def call_api_with_retry(max_retries=3):
    for i in range(max_retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}]
            )
            return response
        except openai.error.RateLimitError:
            if i < max_retries - 1:
                wait_time = 2 ** i  # 指数退避
                print(f"限流，等待 {wait_time} 秒...")
                time.sleep(wait_time)
            else:
                raise
```

### curl 示例

```bash
# 检查响应头
curl -I http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-test-key"

# 查看限流信息
# X-RateLimit-Limit: 60
# X-RateLimit-Remaining: 59
```

## 监控建议

### 查看日志

启用 DEBUG 日志查看限流详情：

```bash
python -m llm_one_api.run_server --log-level DEBUG
```

当用户超限时，会记录：
```
WARNING | 用户 user-123 超过请求频率限制
```

### 统计分析

结合统计插件查看请求频率：

```yaml
plugins:
  stats: ["log", "memory"]
```

## 高级用法

### 按用户差异化限流

如果需要为不同用户设置不同限制，可以自定义限流中间件：

```python
from llm_one_api.middleware.rate_limit import RateLimitMiddleware

class CustomRateLimitMiddleware(RateLimitMiddleware):
    def get_user_limit(self, user_id):
        # VIP 用户更高限制
        if user_id.startswith("vip-"):
            return 200
        return 60
```

## 注意事项

⚠️ **重要提示**：

1. **内存存储**：当前实现使用内存存储，重启会清空计数
2. **多进程**：每个 worker 独立计数，总限制 = 单进程限制 × workers
3. **生产建议**：大规模部署建议使用 Redis 实现分布式限流

## 生产环境建议

### 推荐配置

```yaml
server:
  workers: 4

rate_limit:
  enabled: true
  requests_per_minute: 100  # 单worker限制
  # 总限制 = 100 × 4 = 400 次/分钟
```

### 升级到 Redis

如需分布式限流（多服务器部署），建议使用 Redis：

```python
# 使用 slowapi + redis
pip install slowapi redis
```

## 常见问题

### Q: 限流计数什么时候重置？

A: 使用滑动窗口，任意1分钟内的请求数不超过限制。

### Q: 多个 worker 怎么办？

A: 每个 worker 独立计数。如果配置 60 次/分钟，4个 worker 实际可处理 240 次/分钟。

### Q: 如何为特定用户解除限制？

A: 修改中间件，添加白名单逻辑。

---

**返回**: [文档首页](README.md)
