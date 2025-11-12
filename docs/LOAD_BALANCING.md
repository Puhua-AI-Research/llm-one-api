## 负载均衡功能

LLM One API 支持多个上游服务器的负载均衡和故障转移，提高服务的可用性和性能。

## 🎯 核心特性

- ✅ **多种策略**: 轮询、随机、权重、最少连接
- ✅ **自动故障转移**: 自动切换到健康的服务器
- ✅ **健康检查**: 定期检查服务器健康状态
- ✅ **连接统计**: 跟踪每个服务器的连接和失败情况
- ✅ **向后兼容**: 支持单服务器配置

## 📋 负载均衡策略

### 1. 轮询 (Round Robin)

按顺序依次分配请求到每个服务器。

```yaml
models:
  gpt-3.5-turbo:
    upstreams:
      - api_base: "https://api.openai.com/v1"
        api_key: "sk-key-1"
      - api_base: "https://api-proxy1.com/v1"
        api_key: "sk-key-2"
      - api_base: "https://api-proxy2.com/v1"
        api_key: "sk-key-3"
    load_balance_strategy: "round_robin"  # 默认策略
```

**适用场景**: 服务器性能相近，希望均匀分配流量

### 2. 随机 (Random)

随机选择一个服务器处理请求。

```yaml
models:
  gpt-4:
    upstreams:
      - api_base: "https://api.openai.com/v1"
        api_key: "sk-key-1"
      - api_base: "https://api-backup.com/v1"
        api_key: "sk-key-2"
    load_balance_strategy: "random"
```

**适用场景**: 简单快速的负载分配，无需保持状态

### 3. 加权 (Weighted)

根据权重分配流量，权重越高的服务器获得更多请求。

```yaml
models:
  gpt-4-turbo:
    upstreams:
      - api_base: "https://api.openai.com/v1"
        api_key: "sk-main-key"
        weight: 8  # 80% 的流量
      - api_base: "https://api-backup.com/v1"
        api_key: "sk-backup-key"
        weight: 2  # 20% 的流量
    load_balance_strategy: "weighted"
```

**适用场景**: 服务器性能不同，或主备场景

### 4. 最少连接 (Least Connections)

选择当前活跃连接数最少的服务器。

```yaml
models:
  claude-3:
    upstreams:
      - api_base: "https://api.anthropic.com/v1"
        api_key: "sk-key-1"
      - api_base: "https://api-proxy.com/v1"
        api_key: "sk-key-2"
    load_balance_strategy: "least_connections"
```

**适用场景**: 请求处理时间差异大，希望避免某个服务器过载

## 🔧 配置选项

### 完整配置示例

```yaml
models:
  gpt-3.5-turbo:
    # 上游服务器列表
    upstreams:
      - api_base: "https://api.openai.com/v1"
        api_key: "sk-openai-key"
        weight: 3          # 权重（仅用于 weighted 策略）
        timeout: 60        # 超时时间（秒）
      
      - api_base: "https://api.openai-backup.com/v1"
        api_key: "sk-backup-key"
        weight: 1
        timeout: 60
    
    # 负载均衡策略
    load_balance_strategy: "weighted"
    
    # 健康检查间隔（秒）
    health_check_interval: 30
    
    # 最大连续失败次数（超过后标记为不健康）
    max_failures: 3
```

### 配置参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `upstreams` | List | - | 上游服务器列表 |
| `load_balance_strategy` | String | "round_robin" | 负载均衡策略 |
| `health_check_interval` | Int | 30 | 健康检查间隔（秒） |
| `max_failures` | Int | 3 | 最大连续失败次数 |

### 单个上游服务器参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `api_base` | String | ✅ | API 基础地址 |
| `api_key` | String | ✅ | API 密钥 |
| `weight` | Int | ❌ | 权重（默认 1） |
| `timeout` | Int | ❌ | 超时时间（默认 60秒） |

## 🚦 故障转移机制

### 自动故障检测

1. **请求失败计数**: 每次请求失败，服务器的连续失败计数 +1
2. **健康状态切换**: 连续失败达到 `max_failures` 次，标记为不健康
3. **自动跳过**: 不健康的服务器会被暂时跳过
4. **自动恢复**: 定期健康检查，恢复健康状态

### 重试逻辑

非流式请求会自动重试（最多 3 次）：

```python
# 第1次尝试 -> 失败（服务器A）
# 第2次尝试 -> 选择服务器B
# 第3次尝试 -> 选择服务器C
# 如果都失败 -> 返回错误
```

**注意**: 流式请求不支持自动重试（因为已经开始返回数据）

