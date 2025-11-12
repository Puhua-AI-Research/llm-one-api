# 统计功能文档

## 📊 统计上报功能

LLM One API 提供了完整的统计上报功能，自动记录每个请求的详细信息，包括：

- ✅ **输入 Token** (prompt_tokens) - 请求消息的 token 数量
- ✅ **输出 Token** (completion_tokens) - 生成响应的 token 数量
- ✅ **总 Token** (total_tokens) - 输入+输出的总计
- ✅ **请求耗时** - 完整请求的处理时间
- ✅ **模型信息** - 使用的模型名称
- ✅ **用户信息** - API Key 标识
- ✅ **流式标识** - 是否为流式请求

## 🔌 统计插件

### 1. 日志统计插件 (log)

将统计信息输出到日志文件或控制台。

#### 配置

```yaml
plugins:
  stats: ["log"]

stats:
  log:
    format: "json"  # 或 "text"
```

#### JSON 格式输出

```json
{
  "event": "response",
  "model": "gpt-3.5-turbo",
  "user": "sk-test-123",
  "endpoint": "chat",
  "stream": false,
  "duration": 2.5,
  "timestamp": "2025-11-12T10:00:00.123456",
  "tokens": {
    "prompt_tokens": 50,
    "completion_tokens": 120,
    "total_tokens": 170
  }
}
```

**适用场景**：
- 需要解析日志进行分析
- 集成到日志收集系统（如 ELK、Splunk）
- 自动化统计分析

#### 文本格式输出

```
📊 响应统计 | 模型=gpt-3.5-turbo | 用户=sk-test-123 | 耗时=2.50s | 输入Token=50 | 输出Token=120 | 总Token=170 | 流式=False
```

**适用场景**：
- 开发调试
- 人工查看日志
- 更易读的格式

### 2. 内存统计插件 (memory)

将统计数据保存在内存中，适合开发和测试。

#### 配置

```yaml
plugins:
  stats: ["memory"]

stats:
  memory:
    max_records: 1000  # 最多保存的记录数
```

#### 功能特点

- ✅ 实时统计每个模型的使用情况
- ✅ 记录最近的请求详情
- ✅ 自动计算平均值
- ✅ 服务关闭时输出汇总统计

#### 统计输出示例

服务关闭或重启时会输出：

```
============================================================
📊 内存统计插件 - 最终统计数据
============================================================
总请求数: 150

模型: gpt-3.5-turbo
  ├─ 总请求数: 120
  ├─ 输入 Token (prompt): 6,500
  ├─ 输出 Token (completion): 18,000
  ├─ 总 Token: 24,500
  ├─ 总耗时: 180.50s
  ├─ 平均 Token/请求: 204.2
  └─ 平均耗时/请求: 1.50s

模型: gpt-4
  ├─ 总请求数: 30
  ├─ 输入 Token (prompt): 2,100
  ├─ 输出 Token (completion): 5,500
  ├─ 总 Token: 7,600
  ├─ 总耗时: 75.30s
  ├─ 平均 Token/请求: 253.3
  └─ 平均耗时/请求: 2.51s

============================================================
```

### 3. 同时使用多个插件

可以同时启用多个统计插件：

```yaml
plugins:
  stats: ["log", "memory"]

stats:
  log:
    format: "json"
  
  memory:
    max_records: 1000
```

## 📈 统计数据说明

### Token 计数

#### 输入 Token (prompt_tokens)
- 包含系统消息、用户消息、历史对话等
- 在发送请求前就已确定
- 影响请求成本和响应时间

#### 输出 Token (completion_tokens)
- 模型生成的响应文本
- 在响应完成后才能确定
- 主要的计费项

#### 总 Token (total_tokens)
```
total_tokens = prompt_tokens + completion_tokens
```

### 流式 vs 非流式

#### 非流式请求
- Token 信息直接从响应的 `usage` 字段获取
- 精确且实时

#### 流式请求
- Token 信息从最后的数据块提取
- 或通过 tiktoken 估算
- 可能略有误差

## 🔧 自定义统计插件

您可以开发自己的统计插件来满足特定需求。

### 创建自定义插件

