#!/usr/bin/env python3
"""
MySQL Explorer SSE 启动脚本
用于 uv run 调用
"""

def main():
    """启动 MySQL Explorer SSE 服务器"""
    from .mysql_explorer_sse import main as start_server
    start_server()

if __name__ == "__main__":
    main() 