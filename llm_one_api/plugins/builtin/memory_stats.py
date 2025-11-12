"""
内存统计插件

将统计数据保存在内存中，适合开发和测试
"""

from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime

from llm_one_api.plugins.interfaces.stats import StatsPlugin, RequestInfo, ResponseInfo
from llm_one_api.utils.logger import setup_logger

logger = setup_logger(__name__)


class MemoryStatsPlugin(StatsPlugin):
    """内存统计插件"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_records = config.get("max_records", 1000)  # 最多保存的记录数
        self.requests: List[Dict] = []
        self.responses: List[Dict] = []
        self.stats_by_model = defaultdict(lambda: {
            "total_requests": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "total_duration": 0.0,
            "total_cost": 0.0,
        })
    
    async def record_request(self, request_info: RequestInfo):
        """
        记录请求信息到内存
        
        Args:
            request_info: 请求信息
        """
        record = {
            "request_id": request_info.request_id,
            "user_id": request_info.user_id,
            "model": request_info.model,
            "endpoint": request_info.endpoint,
            "stream": request_info.stream,
            "timestamp": request_info.timestamp.isoformat(),
        }
        
        self.requests.append(record)
        
        # 限制记录数量
        if len(self.requests) > self.max_records:
            self.requests.pop(0)
    
    async def record_response(self, response_info: Dict[str, Any]):
        """
        记录响应信息到内存
        
        Args:
            response_info: 响应信息字典
        """
        model = response_info.get("model", "unknown")
        token_usage = response_info.get("token_usage", {})
        duration = response_info.get("duration", 0)
        metadata = response_info.get("metadata", {})  # 直接获取传递的 metadata
        
        # 记录详细响应
        self.responses.append(response_info)
        
        # 限制记录数量
        if len(self.responses) > self.max_records:
            self.responses.pop(0)
        
        # 更新模型统计
        stats = self.stats_by_model[model]
        stats["total_requests"] += 1
        stats["total_tokens"] += token_usage.get("total_tokens", 0)
        stats["prompt_tokens"] = stats.get("prompt_tokens", 0) + token_usage.get("prompt_tokens", 0)
        stats["completion_tokens"] = stats.get("completion_tokens", 0) + token_usage.get("completion_tokens", 0)
        stats["total_duration"] += duration
        
        # 计算并累计成本
        cost = self._calculate_cost(token_usage, metadata)
        if cost:
            stats["total_cost"] += cost.get("total_cost", 0)
        
        # 记录模型限制信息（只记录一次）
        if "model_info" not in stats and metadata:
            model_info = self._extract_model_info(metadata)
            if model_info:
                stats["model_info"] = model_info
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计数据
        
        Returns:
            统计数据字典
        """
        return {
            "total_requests": len(self.responses),
            "by_model": dict(self.stats_by_model),
            "recent_requests": self.requests[-10:],  # 最近10条请求
            "recent_responses": self.responses[-10:],  # 最近10条响应
        }
    
    async def initialize(self):
        """初始化插件"""
        logger.info(f"内存统计插件初始化，最大记录数: {self.max_records}")
    
    def _calculate_cost(self, token_usage: Dict[str, int], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算请求成本
        
        Args:
            token_usage: token 使用量
            metadata: 模型元数据（包含价格信息）
            
        Returns:
            成本信息字典
        """
        if not token_usage or not metadata:
            return {}
        
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        
        prompt_price = metadata.get("price_per_1k_prompt_tokens")
        completion_price = metadata.get("price_per_1k_completion_tokens")
        
        if prompt_price is None or completion_price is None:
            return {}
        
        prompt_cost = (prompt_tokens / 1000) * prompt_price
        completion_cost = (completion_tokens / 1000) * completion_price
        total_cost = prompt_cost + completion_cost
        
        return {
            "prompt_cost": round(prompt_cost, 6),
            "completion_cost": round(completion_cost, 6),
            "total_cost": round(total_cost, 6),
            "currency": "USD"
        }
    
    def _extract_model_info(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取模型限制信息
        
        Args:
            metadata: 模型元数据
            
        Returns:
            模型限制信息
        """
        if not metadata:
            return {}
        
        model_info = {}
        for field in ["max_tokens", "max_input_tokens", "max_output_tokens"]:
            if field in metadata:
                model_info[field] = metadata[field]
        
        return model_info
    
    async def cleanup(self):
        """清理插件"""
        # 输出最终统计
        logger.info("=" * 60)
        logger.info("📊 内存统计插件 - 最终统计数据")
        logger.info("=" * 60)
        logger.info(f"总请求数: {len(self.responses)}")
        logger.info("")
        
        total_cost = 0.0
        
        for model, stats in self.stats_by_model.items():
            logger.info(f"模型: {model}")
            logger.info(f"  ├─ 总请求数: {stats['total_requests']}")
            logger.info(f"  ├─ 输入 Token (prompt): {stats['prompt_tokens']:,}")
            logger.info(f"  ├─ 输出 Token (completion): {stats['completion_tokens']:,}")
            logger.info(f"  ├─ 总 Token: {stats['total_tokens']:,}")
            logger.info(f"  ├─ 总耗时: {stats['total_duration']:.2f}s")
            
            if stats['total_requests'] > 0:
                avg_tokens = stats['total_tokens'] / stats['total_requests']
                avg_duration = stats['total_duration'] / stats['total_requests']
                logger.info(f"  ├─ 平均 Token/请求: {avg_tokens:.1f}")
                logger.info(f"  ├─ 平均耗时/请求: {avg_duration:.2f}s")
            
            # 显示成本信息
            model_cost = stats.get('total_cost', 0)
            if model_cost > 0:
                logger.info(f"  ├─ 总成本: ${model_cost:.6f} USD")
                if stats['total_requests'] > 0:
                    avg_cost = model_cost / stats['total_requests']
                    logger.info(f"  ├─ 平均成本/请求: ${avg_cost:.6f} USD")
                total_cost += model_cost
            
            # 显示模型限制信息
            model_info = stats.get('model_info')
            if model_info:
                limits = []
                if model_info.get('max_tokens'):
                    limits.append(f"总={model_info['max_tokens']}")
                if model_info.get('max_input_tokens'):
                    limits.append(f"输入={model_info['max_input_tokens']}")
                if model_info.get('max_output_tokens'):
                    limits.append(f"输出={model_info['max_output_tokens']}")
                if limits:
                    logger.info(f"  ├─ Token 限制: {', '.join(limits)}")
            
            logger.info(f"  └─ 完成")
            logger.info("")
        
        # 显示总成本
        if total_cost > 0:
            logger.info(f"💰 总成本: ${total_cost:.6f} USD")
            logger.info("")
        
        logger.info("=" * 60)

