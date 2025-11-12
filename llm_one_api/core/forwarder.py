"""
请求转发器

负责将请求转发到目标 LLM API，并处理响应
分为流式和非流式两种转发器
支持负载均衡和故障转移
"""

import json
import httpx
from typing import Dict, Any, AsyncIterator, Union
from datetime import datetime

from llm_one_api.utils.logger import logger
from llm_one_api.utils.exceptions import LLMOneAPIError, UpstreamError
from llm_one_api.core.token_extractor import TokenExtractor
from llm_one_api.core.load_balancer import LoadBalancer, SingleServerWrapper, UpstreamServer


class BaseForwarder:
    """转发器基类"""
    
    def __init__(self, model_config: Dict[str, Any], plugin_manager):
        self.model_config = model_config
        self.plugin_manager = plugin_manager
        
        # 初始化负载均衡器
        self.load_balancer = self._create_load_balancer(model_config)
    
    def _create_load_balancer(self, config: Dict[str, Any]) -> Union[LoadBalancer, SingleServerWrapper]:
        """创建负载均衡器"""
        # 检查是否配置了多个上游服务器
        upstreams = config.get("upstreams")
        
        if upstreams and isinstance(upstreams, list):
            if len(upstreams) > 1:
                # 多服务器：使用负载均衡器
                strategy = config.get("load_balance_strategy", "round_robin")
                health_check_interval = config.get("health_check_interval", 30)
                max_failures = config.get("max_failures", 3)
                
                logger.info(
                    f"启用负载均衡: 服务器数量={len(upstreams)}, "
                    f"策略={strategy}"
                )
                
                return LoadBalancer(
                    servers=upstreams,
                    strategy=strategy,
                    health_check_interval=health_check_interval,
                    max_failures=max_failures,
                )
            else:
                # 单个 upstream：从 upstreams[0] 获取配置
                upstream = upstreams[0]
                api_base = upstream.get("api_base", "").rstrip("/")
                api_key = upstream.get("api_key")
                timeout = upstream.get("timeout", 60)
                
                logger.info(f"使用单个上游: {api_base}")
                
                return SingleServerWrapper(
                    api_base=api_base,
                    api_key=api_key,
                    timeout=timeout,
                )
        else:
            # 旧格式配置：直接从顶层获取
            api_base = config.get("api_base", "").rstrip("/")
            api_key = config.get("api_key")
            timeout = config.get("timeout", 60)
            
            logger.info(f"使用传统配置: {api_base}")
            
            return SingleServerWrapper(
                api_base=api_base,
                api_key=api_key,
                timeout=timeout,
            )
    
    def _get_headers(self, api_key: str) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    
    async def _execute_with_retry(self, request_func, *args, **kwargs):
        """
        执行请求并支持重试（故障转移）
        
        Args:
            request_func: 请求函数
            *args, **kwargs: 请求参数
        """
        last_error = None
        
        # 尝试所有可用服务器
        for attempt in range(3):  # 最多重试3次
            server = self.load_balancer.get_server()
            
            if not server:
                raise UpstreamError("没有可用的上游服务器")
            
            try:
                self.load_balancer.mark_request_start(server)
                
                # 执行请求
                result = await request_func(server, *args, **kwargs)
                
                self.load_balancer.mark_request_success(server)
                return result
            
            except Exception as e:
                self.load_balancer.mark_request_failure(server, e)
                last_error = e
                
                logger.warning(
                    f"服务器 {server.api_base} 请求失败 (尝试 {attempt + 1}/3): {e}"
                )
                
                # 如果还有其他服务器，继续尝试
                continue
        
        # 所有服务器都失败了
        raise last_error or UpstreamError("所有上游服务器均不可用")


