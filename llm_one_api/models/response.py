"""
响应数据模型

定义 OpenAI API 兼容的响应格式
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class Usage(BaseModel):
    """Token 使用量"""
    prompt_tokens: int = Field(..., description="提示 token 数")
    completion_tokens: int = Field(..., description="补全 token 数")
    total_tokens: int = Field(..., description="总 token 数")


class ChatCompletionMessage(BaseModel):
    """聊天补全消息"""
    role: str = Field(..., description="角色")
    content: str = Field(..., description="内容")


class ChatCompletionChoice(BaseModel):
    """聊天补全选项"""
    index: int = Field(..., description="索引")
    message: ChatCompletionMessage = Field(..., description="消息")
    finish_reason: Optional[str] = Field(None, description="结束原因")


class ChatCompletionResponse(BaseModel):
    """聊天补全响应"""
    id: str = Field(..., description="响应ID")
    object: str = Field("chat.completion", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="模型名称")
    choices: List[ChatCompletionChoice] = Field(..., description="选项列表")
    usage: Optional[Usage] = Field(None, description="Token 使用量")


class CompletionChoice(BaseModel):
    """文本补全选项"""
    index: int = Field(..., description="索引")
    text: str = Field(..., description="生成的文本")
    finish_reason: Optional[str] = Field(None, description="结束原因")
    logprobs: Optional[Dict[str, Any]] = Field(None, description="Log 概率")


class CompletionResponse(BaseModel):
    """文本补全响应"""
    id: str = Field(..., description="响应ID")
    object: str = Field("text_completion", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="模型名称")
    choices: List[CompletionChoice] = Field(..., description="选项列表")
    usage: Optional[Usage] = Field(None, description="Token 使用量")


class Embedding(BaseModel):
    """嵌入向量"""
    object: str = Field("embedding", description="对象类型")
    embedding: List[float] = Field(..., description="嵌入向量")
    index: int = Field(..., description="索引")


class EmbeddingResponse(BaseModel):
    """嵌入响应"""
    object: str = Field("list", description="对象类型")
    data: List[Embedding] = Field(..., description="嵌入列表")
    model: str = Field(..., description="模型名称")
    usage: Optional[Usage] = Field(None, description="Token 使用量")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: Dict[str, Any] = Field(..., description="错误信息")

