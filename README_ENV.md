# 使用 .env 文件配置环境变量

## ✅ 是的！完全可以！

FastMCP 原生支持 `.env` 文件，这是推荐的配置方式。

## 🚀 快速设置

### 1. 创建 .env 文件

```bash
# 复制示例文件
copy env.example .env
```

### 2. 编辑 .env 文件

```bash
# MySQL 数据库配置
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=chinook

# SSE 服务器配置  
SSE_HOST=localhost
SSE_PORT=3001

# FastMCP 配置（自动读取）
FASTMCP_HOST=localhost
FASTMCP_PORT=3001
FASTMCP_LOG_LEVEL=INFO
```

### 3. 运行服务器

```bash
# 不需要手动设置环境变量，直接运行
uv run run_mysql_sse.py
```

## 🔧 FastMCP 自动支持

FastMCP 具有以下特性：

```python
class Settings(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(
        env_prefix="FASTMCP_",    # 自动读取 FASTMCP_ 前缀的变量
        env_file=".env",          # 自动读取 .env 文件
        extra="ignore",
    )
```

## 🎯 优势

### ✅ 相比手动设置环境变量：

**之前**：
```powershell
$env:MYSQL_PASSWORD = "your_password"
$env:MYSQL_DATABASE = "your_database"
$env:SSE_HOST = "localhost"
$env:SSE_PORT = "3001"
uv run run_mysql_sse.py
```

**现在**：
```bash
# 一次性配置 .env 文件
uv run run_mysql_sse.py
```

### 🛡️ 安全性

- `.env` 文件被 `.gitignore` 忽略
- 密码不会意外提交到版本控制
- 团队成员可以有不同的本地配置

### 📋 维护性

- 集中管理所有配置
- 一目了然所有环境变量
- 易于备份和迁移

## 🎁 额外福利

### 支持多环境

```bash
# 开发环境
.env.development

# 生产环境  
.env.production

# 测试环境
.env.test
```

### uv 原生支持

```bash
# uv 会自动加载 .env 文件
uv run --env-file .env.production run_mysql_sse.py
```

就是这么简单！🎉 