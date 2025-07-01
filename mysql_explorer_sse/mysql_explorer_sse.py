#!/usr/bin/env python3
"""
MySQL 数据库探索工具 - SSE (Server-Sent Events) 版本

通过 HTTP Server-Sent Events 提供 MySQL 数据库探索功能。
支持执行 SQL 查询、浏览表结构、导出数据等操作。
"""

import os
import socket
import pymysql
import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取服务器配置
SSE_HOST = os.getenv("SSE_HOST", "localhost")
SSE_PORT = int(os.getenv("SSE_PORT", "3001"))

# 初始化 FastMCP 服务器，指定端口和主机
mcp = FastMCP("MySQL Explorer SSE", host=SSE_HOST, port=SSE_PORT)

def get_db_config():
    """从环境变量获取数据库配置信息
    
    返回:
        dict: 包含数据库连接所需的配置信息
        - host: 数据库主机地址
        - port: 数据库端口  
        - user: 数据库用户名
        - password: 数据库密码
        - database: 数据库名称
        
    异常:
        ValueError: 当必需的配置信息缺失时抛出
    """
    config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
        "charset": "utf8mb4",
        "autocommit": True
    }
    
    if not all([config["user"], config["password"], config["database"]]):
        raise ValueError("缺少必需的数据库配置信息。请设置 MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE 环境变量。")
    
    return config

class MySQLConnection:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.conn = None
        
    def __enter__(self):
        self.conn = pymysql.connect(**self.config)
        return self.conn
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

@mcp.tool()
def read_query(
    query: str,
    params: Optional[List[Any]] = None,
    fetch_all: bool = True,
    row_limit: int = 1000
) -> Dict[str, Any]:
    """Execute a SELECT query on the MySQL database.
    
    Args:
        query: SELECT SQL query to execute
        params: Optional list of parameters for the query
        fetch_all: If True, fetches all results. If False, fetches one row.
        row_limit: Maximum number of rows to return (default 1000)
    
    Returns:
        Dictionary containing:
        - data: List of dictionaries with query results
        - row_count: Number of rows returned
        - columns: List of column names
        - query_info: Information about the executed query
    """
    config = get_db_config()
    
    # 清理和验证查询
    query = query.strip()
    
    # 移除末尾分号
    if query.endswith(';'):
        query = query[:-1].strip()
    
    # 检查多语句查询
    def contains_multiple_statements(sql: str) -> bool:
        in_single_quote = False
        in_double_quote = False
        for char in sql:
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == ';' and not in_single_quote and not in_double_quote:
                return True
        return False
    
    if contains_multiple_statements(query):
        raise ValueError("不允许多语句查询，请一次只执行一条语句")
    
    # 检查危险关键词
    def contains_dangerous_keywords(sql: str) -> tuple[bool, str]:
        # 移除字符串字面量以避免误报
        sql_no_strings = sql
        import re
        sql_no_strings = re.sub(r"'[^']*'", "", sql_no_strings)
        sql_no_strings = re.sub(r'"[^"]*"', "", sql_no_strings)
        
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 
            'TRUNCATE', 'REPLACE', 'GRANT', 'REVOKE', 'SET', 'CALL',
            'EXECUTE', 'PREPARE', 'DEALLOCATE', 'LOCK', 'UNLOCK',
            'START TRANSACTION', 'COMMIT', 'ROLLBACK', 'SAVEPOINT'
        ]
        
        sql_upper = sql_no_strings.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return True, keyword
        return False, ""
    
    # 验证查询类型
    query_lower = query.lower().strip()
    if not any(query_lower.startswith(prefix) for prefix in ('select', 'show', 'describe', 'desc', 'explain', 'with')):
        # 检查是否包含危险关键词
        is_dangerous, dangerous_keyword = contains_dangerous_keywords(query)
        if is_dangerous:
            raise ValueError(f"检测到可能的危险操作: {dangerous_keyword}。为了安全，只允许执行 SELECT, SHOW, DESCRIBE, EXPLAIN 和 WITH 查询。")
        else:
            raise ValueError("为了安全，只允许执行 SELECT, SHOW, DESCRIBE, EXPLAIN 和 WITH 查询。")
    
    params = params or []
    
    with MySQLConnection(config) as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        try:
            # 只对 SELECT 查询添加 LIMIT
            if query_lower.startswith('select') and 'limit' not in query_lower:
                query = f"{query} LIMIT {row_limit}"
            
            cursor.execute(query, params)
            
            if fetch_all:
                results = cursor.fetchall()
            else:
                result = cursor.fetchone()
                results = [result] if result else []
            
            # 获取列名
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # 转换结果为普通字典列表
            data = [dict(row) for row in results]
            
            return {
                "data": data,
                "row_count": len(data),
                "columns": columns,
                "query_info": {
                    "query": query,
                    "params": params,
                    "row_limit": row_limit
                }
            }
            
        except pymysql.Error as e:
            raise ValueError(f"MySQL 错误: {str(e)}")

