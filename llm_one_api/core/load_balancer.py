"""
负载均衡器

支持多个上游 LLM API 的负载均衡和故障转移
"""

import random
import time
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field

from llm_one_api.utils.logger import logger


class LoadBalanceStrategy(str, Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"  # 轮询
    RANDOM = "random"  # 随机
    WEIGHTED = "weighted"  # 权重
    LEAST_CONNECTIONS = "least_connections"  # 最少连接


@dataclass
class UpstreamServer:
    """上游服务器配置"""
    api_base: str
    api_key: str
    weight: int = 1  # 权重（用于加权负载均衡）
    timeout: int = 60
    max_retries: int = 3
    
    # 健康检查相关
    healthy: bool = True
    last_check_time: float = 0.0
    consecutive_failures: int = 0
    
    # 连接统计
    active_connections: int = 0
    total_requests: int = 0
    total_failures: int = 0


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(
        self,
        servers: List[Dict[str, Any]],
        strategy: str = "round_robin",
        health_check_interval: int = 30,
        max_failures: int = 3,
    ):
        """
        初始化负载均衡器
        
        Args:
            servers: 上游服务器列表
            strategy: 负载均衡策略
            health_check_interval: 健康检查间隔（秒）
            max_failures: 最大连续失败次数（超过则标记为不健康）
        """
        # 创建 UpstreamServer 对象，只提取需要的字段
        self.servers = []
        for server in servers:
            # 只提取 UpstreamServer 需要的字段
            server_config = {
                "api_base": server.get("api_base", ""),
                "api_key": server.get("api_key", ""),
                "weight": server.get("weight", 1),  # 默认权重为1
                "timeout": server.get("timeout", 60),
                "max_retries": server.get("max_retries", 3),
            }
            self.servers.append(UpstreamServer(**server_config))
        
        self.strategy = LoadBalanceStrategy(strategy)
        self.health_check_interval = health_check_interval
        self.max_failures = max_failures
        
        self._current_index = 0  # 用于轮询策略
        
        # 统计权重总和（用于加权策略）
        total_weight = sum(s.weight for s in self.servers)
        
        logger.info(
            f"负载均衡器初始化: 策略={strategy}, "
            f"服务器数量={len(self.servers)}, "
            f"总权重={total_weight}, "
            f"健康检查间隔={health_check_interval}s"
        )
    
    def get_server(self) -> Optional[UpstreamServer]:
        """
        根据负载均衡策略选择一个服务器
        
        Returns:
            选中的服务器，如果没有可用服务器返回 None
        """
        healthy_servers = [s for s in self.servers if s.healthy]
        
        if not healthy_servers:
            logger.error("没有可用的健康服务器")
            # 尝试重置所有服务器（可能是临时问题）
            self._reset_all_servers()
            healthy_servers = self.servers
        
        if not healthy_servers:
            return None
        
        # 根据策略选择服务器
        if self.strategy == LoadBalanceStrategy.ROUND_ROBIN:
            server = self._round_robin(healthy_servers)
        elif self.strategy == LoadBalanceStrategy.RANDOM:
            server = self._random(healthy_servers)
        elif self.strategy == LoadBalanceStrategy.WEIGHTED:
            server = self._weighted(healthy_servers)
        elif self.strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            server = self._least_connections(healthy_servers)
        else:
            server = healthy_servers[0]
        
        logger.debug(f"选择服务器: {server.api_base}")
        return server
    
    def _round_robin(self, servers: List[UpstreamServer]) -> UpstreamServer:
        """轮询策略"""
        server = servers[self._current_index % len(servers)]
        self._current_index += 1
        return server
    
    def _random(self, servers: List[UpstreamServer]) -> UpstreamServer:
        """随机策略"""
        return random.choice(servers)
    
    def _weighted(self, servers: List[UpstreamServer]) -> UpstreamServer:
        """权重策略"""
        total_weight = sum(s.weight for s in servers)
        if total_weight == 0:
            return servers[0]
        
        rand = random.randint(1, total_weight)
        current_weight = 0
        
        for server in servers:
            current_weight += server.weight
            if rand <= current_weight:
                return server
        
        return servers[-1]
    
    def _least_connections(self, servers: List[UpstreamServer]) -> UpstreamServer:
        """最少连接策略"""
        return min(servers, key=lambda s: s.active_connections)
    
    def _reset_all_servers(self):
        """重置所有服务器状态（用于恢复）"""
        logger.warning("重置所有服务器健康状态")
        for server in self.servers:
            server.healthy = True
            server.consecutive_failures = 0
    
    def mark_request_start(self, server: UpstreamServer):
        """标记请求开始"""
        server.active_connections += 1
        server.total_requests += 1
    
    def mark_request_success(self, server: UpstreamServer):
        """标记请求成功"""
        server.active_connections -= 1
        server.consecutive_failures = 0
        server.healthy = True
        
        logger.debug(
            f"请求成功: {server.api_base}, "
            f"活跃连接={server.active_connections}"
        )
    
    def mark_request_failure(self, server: UpstreamServer, error: Exception = None):
        """标记请求失败"""
        server.active_connections -= 1
        server.total_failures += 1
        server.consecutive_failures += 1
        
        logger.warning(
            f"请求失败: {server.api_base}, "
            f"连续失败={server.consecutive_failures}, "
            f"错误={error}"
        )
        
        # 连续失败超过阈值，标记为不健康
        if server.consecutive_failures >= self.max_failures:
            server.healthy = False
            logger.error(
                f"服务器标记为不健康: {server.api_base}, "
                f"连续失败={server.consecutive_failures}次"
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "strategy": self.strategy.value,
            "total_servers": len(self.servers),
            "healthy_servers": sum(1 for s in self.servers if s.healthy),
            "servers": [
                {
                    "api_base": server.api_base,
                    "healthy": server.healthy,
                    "weight": server.weight,
                    "active_connections": server.active_connections,
                    "total_requests": server.total_requests,
                    "total_failures": server.total_failures,
                    "consecutive_failures": server.consecutive_failures,
                }
                for server in self.servers
            ],
        }
    
    def health_check(self) -> Dict[str, bool]:
        """
        执行健康检查
        
        Returns:
            服务器健康状态字典
        """
        current_time = time.time()
        results = {}
        
        for server in self.servers:
            # 检查是否需要健康检查
            if current_time - server.last_check_time < self.health_check_interval:
                results[server.api_base] = server.healthy
                continue
            
            # TODO: 实现实际的健康检查（发送探测请求）
            # 这里简化处理：如果连续失败次数清零，恢复健康状态
            if not server.healthy and server.consecutive_failures == 0:
                server.healthy = True
                logger.info(f"服务器恢复健康: {server.api_base}")
            
            server.last_check_time = current_time
            results[server.api_base] = server.healthy
        
        return results


class SingleServerWrapper:
    """单服务器包装器（兼容旧的单服务器配置）"""
    
    def __init__(self, api_base: str, api_key: str, timeout: int = 60):
        self.server = UpstreamServer(
            api_base=api_base,
            api_key=api_key,
            timeout=timeout,
        )
    
    def get_server(self) -> UpstreamServer:
        """获取服务器（始终返回同一个）"""
        return self.server
    
    def mark_request_start(self, server: UpstreamServer):
        """标记请求开始"""
        pass
    
    def mark_request_success(self, server: UpstreamServer):
        """标记请求成功"""
        pass
    
    def mark_request_failure(self, server: UpstreamServer, error: Exception = None):
        """标记请求失败"""
        if error:
            logger.warning(f"请求失败: {error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "strategy": "single",
            "total_servers": 1,
            "healthy_servers": 1,
            "servers": [
                {
                    "api_base": self.server.api_base,
                    "healthy": True,
                }
            ],
        }

