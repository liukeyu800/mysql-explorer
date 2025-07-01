# MySQL Explorer SSE 版本

这是 MySQL Explorer 的 Server-Sent Events (SSE) 版本，通过 HTTP 服务器提供数据库探索功能。

## 主要差异

与 stdio 版本相比，SSE 版本的主要差异：

- **传输方式**: 使用 SSE (Server-Sent Events) 而不是标准输入输出
- **访问方式**: 通过 HTTP 端点访问，而不是命令行工具
- **部署方式**: 可以作为 Web 服务部署，支持远程访问

## 文件说明

- `mysql_explorer_sse.py` - 主要的 MySQL Explorer 代码（SSE 版本）
- `run_sse_server.py` - 启动服务器脚本
- `config_example.txt` - 配置示例文件
- `README_SSE.md` - 本说明文件

## 快速开始

### 1. 环境配置

设置环境变量或创建 `.env` 文件：

```bash
# MySQL 数据库配置
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=your_database

# SSE 服务器配置
export SSE_HOST=localhost
export SSE_PORT=3001
```

### 2. 启动服务器

#### 方式一：使用 uv （推荐）

```bash
cd mysql_explorer_sse
uv run mysql-explorer-sse
```

#### 方式二：直接运行 Python 脚本

```bash
cd mysql_explorer_sse
python run_sse_server.py
```

#### 方式三：作为 MCP 服务器（配合客户端）

在你的 MCP 客户端配置中添加：

```json
{
  "mcpServers": {
    "mysql-explorer-sse": {
      "command": "uv",
      "args": ["run", "--directory", "./mysql_explorer_sse", "mysql-explorer-sse"],
      "env": {
        "MYSQL_HOST": "127.0.0.1",
        "MYSQL_USER": "root",
        "MYSQL_PASSWORD": "your_password",
        "MYSQL_DATABASE": "your_database"
      }
    }
  }
}
```

服务器启动后会显示：
```
启动 MySQL Explorer SSE 服务器...
服务器地址: http://localhost:3001
SSE 端点: http://localhost:3001/sse
按 Ctrl+C 停止服务器
```

### 3. 使用服务

SSE 服务器启动后，客户端可以通过以下方式连接：

- **MCP 客户端**: 配置连接到 `http://localhost:3001/sse`
- **Web 浏览器**: 访问 `http://localhost:3001` 查看服务状态
- **其他工具**: 任何支持 SSE 的客户端

## 可用工具

SSE 版本提供与 stdio 版本相同的工具：

1. **read_query** - 执行只读 SQL 查询
2. **list_tables** - 列出数据库中的所有表
3. **describe_table** - 查看表结构
4. **show_table_indexes** - 显示表索引
5. **show_create_table** - 显示建表语句
6. **get_database_info** - 获取数据库信息

## 安全注意事项

- 确保只在受信任的网络环境中运行
- 配置适当的防火墙规则
- 考虑使用 HTTPS（需要额外配置）
- 定期更新数据库密码

## 故障排除

### 常见问题

1. **端口被占用**
   ```
   OSError: [Errno 48] Address already in use
   ```
   解决方法：更改 `SSE_PORT` 环境变量或终止占用端口的进程

2. **数据库连接失败**
   ```
   ValueError: Missing required database configuration
   ```
   解决方法：检查并设置正确的数据库环境变量

3. **权限不足**
   ```
   PermissionError: [Errno 13] Permission denied
   ```
   解决方法：确保运行用户有权访问指定端口（通常需要 root 权限访问 1024 以下端口）

### 日志查看

服务器运行时会输出关键信息到控制台。如需更详细的日志，可以修改 `mysql_explorer_sse.py` 中的日志级别：

```python
mcp = FastMCP("MySQL Explorer SSE", log_level="INFO")  # 或 "DEBUG"
``` 