@mcp.tool()
def execute_sql(query: str) -> List[str]:
    """执行SQL查询语句（兼容性工具，建议使用 read_query）
    
    参数:
        query (str): 要执行的SQL语句
        
    返回:
        list: 包含查询结果的文本列表
    """
    try:
        result = read_query(query)
        
        if not result["data"]:
            return ["查询未返回任何结果"]
        
        # 转换为CSV格式
        lines = []
        if result["columns"]:
            lines.append(",".join(result["columns"]))
        
        for row in result["data"]:
            formatted_row = []
            for col in result["columns"]:
                value = row.get(col)
                if value is None:
                    formatted_row.append("NULL")
                else:
                    formatted_row.append(str(value))
            lines.append(",".join(formatted_row))
        
        return ["\n".join(lines)]
        
    except Exception as e:
        return [f"执行查询时出错: {str(e)}"]

@mcp.tool()
def list_tables() -> List[str]:
    """List all tables in the MySQL database.
    
    Returns:
        List of table names in the database
    """
    config = get_db_config()
    
    with MySQLConnection(config) as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("SHOW TABLES")
            results = cursor.fetchall()
            
            # 提取表名 - results 是元组列表，每个元组包含一个表名
            table_names = [row[0] for row in results]
            return sorted(table_names)
            
        except pymysql.Error as e:
            raise ValueError(f"MySQL 错误: {str(e)}")

@mcp.tool()
def describe_table(table_name: str) -> List[Dict[str, Any]]:
    """Get detailed information about a table's schema.
    
    Args:
        table_name: Name of the table to describe
        
    Returns:
        List of dictionaries containing column information
    """
    config = get_db_config()
    
    with MySQLConnection(config) as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        try:
            # 验证表是否存在
            cursor.execute("SHOW TABLES LIKE %s", [table_name])
            if not cursor.fetchone():
                raise ValueError(f"表 '{table_name}' 不存在")
            
            # 获取表结构
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = cursor.fetchall()
            
            return [dict(row) for row in columns]
            
        except pymysql.Error as e:
            raise ValueError(f"MySQL 错误: {str(e)}")

@mcp.tool()
def get_table_name(text: str) -> List[str]:
    """根据表的中文注释搜索数据库中的表名
    
    参数:
        text (str): 要搜索的表中文注释关键词
        
    返回:
        list: 包含匹配表信息的文本列表
    """
    config = get_db_config()
    sql = ("SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_COMMENT "
           f"FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{config['database']}' "
           f"AND TABLE_COMMENT LIKE '%{text}%'")
    return execute_sql(sql)

@mcp.tool()
def get_table_desc(text: str) -> List[str]:
    """获取指定表的字段结构信息
    
    参数:
        text (str): 要查询的表名，多个表名以逗号分隔
        
    返回:
        list: 包含字段信息的文本列表
    """
    config = get_db_config()
    table_names = [name.strip() for name in text.split(",")]
    table_condition = "','".join(table_names)
    sql = ("SELECT TABLE_NAME, COLUMN_NAME, COLUMN_COMMENT "
           f"FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '{config['database']}' "
           f"AND TABLE_NAME IN ('{table_condition}') ORDER BY TABLE_NAME, ORDINAL_POSITION")
    return execute_sql(sql)

