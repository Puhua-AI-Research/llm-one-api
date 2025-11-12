"""
日志工具

使用 loguru 进行日志记录
"""

import sys
from loguru import logger
from typing import Optional


def setup_logger(name: str = None, level: str = "INFO"):
    """
    配置 loguru logger
    
    Args:
        name: 日志记录器名称（保留参数以兼容旧代码，但 loguru 使用全局 logger）
        level: 日志级别
        
    Returns:
        loguru logger 实例
    """
    # loguru 使用全局 logger，这里只是为了兼容旧的 setup_logger 调用
    # 返回配置好的全局 logger
    return logger


def configure_logger(level: str = "INFO", format_string: str = None):
    """
    配置全局 loguru logger
    
    Args:
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        format_string: 自定义日志格式
    """
    # 移除默认的 handler
    logger.remove()
    
    # 自定义格式
    if format_string is None:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # 添加控制台输出（不写文件）
    logger.add(
        sys.stdout,
        format=format_string,
        level=level.upper(),
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    logger.info(f"日志系统初始化完成，日志级别: {level.upper()}")


# 初始化默认配置
configure_logger(level="INFO")


# 导出 logger 供直接使用
__all__ = ["logger", "setup_logger", "configure_logger"]
