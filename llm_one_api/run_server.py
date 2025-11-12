"""
服务启动入口

使用 fire 库提供命令行接口
使用 uvicorn 多进程模式启动 FastAPI 应用

使用方式:
    python -m llm_one_api.run_server --port 8000 --workers 4
    python -m llm_one_api.run_server --dev
"""

import sys
import fire
import uvicorn
from pathlib import Path
from llm_one_api.utils.logger import configure_logger


def main(
    port: int = 8000,
    host: str = "0.0.0.0",
    workers: int = 4,
    config: str = None,
    dev: bool = False,
    reload: bool = False,
    log_level: str = "INFO",
):
    """
    启动 LLM One API 服务
    
    Args:
        port: 服务端口，默认 8000
        host: 绑定地址，默认 0.0.0.0
        workers: 工作进程数，默认 4（dev 模式下固定为 1）
        config: 配置文件路径，默认使用内置配置
        dev: 开发模式，启用自动重载，单进程
        reload: 是否启用热重载（文件变化自动重启）
        log_level: 日志级别，默认 INFO
    """
    
    # 配置日志系统
    if dev:
        configure_logger(level="DEBUG")
    else:
        configure_logger(level=log_level.upper())
    
    # 如果指定了配置文件，设置环境变量
    if config:
        import os
        os.environ["LLM_ONE_API_CONFIG"] = config
        print(f"使用配置文件: {config}")
    
    # 开发模式配置
    if dev:
        print("🚀 开发模式启动...")
        workers = 1
        reload = True
    
    # 生产模式配置
    if workers > 1 and reload:
        print("⚠️  多进程模式不支持热重载，已禁用 reload")
        reload = False
    
    print(f"🌐 启动服务: http://{host}:{port}")
    print(f"👷 工作进程数: {workers}")
    
    # 启动 uvicorn
    uvicorn.run(
        "llm_one_api.api.app:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,  # reload 模式只能单进程
        reload=reload,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    fire.Fire(main)

