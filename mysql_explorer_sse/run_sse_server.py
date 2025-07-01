#!/usr/bin/env python3
"""
启动 MySQL Explorer SSE 服务器

这个脚本启动一个 HTTP 服务器，通过 Server-Sent Events (SSE) 提供 MySQL 数据库探索功能。
"""

import os
import sys
from . import mysql_explorer_sse as mcp

def main():
    """启动 SSE 服务器"""
    # 获取端口配置，默认使用 3001
    port = int(os.getenv("SSE_PORT", "3001"))
    host = os.getenv("SSE_HOST", "localhost")
    
    print(f"启动 MySQL Explorer SSE 服务器...")
    print(f"服务器地址: http://{host}:{port}")
    print(f"SSE 端点: http://{host}:{port}/sse")
    print("按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    try:
        # 设置环境变量供 FastMCP 使用
        os.environ["FASTMCP_HOST"] = host
        os.environ["FASTMCP_PORT"] = str(port)
        
        # 运行 SSE 服务器
        mcp.run(transport="sse")
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动服务器时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 