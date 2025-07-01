# MySQL MCP 服务器采样功能使用指南

## 概述

本指南介绍如何使用 MySQL MCP 服务器的采样功能来安全地执行危险的数据库删除操作。采样功能通过 MCP (Model Context Protocol) 的人机交互机制，确保所有危险操作都需要明确的人工确认。

## 采样功能原理

采样功能使用 MCP 的 `SamplingMessage` 和 `TextContent` 来创建交互式确认对话框：

1. **操作预检**: 在执行危险操作前，先查询数据库获取操作影响范围
2. **创建采样消息**: 使用 `SamplingMessage` 向用户显示详细的操作信息
3. **等待用户响应**: 系统暂停等待用户输入确认或取消
4. **验证响应**: 检查用户输入是否匹配预期的确认关键词
5. **执行或取消**: 根据用户响应决定是否执行操作

## 可用的危险操作工具

### 1. 删除表记录 - `delete_records_with_confirmation`

**用途**: 删除表中的特定记录或所有记录

**参数**:
- `table_name`: 表名
- `where_condition`: WHERE 条件（可选，不包含 WHERE 关键字）
- `params`: WHERE 条件参数（可选）

**确认关键词**: `YES`

**示例**:
```python
# 删除特定条件的记录
await delete_records_with_confirmation("users", "age < %s", [18])

# 删除所有记录
await delete_records_with_confirmation("users")
```

**确认对话框示例**:
```
⚠️  危险操作确认 ⚠️

即将执行: 删除表 users 中满足条件 'age < %s' 的记录
将影响 25 行数据
SQL: DELETE FROM `users` WHERE age < %s
参数: [18]
此操作不可逆！

确认删除请回复: YES
取消操作请回复: NO
```

### 2. 清空表 - `truncate_table_with_confirmation`

**用途**: 删除表中所有数据并重置自增计数器

**参数**:
- `table_name`: 表名

**确认关键词**: `YES`

**示例**:
```python
await truncate_table_with_confirmation("logs")
```

**确认对话框示例**:
```
⚠️  危险操作确认 ⚠️

即将清空表: logs
当前包含 1500 行数据
TRUNCATE 操作将:
- 删除所有数据
- 重置自增计数器
- 比 DELETE 更快但不可回滚
此操作不可逆！

确认清空请回复: YES
取消操作请回复: NO
```

### 3. 删除表 - `delete_table_with_confirmation`

**用途**: 完全删除表结构和所有数据

**参数**:
- `table_name`: 表名

**确认关键词**: `YES`

**示例**:
```python
await delete_table_with_confirmation("old_table")
```

**确认对话框示例**:
```
⚠️  危险操作确认 ⚠️

即将删除表: old_table
该表包含 500 行数据
此操作不可逆！

确认删除请回复: YES
取消操作请回复: NO
```

### 4. 删除数据库 - `drop_database_with_confirmation`

**用途**: 删除整个数据库（极度危险）

**参数**:
- `database_name`: 数据库名

**确认关键词**: `DELETE_DATABASE`（特殊确认词）

**示例**:
```python
await drop_database_with_confirmation("test_db")
```

**确认对话框示例**:
```
🚨 极度危险操作确认 🚨

即将删除整个数据库: test_db
该数据库包含 15 个表
所有数据、表结构、索引、触发器等都将被永久删除！
此操作完全不可逆！

如果您完全确定要删除整个数据库，请回复: DELETE_DATABASE
取消操作请回复: NO
```

## 安全机制

### 1. 多层确认
- **操作预检**: 验证目标存在性
- **影响评估**: 显示将要影响的数据量
- **明确确认**: 要求特定的确认关键词
- **最后检查**: 执行前再次验证

### 2. 确认关键词设计
- **普通操作**: 使用 `YES` 作为确认词
- **极危险操作**: 使用 `DELETE_DATABASE` 等特殊确认词
- **大小写不敏感**: 系统会自动转换为大写进行比较
- **精确匹配**: 只有完全匹配才会执行操作

### 3. 错误处理
- **数据库错误**: 捕获并转换为用户友好的错误消息
- **权限错误**: 明确提示权限不足
- **连接错误**: 提供连接问题的诊断信息

## 最佳实践

### 1. 使用前准备
```bash
# 1. 确保有数据备份
mysqldump -u username -p database_name > backup.sql

# 2. 在测试环境中先试用
export MYSQL_DATABASE="test_database"

# 3. 确认权限
# 确保用户有 DROP, DELETE 等必要权限
```

### 2. 操作流程
1. **评估影响**: 先使用查询工具了解数据情况
2. **小范围测试**: 在测试数据上先试用
3. **逐步操作**: 不要一次性删除大量数据
4. **验证结果**: 操作后检查结果是否符合预期

### 3. 应急处理
```python
# 如果误操作，立即检查是否可以恢复
# 1. 检查是否有最近的备份
# 2. 检查 MySQL 的 binlog 是否可以用于恢复
# 3. 联系数据库管理员
```

## 代码示例

### 完整的使用示例
```python
import asyncio
from mysql_explorer import (
    delete_records_with_confirmation,
    list_tables,
    read_query
)

async def cleanup_old_data():
    """清理旧数据的示例"""
    
    # 1. 先查看要删除的数据
    old_records = read_query(
        "SELECT COUNT(*) as count FROM logs WHERE created_at < %s",
        ["2023-01-01"]
    )
    print(f"将要删除 {old_records[0]['count']} 条旧记录")
    
    # 2. 执行删除（会弹出确认对话框）
    result = await delete_records_with_confirmation(
        table_name="logs",
        where_condition="created_at < %s",
        params=["2023-01-01"]
    )
    print(result)

# 运行示例
asyncio.run(cleanup_old_data())
```

### 批量操作示例
```python
async def batch_cleanup():
    """批量清理示例"""
    
    tables_to_clean = ["temp_logs", "cache_data", "session_data"]
    
    for table in tables_to_clean:
        try:
            # 清空每个表
            result = await truncate_table_with_confirmation(table)
            print(f"表 {table}: {result}")
        except Exception as e:
            print(f"清空表 {table} 时出错: {e}")

asyncio.run(batch_cleanup())
```

## 故障排除

### 常见问题

1. **权限不足**
   ```
   错误: MySQL error: (1142, "DROP command denied to user...")
   解决: 确保用户有相应的 DROP/DELETE 权限
   ```

2. **表不存在**
   ```
   错误: Table 'table_name' does not exist
   解决: 使用 list_tables() 检查表名是否正确
   ```

3. **连接失败**
   ```
   错误: MySQL error: (2003, "Can't connect to MySQL server...")
   解决: 检查 MySQL 服务是否运行，网络连接是否正常
   ```

### 调试技巧

1. **启用详细日志**
   ```python
   # 在 mysql_explorer.py 中修改日志级别
   mcp = FastMCP("MySQL Explorer", log_level="DEBUG")
   ```

2. **测试连接**
   ```python
   # 使用基础工具测试连接
   info = get_database_info()
   print(info)
   ```

3. **检查权限**
   ```python
   # 查看当前用户权限
   permissions = read_query("SHOW GRANTS FOR CURRENT_USER()")
   print(permissions)
   ```

## 注意事项

⚠️ **重要警告**:
- 所有删除操作都是不可逆的
- 在生产环境中使用前请充分测试
- 确保有完整的数据备份
- 建议在维护窗口期间执行危险操作
- 对于大型数据库，删除操作可能需要较长时间

🔒 **安全建议**:
- 使用专门的维护账户，限制权限范围
- 记录所有危险操作的执行日志
- 建立操作审批流程
- 定期检查和更新备份策略 