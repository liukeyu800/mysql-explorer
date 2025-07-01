# MySQL Explorer MCP Server

这是一个基于 FastMCP 的 MySQL 数据库探索服务器，仿照 SQLite Explorer 的形式构建。
mcpo --port 8001 --config config.json
## 功能特性

- **安全的查询执行**: 只允许 SELECT、WITH、SHOW、DESCRIBE 和 EXPLAIN 查询
- **表结构探索**: 列出表、查看表结构、索引信息
- **连接管理**: 自动管理数据库连接的打开和关闭
- **参数化查询**: 支持参数化查询以防止 SQL 注入
- **结果限制**: 自动限制查询结果数量以防止内存溢出
- **人工确认删除**: 使用 MCP 采样功能进行危险操作的人工确认

## 环境变量配置

在使用之前，需要设置以下环境变量：

```bash
# 必需的环境变量
export MYSQL_USER="your_username"
export MYSQL_PASSWORD="your_password"
export MYSQL_DATABASE="your_database"

# 可选的环境变量（有默认值）
export MYSQL_HOST="127.0.0.1"        # 默认: 127.0.0.1
export MYSQL_PORT="3306"              # 默认: 3306
```

## 可用工具

### 查询和探索工具

### 1. read_query
执行 SQL 查询并返回结果。

**参数:**
- `query` (str): 要执行的 SQL 查询
- `params` (List[Any], 可选): 查询参数
- `fetch_all` (bool): 是否获取所有结果，默认 True
- `row_limit` (int): 最大返回行数，默认 1000

**示例:**
```python
read_query("SELECT * FROM users WHERE age > %s", [18])
```

### 2. list_tables
列出数据库中的所有表。

**返回:** 表名列表

### 3. describe_table
获取表的详细结构信息。

**参数:**
- `table_name` (str): 表名

**返回:** 包含列信息的字典列表，包括：
- Field: 列名
- Type: 数据类型
- Null: 是否允许 NULL
- Key: 键信息（PRI 表示主键）
- Default: 默认值
- Extra: 额外信息（如 auto_increment）

### 4. show_table_indexes
显示表的索引信息。

**参数:**
- `table_name` (str): 表名

**返回:** 索引信息的字典列表

### 5. show_create_table
显示表的 CREATE TABLE 语句。

**参数:**
- `table_name` (str): 表名

**返回:** CREATE TABLE 语句字符串

### 6. get_database_info
获取数据库的基本信息。

**返回:** 包含以下信息的字典：
- database_name: 数据库名
- mysql_version: MySQL 版本
- current_user: 当前用户
- table_count: 表数量

### 危险操作工具（需要人工确认）

### 7. delete_table_with_confirmation
删除整个表（需要人工确认）。

**参数:**
- `table_name` (str): 要删除的表名

**功能:**
- 显示表的行数信息
- 要求用户回复 "YES" 确认删除
- 执行 DROP TABLE 操作

### 8. delete_records_with_confirmation
删除表中的记录（需要人工确认）。

**参数:**
- `table_name` (str): 表名
- `where_condition` (str, 可选): WHERE 条件（不包含 WHERE 关键字）
- `params` (List[Any], 可选): WHERE 条件的参数

**功能:**
- 显示将要删除的记录数量
- 显示完整的 DELETE SQL 语句
- 要求用户回复 "YES" 确认删除

**示例:**
```python
# 删除特定条件的记录
delete_records_with_confirmation("users", "age < %s", [18])

# 删除所有记录
delete_records_with_confirmation("users")
```

### 9. truncate_table_with_confirmation
清空表（删除所有记录并重置自增计数器，需要人工确认）。

**参数:**
- `table_name` (str): 要清空的表名

**功能:**
- 显示当前表的行数
- 说明 TRUNCATE 与 DELETE 的区别
- 要求用户回复 "YES" 确认清空

### 10. drop_database_with_confirmation
删除整个数据库（需要人工确认）。

**参数:**
- `database_name` (str): 要删除的数据库名

**功能:**
- 显示数据库中的表数量
- 警告这是极度危险的操作
- 要求用户回复 "DELETE_DATABASE" 确认删除

## 安全特性

1. **查询类型限制**: 只允许读取操作（SELECT、WITH、SHOW、DESCRIBE、EXPLAIN）
2. **多语句防护**: 防止执行多个 SQL 语句
3. **参数化查询**: 支持参数化查询防止 SQL 注入
4. **结果限制**: 自动限制查询结果数量
5. **连接管理**: 使用上下文管理器确保连接正确关闭
6. **人工确认**: 所有危险操作都需要通过 MCP 采样功能进行人工确认
7. **操作预览**: 在执行前显示将要影响的数据量和具体操作

## 采样功能说明

危险操作工具使用 MCP 的采样功能来实现人工交互确认：

1. **操作预检**: 在执行危险操作前，先检查操作的影响范围
2. **详细提示**: 显示操作类型、影响的数据量、SQL 语句等详细信息
3. **明确确认**: 要求用户输入特定的确认文本（如 "YES" 或 "DELETE_DATABASE"）
4. **安全取消**: 任何非确认回复都会取消操作
5. **操作反馈**: 执行后提供详细的操作结果反馈

## 运行服务器

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export MYSQL_USER="your_username"
export MYSQL_PASSWORD="your_password"
export MYSQL_DATABASE="your_database"

# 运行服务器
python mysql_explorer.py
```

## 与 SQLite Explorer 的差异

1. **连接方式**: 使用网络连接而非文件路径
2. **查询语法**: 支持 MySQL 特有的 SHOW 和 DESCRIBE 语句
3. **数据类型**: 返回 MySQL 特有的数据类型信息
4. **额外功能**: 
   - `show_table_indexes`: 查看表索引
   - `show_create_table`: 查看建表语句
   - `get_database_info`: 获取数据库信息
   - **采样确认工具**: 支持需要人工确认的危险删除操作

## 错误处理

服务器会捕获并转换 MySQL 错误为用户友好的错误消息，包括：
- 连接错误
- 权限错误
- 语法错误
- 表不存在错误

## 注意事项

1. 确保 MySQL 服务器正在运行且可访问
2. 确保提供的用户有足够的权限访问指定数据库
3. 对于大型结果集，建议使用 LIMIT 子句
4. 服务器会自动为 SELECT 查询添加 LIMIT 限制
5. **危险操作警告**: 删除操作是不可逆的，请谨慎使用
6. **权限要求**: 删除操作需要相应的数据库权限（DROP、DELETE 等） 