@mcp.tool()
def get_lock_tables() -> List[str]:
    """获取当前MySQL服务器InnoDB的行级锁信息
    
    返回:
        list: 包含锁信息的文本列表
    """
    sql = """SELECT
    p2.`HOST` AS 被阻塞方host,
    p2.`USER` AS 被阻塞方用户,
    r.trx_id AS 被阻塞方事务id,
    r.trx_mysql_thread_id AS 被阻塞方线程号,
    TIMESTAMPDIFF(SECOND, r.trx_wait_started, CURRENT_TIMESTAMP) AS 等待时间,
    r.trx_query AS 被阻塞的查询,
    l.OBJECT_NAME AS 阻塞方锁住的表,
    m.LOCK_MODE AS 被阻塞方的锁模式,
    m.LOCK_TYPE AS '被阻塞方的锁类型(表锁还是行锁)',
    m.INDEX_NAME AS 被阻塞方锁住的索引,
    m.OBJECT_SCHEMA AS 被阻塞方锁对象的数据库名,
    m.OBJECT_NAME AS 被阻塞方锁对象的表名,
    m.LOCK_DATA AS 被阻塞方事务锁定记录的主键值,
    p.`HOST` AS 阻塞方主机,
    p.`USER` AS 阻塞方用户,
    b.trx_id AS 阻塞方事务id,
    b.trx_mysql_thread_id AS 阻塞方线程号,
    b.trx_query AS 阻塞方查询,
    l.LOCK_MODE AS 阻塞方的锁模式,
    l.LOCK_TYPE AS '阻塞方的锁类型(表锁还是行锁)',
    l.INDEX_NAME AS 阻塞方锁住的索引,
    l.OBJECT_SCHEMA AS 阻塞方锁对象的数据库名,
    l.OBJECT_NAME AS 阻塞方锁对象的表名,
    l.LOCK_DATA AS 阻塞方事务锁定记录的主键值,
    IF(p.COMMAND = 'Sleep', CONCAT(p.TIME, ' 秒'), 0) AS 阻塞方事务空闲的时间
    FROM performance_schema.data_lock_waits w
    INNER JOIN performance_schema.data_locks l ON w.BLOCKING_ENGINE_LOCK_ID = l.ENGINE_LOCK_ID
    INNER JOIN performance_schema.data_locks m ON w.REQUESTING_ENGINE_LOCK_ID = m.ENGINE_LOCK_ID
    INNER JOIN information_schema.INNODB_TRX b ON b.trx_id = w.BLOCKING_ENGINE_TRANSACTION_ID
    INNER JOIN information_schema.INNODB_TRX r ON r.trx_id = w.REQUESTING_ENGINE_TRANSACTION_ID
    INNER JOIN information_schema.PROCESSLIST p ON p.ID = b.trx_mysql_thread_id
    INNER JOIN information_schema.PROCESSLIST p2 ON p2.ID = r.trx_mysql_thread_id
    ORDER BY 等待时间 DESC"""
    
    return execute_sql(sql)

@mcp.tool()
def get_database_info() -> Dict[str, Any]:
    """Get general information about the MySQL database.
    
    Returns:
        Dictionary containing database information
    """
    config = get_db_config()
    
    with MySQLConnection(config) as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        try:
            info = {}
            
            # 获取数据库名
            cursor.execute("SELECT DATABASE()")
            result = cursor.fetchone()
            info['database_name'] = list(result.values())[0] if result else None
            
            # 获取MySQL版本
            cursor.execute("SELECT VERSION()")
            result = cursor.fetchone()
            info['mysql_version'] = list(result.values())[0] if result else None
            
            # 获取当前用户
            cursor.execute("SELECT USER()")
            result = cursor.fetchone()
            info['current_user'] = list(result.values())[0] if result else None
            
            # 获取表数量
            cursor.execute("SHOW TABLES")
            info['table_count'] = len(cursor.fetchall())
            
            return info
            
        except pymysql.Error as e:
            raise ValueError(f"MySQL 错误: {str(e)}")

def main():
    """主入口点函数"""
    print(f"🚀 启动 MySQL Explorer SSE 服务器...")
    print(f"📍 服务器地址: http://{SSE_HOST}:{SSE_PORT}")
    print(f"🔗 SSE 端点: http://{SSE_HOST}:{SSE_PORT}/sse")
    print("⚡ 按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    try:
        # 检查数据库配置
        config = get_db_config()
        print(f"📋 数据库配置:")
        print(f"   主机: {config['host']}:{config['port']}")
        print(f"   数据库: {config['database']}")
        print(f"   用户: {config['user']}")
        print()
        
        # 测试数据库连接
        with MySQLConnection(config) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            print("✅ 数据库连接测试成功")
        
        print("🔄 启动 FastMCP SSE 服务器...")
        mcp.run(transport="sse")
        
    except KeyboardInterrupt:
        print("\n✅ 服务器已停止")
    except Exception as e:
        print(f"❌ 启动服务器时发生错误: {e}")
        print(f"💡 建议:")
        print(f"   1. 检查数据库连接配置")
        print(f"   2. 确保 MySQL 服务器正在运行")
        print(f"   3. 检查端口 {SSE_PORT} 是否被占用")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main() 