```python
# my_stats_plugin/database_stats.py

from llm_one_api.plugins.interfaces import StatsPlugin
import psycopg2

class DatabaseStatsPlugin(StatsPlugin):
    """将统计数据存储到数据库"""
    
    def __init__(self, config):
        super().__init__(config)
        self.conn = psycopg2.connect(
            config.get("database_url")
        )
    
    async def record_response(self, response_info):
        """记录到数据库"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO api_stats (
                model, user_id, 
                prompt_tokens, completion_tokens, total_tokens,
                duration, timestamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            response_info['model'],
            response_info['user'],
            response_info['token_usage']['prompt_tokens'],
            response_info['token_usage']['completion_tokens'],
            response_info['token_usage']['total_tokens'],
            response_info['duration'],
            response_info['timestamp']
        ))
        self.conn.commit()
```

### 注册插件

```python
# setup.py
setup(
    entry_points={
        'llm_one_api.stats': [
            'database = my_stats_plugin.database_stats:DatabaseStatsPlugin',
        ],
    }
)
```

### 使用插件

```yaml
plugins:
  stats: ["database"]

stats:
  database:
    database_url: "postgresql://user:pass@localhost/stats"
```

## 📊 统计分析建议

### 1. Token 成本分析

根据统计数据计算成本：

```python
# 价格（示例，单位：美元/1K tokens）
PRICING = {
    "gpt-3.5-turbo": {
        "prompt": 0.0015,
        "completion": 0.002
    },
    "gpt-4": {
        "prompt": 0.03,
        "completion": 0.06
    }
}

def calculate_cost(model, prompt_tokens, completion_tokens):
    price = PRICING.get(model, PRICING["gpt-3.5-turbo"])
    
    prompt_cost = (prompt_tokens / 1000) * price["prompt"]
    completion_cost = (completion_tokens / 1000) * price["completion"]
    
    return prompt_cost + completion_cost

# 例如：
# gpt-3.5-turbo: 50 prompt + 120 completion = $0.00031
# gpt-4: 50 prompt + 120 completion = $0.0087
```

### 2. 性能监控指标

关注以下指标：

- **平均响应时间** - 应该在合理范围内（< 3秒）
- **Token 使用率** - 输入/输出比例是否合理
- **错误率** - 失败请求占比
- **并发量** - 活跃连接数

### 3. 用户行为分析

- 哪些用户使用最频繁？
- 哪些模型最受欢迎？
- 流式 vs 非流式的使用比例？
- 高峰时段分布？

## 🎯 最佳实践

### 1. 日志轮转

如果使用日志统计插件，建议配置日志轮转：

```yaml
logging:
  file: "logs/stats.log"
  rotate: "daily"  # 或 "size:100MB"
  backup_count: 30
```

### 2. 定期导出

定期将内存统计数据导出到持久化存储：

```python
# 定时任务
async def export_stats():
    stats = memory_stats_plugin.get_stats()
    
    # 导出到文件
    with open(f"stats_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
        json.dump(stats, f, indent=2)
```

### 3. 监控告警

基于统计数据设置告警：

```python
# 检查异常
if avg_tokens > 1000:
    alert("Token 使用量过高")

if error_rate > 0.05:
    alert("错误率超过 5%")

if avg_duration > 5.0:
    alert("响应时间过长")
```

### 4. 成本控制

设置每日/每月的 Token 限额：

```python
# 每日限额检查
daily_tokens = sum(stats['total_tokens'] for stats in today_stats)

if daily_tokens > DAILY_LIMIT:
    # 限流或停止服务
    enable_rate_limiting()
```

## 📱 实时监控

结合监控工具使用：

### Prometheus 导出（计划中）

```yaml
# 未来功能
monitoring:
  prometheus:
    enabled: true
    port: 9090
    metrics:
      - request_total
      - request_duration_seconds
      - token_usage_total
      - error_rate
```

### Grafana 仪表板（计划中）

预配置的仪表板显示：
- 实时 QPS
- Token 使用趋势
- 响应时间分布
- 模型使用占比
- 成本趋势

## 🔍 调试和排查

### 查看统计信息

```bash
# 实时查看日志
tail -f logs/llm-one-api.log | grep "📊 响应统计"

# JSON 格式解析
tail -f logs/llm-one-api.log | jq 'select(.event=="response")'

# 统计总 Token
tail -f logs/llm-one-api.log | jq 'select(.event=="response") | .tokens.total_tokens' | awk '{sum+=$1} END {print sum}'
```

## 📚 相关文档

- [配置说明](../README.md#配置)
- [插件开发](../examples/custom_plugin/README.md)
- [API 参考](../README.md#api-文档)

## 🤝 贡献

如果您开发了有用的统计插件，欢迎提交 PR 分享给社区！

