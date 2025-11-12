"""
通用数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ModelInfo(BaseModel):
    """模型信息"""
    id: str = Field(..., description="模型ID")
    object: str = Field("model", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    owned_by: str = Field(..., description="所有者")


class ModelList(BaseModel):
    """模型列表"""
    object: str = Field("list", description="对象类型")
    data: list[ModelInfo] = Field(..., description="模型列表")