## 📊 监控和统计

### 查看负载均衡器状态

```bash
curl http://localhost:8000/v1/stats/load_balancers \
  -H "Authorization: Bearer sk-your-key"
```

### 查看指定模型统计

```bash
curl http://localhost:8000/v1/stats/models/gpt-3.5-turbo \
  -H "Authorization: Bearer sk-your-key"
```

## 💡 使用场景

### 场景 1: 提高可用性

使用多个 API 提供商，一个失败自动切换到另一个。

```yaml
models:
  gpt-3.5-turbo:
    upstreams:
      - api_base: "https://api.openai.com/v1"
        api_key: "sk-openai-key"
      - api_base: "https://api.azure.openai.com/v1"
        api_key: "sk-azure-key"
      - api_base: "https://api.cloudflare-workers.com/v1"
        api_key: "sk-cf-key"
    load_balance_strategy: "round_robin"
    max_failures: 2
```

### 场景 2: 主备模式

主服务器处理大部分流量，备用服务器作为保障。

```yaml
models:
  gpt-4:
    upstreams:
      - api_base: "https://api.openai.com/v1"
        api_key: "sk-main-key"
        weight: 9  # 90% 流量
      - api_base: "https://api-backup.com/v1"
        api_key: "sk-backup-key"
        weight: 1  # 10% 流量
    load_balance_strategy: "weighted"
```

### 场景 3: 区域就近访问

根据地理位置配置不同区域的服务器。

```yaml
models:
  gpt-3.5-turbo:
    upstreams:
      - api_base: "https://api-us.openai.com/v1"    # 美国
        api_key: "sk-us-key"
      - api_base: "https://api-eu.openai.com/v1"    # 欧洲
        api_key: "sk-eu-key"
      - api_base: "https://api-asia.openai.com/v1"  # 亚洲
        api_key: "sk-asia-key"
    load_balance_strategy: "random"
```

### 场景 4: 流量控制和成本优化

使用多个账号分散流量，避免单账号限流。

```yaml
models:
  gpt-4:
    upstreams:
      - api_base: "https://api.openai.com/v1"
        api_key: "sk-account1-key"
        weight: 1
      - api_base: "https://api.openai.com/v1"
        api_key: "sk-account2-key"
        weight: 1
      - api_base: "https://api.openai.com/v1"
        api_key: "sk-account3-key"
        weight: 1
    load_balance_strategy: "round_robin"
```

## ⚠️ 注意事项

### 1. 流式请求的限制

流式请求**不支持中途切换服务器**，因为：
- 响应已经开始返回给客户端
- 无法回滚已发送的数据
- 会导致客户端收到不完整的响应

**解决方案**: 流式请求只在开始时选择一次服务器，如果失败会返回错误。

### 2. API Key 管理

- 确保所有上游服务器的 API Key 都有效
- 定期检查 API Key 的额度和有效期
- 为不同服务器使用不同的 Key 以便追踪

### 3. 超时设置

- 根据实际网络情况调整 `timeout` 值
- 不同服务器可能需要不同的超时时间
- 超时过短会导致频繁失败

### 4. 权重配置

- 权重总和不需要等于 100
- 权重比例决定流量分配
- 权重为 0 的服务器不会被选中

## 🔍 日志示例

启用负载均衡后，您会看到类似的日志：

```
2025-11-12 10:00:00.123 | INFO | llm_one_api.core.forwarder | 启用负载均衡: 服务器数量=3, 策略=round_robin
2025-11-12 10:00:01.234 | DEBUG | llm_one_api.core.load_balancer | 选择服务器: https://api.openai.com/v1
2025-11-12 10:00:02.345 | WARNING | llm_one_api.core.load_balancer | 请求失败: https://api.openai.com/v1, 连续失败=1, 错误=Connection timeout
2025-11-12 10:00:02.346 | WARNING | llm_one_api.core.forwarder | 服务器 https://api.openai.com/v1 请求失败 (尝试 1/3): Connection timeout
2025-11-12 10:00:02.347 | DEBUG | llm_one_api.core.load_balancer | 选择服务器: https://api-backup.com/v1
2025-11-12 10:00:03.456 | DEBUG | llm_one_api.core.load_balancer | 请求成功: https://api-backup.com/v1, 活跃连接=0
```

## 📚 相关文档

- [配置示例](../examples/config_examples/load_balance.yaml)
- [架构设计](../DESIGN.md)
- [API 参考](../README.md#api-文档)

## 🤝 贡献

如果您有改进建议或发现问题，欢迎提交 Issue 或 Pull Request！

