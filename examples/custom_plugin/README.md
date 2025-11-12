# 自定义插件开发示例

本目录展示如何开发和使用自定义插件来扩展 LLM One API 的功能。

## 插件类型

LLM One API 支持三种类型的插件：

1. **认证插件** (AuthPlugin) - 自定义认证逻辑
2. **模型路由插件** (ModelRoutePlugin) - 自定义模型配置获取方式
3. **统计插件** (StatsPlugin) - 自定义统计数据记录方式

## 示例：数据库认证插件

### 1. 创建插件文件

```python
# my_auth_plugin/database_auth.py

from llm_one_api.plugins.interfaces import AuthPlugin, AuthResult
import sqlite3

class DatabaseAuthPlugin(AuthPlugin):
    """从数据库验证 API Key"""
    
    def __init__(self, config):
        super().__init__(config)
        self.db_path = config.get("db_path", "auth.db")
    
    async def authenticate(self, api_key: str) -> AuthResult:
        # 连接数据库查询
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT user_id, active FROM api_keys WHERE key = ?",
            (api_key,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result and result[1]:  # 存在且激活
            return AuthResult(
                success=True,
                user_id=result[0],
                message="认证成功"
            )
        
        return AuthResult(
            success=False,
            message="无效的 API Key"
        )
```

### 2. 创建 setup.py

```python
# my_auth_plugin/setup.py

from setuptools import setup, find_packages

setup(
    name="llm-one-api-database-auth",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "llm-one-api>=0.1.0",
    ],
    entry_points={
        'llm_one_api.auth': [
            'database = my_auth_plugin.database_auth:DatabaseAuthPlugin',
        ],
    },
)
```

### 3. 安装插件

```bash
cd my_auth_plugin
pip install -e .
```

### 4. 配置使用

在 `config.yaml` 中启用插件：

```yaml
plugins:
  auth: "database"  # 使用 database 插件

auth:
  database:
    db_path: "/path/to/auth.db"
```

## 示例：Redis 统计插件

```python
# my_stats_plugin/redis_stats.py

from llm_one_api.plugins.interfaces import StatsPlugin, ResponseInfo
import redis

class RedisStatsPlugin(StatsPlugin):
    """将统计数据存储到 Redis"""
    
    def __init__(self, config):
        super().__init__(config)
        self.redis_client = redis.from_url(
            config.get("redis_url", "redis://localhost:6379")
        )
    
    async def record_response(self, response_info: ResponseInfo):
        # 记录到 Redis
        key = f"stats:{response_info.model}:{response_info.user_id}"
        self.redis_client.hincrby(key, "total_requests", 1)
        self.redis_client.hincrby(
            key,
            "total_tokens",
            response_info.token_usage.get("total_tokens", 0)
        )
```

## 最佳实践

1. **错误处理**：插件应该妥善处理异常，避免影响主服务
2. **配置验证**：在 `initialize()` 方法中验证配置
3. **资源清理**：在 `cleanup()` 方法中释放资源
4. **日志记录**：使用统一的日志系统
5. **性能考虑**：避免阻塞操作，使用异步

## 更多示例

查看项目的内置插件实现：
- `llm_one_api/plugins/builtin/default_auth.py`
- `llm_one_api/plugins/builtin/default_router.py`
- `llm_one_api/plugins/builtin/log_stats.py`