class NonStreamForwarder(BaseForwarder):
    """非流式转发器"""
    
    async def _do_forward(self, server: UpstreamServer, url: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行实际的转发请求"""
        async with httpx.AsyncClient(timeout=server.timeout) as client:
            response = await client.post(
                url,
                json=request_data,
                headers=self._get_headers(server.api_key),
            )
            
            response.raise_for_status()
            return response.json()
    
    async def forward_chat(self, request_data: Dict[str, Any], auth_result: Dict) -> Dict[str, Any]:
        """
        转发聊天请求（非流式）
        支持负载均衡和故障转移
        
        Args:
            request_data: 请求数据
            auth_result: 认证结果
            
        Returns:
            响应数据
        """
        start_time = datetime.now()
        
        try:
            # 使用负载均衡和重试机制
            async def request_func(server: UpstreamServer):
                url = f"{server.api_base}/chat/completions"
                return await self._do_forward(server, url, request_data)
            
            response_data = await self._execute_with_retry(request_func)
            
            # 提取 token 使用量
            token_usage = TokenExtractor.extract_from_response(response_data)
            
            # 计算耗时
            duration = (datetime.now() - start_time).total_seconds()
            
            # 记录统计
            await self._record_stats(request_data, response_data, token_usage, duration, auth_result)
            
            return response_data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"上游 API 返回错误: {e.response.status_code} - {e.response.text}")
            raise UpstreamError(
                f"上游 API 错误: {e.response.status_code}",
                status_code=e.response.status_code,
            )
        
        except httpx.TimeoutException:
            logger.error(f"请求超时")
            raise UpstreamError("请求超时", status_code=504)
        
        except Exception as e:
            logger.exception(f"转发请求失败: {e}")
            raise UpstreamError(f"转发失败: {str(e)}")
    
    async def forward_completion(self, request_data: Dict[str, Any], auth_result: Dict) -> Dict[str, Any]:
        """转发文本补全请求（非流式）"""
        start_time = datetime.now()
        
        try:
            async def request_func(server: UpstreamServer):
                url = f"{server.api_base}/completions"
                return await self._do_forward(server, url, request_data)
            
            response_data = await self._execute_with_retry(request_func)
            
            token_usage = TokenExtractor.extract_from_response(response_data)
            duration = (datetime.now() - start_time).total_seconds()
            await self._record_stats(request_data, response_data, token_usage, duration, auth_result)
            
            return response_data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"上游 API 返回错误: {e.response.status_code}")
            raise UpstreamError(f"上游 API 错误: {e.response.status_code}", status_code=e.response.status_code)
        
        except Exception as e:
            logger.exception(f"转发请求失败: {e}")
            raise UpstreamError(f"转发失败: {str(e)}")
    
    async def forward_embedding(self, request_data: Dict[str, Any], auth_result: Dict) -> Dict[str, Any]:
        """转发嵌入请求"""
        start_time = datetime.now()
        
        try:
            async def request_func(server: UpstreamServer):
                url = f"{server.api_base}/embeddings"
                return await self._do_forward(server, url, request_data)
            
            response_data = await self._execute_with_retry(request_func)
            
            token_usage = TokenExtractor.extract_from_response(response_data)
            duration = (datetime.now() - start_time).total_seconds()
            await self._record_stats(request_data, response_data, token_usage, duration, auth_result)
            
            return response_data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"上游 API 返回错误: {e.response.status_code}")
            raise UpstreamError(f"上游 API 错误: {e.response.status_code}", status_code=e.response.status_code)
        
        except Exception as e:
            logger.exception(f"转发请求失败: {e}")
            raise UpstreamError(f"转发失败: {str(e)}")
    
    async def _record_stats(
        self,
        request_data: Dict,
        response_data: Dict,
        token_usage: Dict,
        duration: float,
        auth_result: Dict,
    ):
        """记录统计信息"""
        try:
            model_name = request_data.get("model")
            
            # 获取模型配置并提取 metadata
            model_config = await self.plugin_manager.get_model_config(model_name)
            metadata = model_config.get("metadata", {}) if model_config else {}
            
            stats_data = {
                "model": model_name,
                "endpoint": "chat" if "messages" in request_data else "completion",
                "stream": False,
                "user": auth_result.get("user_id"),
                "timestamp": datetime.now().isoformat(),
                "duration": duration,
                "token_usage": token_usage,
                "metadata": metadata,  # 直接传递 metadata
            }
            
            await self.plugin_manager.record_request_stats(stats_data)
        except Exception as e:
            logger.warning(f"记录统计信息失败: {e}")


class StreamForwarder(BaseForwarder):
    """流式转发器"""
    
    async def forward_chat_stream(
        self,
        request_data: Dict[str, Any],
        auth_result: Dict,
    ) -> AsyncIterator[str]:
        """
        转发聊天请求（流式）
        支持负载均衡（但流式不做自动故障转移，因为已经开始响应）
        
        Args:
            request_data: 请求数据
            auth_result: 认证结果
            
        Yields:
            SSE 格式的数据块
        """
        start_time = datetime.now()
        
        # 确保请求是流式的
        request_data["stream"] = True
        
        token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        # 选择一个服务器（流式不支持中途切换）
        server = self.load_balancer.get_server()
        
        if not server:
            yield 'data: {"error": "没有可用的上游服务器"}\n\n'
            return
        
        url = f"{server.api_base}/chat/completions"
        self.load_balancer.mark_request_start(server)
        
        try:
            async with httpx.AsyncClient(timeout=server.timeout) as client:
                async with client.stream(
                    "POST",
                    url,
                    json=request_data,
                    headers=self._get_headers(server.api_key),
                ) as response:
                    response.raise_for_status()
                    
                    # 逐块转发
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        # 转发原始数据
                        yield f"{line}\n\n"
                        
                        # 提取 token 信息（不影响转发）
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str != "[DONE]":
                                try:
                                    chunk_data = json.loads(data_str)
                                    chunk_usage = TokenExtractor.extract_from_stream_chunk(chunk_data)
                                    if chunk_usage:
                                        # 累加 token
                                        for key in ["prompt_tokens", "completion_tokens", "total_tokens"]:
                                            token_usage[key] = max(token_usage[key], chunk_usage.get(key, 0))
                                except json.JSONDecodeError:
                                    pass
            
            # 成功完成
            self.load_balancer.mark_request_success(server)
            
            # 记录统计
            duration = (datetime.now() - start_time).total_seconds()
            await self._record_stats(request_data, token_usage, duration, auth_result)
        
        except httpx.HTTPStatusError as e:
            self.load_balancer.mark_request_failure(server, e)
            error_message = f"data: {{\"error\": \"上游 API 错误: {e.response.status_code}\"}}\n\n"
            yield error_message
            logger.error(f"流式请求错误: {e.response.status_code}")
        
        except Exception as e:
            self.load_balancer.mark_request_failure(server, e)
            error_message = f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            yield error_message
            logger.exception(f"流式转发失败: {e}")
    
    async def forward_completion_stream(
        self,
        request_data: Dict[str, Any],
        auth_result: Dict,
    ) -> AsyncIterator[str]:
        """转发文本补全请求（流式）"""
        start_time = datetime.now()
        request_data["stream"] = True
        token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        # 选择一个服务器
        server = self.load_balancer.get_server()
        
        if not server:
            yield 'data: {"error": "没有可用的上游服务器"}\n\n'
            return
        
        url = f"{server.api_base}/completions"
        self.load_balancer.mark_request_start(server)
        
        try:
            async with httpx.AsyncClient(timeout=server.timeout) as client:
                async with client.stream(
                    "POST",
                    url,
                    json=request_data,
                    headers=self._get_headers(server.api_key),
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        yield f"{line}\n\n"
                        
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str != "[DONE]":
                                try:
                                    chunk_data = json.loads(data_str)
                                    chunk_usage = TokenExtractor.extract_from_stream_chunk(chunk_data)
                                    if chunk_usage:
                                        for key in ["prompt_tokens", "completion_tokens", "total_tokens"]:
                                            token_usage[key] = max(token_usage[key], chunk_usage.get(key, 0))
                                except json.JSONDecodeError:
                                    pass
            
            self.load_balancer.mark_request_success(server)
            duration = (datetime.now() - start_time).total_seconds()
            await self._record_stats(request_data, token_usage, duration, auth_result)
        
        except Exception as e:
            self.load_balancer.mark_request_failure(server, e)
            error_message = f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            yield error_message
            logger.exception(f"流式转发失败: {e}")
    
    async def _record_stats(
        self,
        request_data: Dict,
        token_usage: Dict,
        duration: float,
        auth_result: Dict,
    ):
        """记录统计信息（流式）"""
        try:
            model_name = request_data.get("model")
            
            # 获取模型配置并提取 metadata
            model_config = await self.plugin_manager.get_model_config(model_name)
            metadata = model_config.get("metadata", {}) if model_config else {}
            
            stats_data = {
                "model": model_name,
                "endpoint": "chat" if "messages" in request_data else "completion",
                "stream": True,
                "user": auth_result.get("user_id"),
                "timestamp": datetime.now().isoformat(),
                "duration": duration,
                "token_usage": token_usage,
                "metadata": metadata,  # 直接传递 metadata
            }
            
            await self.plugin_manager.record_request_stats(stats_data)
        except Exception as e:
            logger.warning(f"记录统计信息失败: {e}")

