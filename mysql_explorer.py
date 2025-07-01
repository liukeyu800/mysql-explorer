import pymysql
import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from mcp.server import FastMCP

# Initialize FastMCP server
mcp = FastMCP("MySQL Explorer",
    log_level="CRITICAL")

def get_db_config():
    """Get database configuration from environment variables."""
    config = {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "123456"),
        "database": os.getenv("MYSQL_DATABASE", "aircraft"),
        "cursorclass": pymysql.cursors.DictCursor
    }
    
    if not all([config["user"], config["password"], config["database"]]):
        raise ValueError("Missing required database configuration. Please check environment variables: MYSQL_USER, MYSQL_PASSWORD, and MYSQL_DATABASE are required")
    
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
    """Execute a read-only query on the MySQL database and return results.
    
    Args:
        query: Read-only SQL query to execute (SELECT, SHOW, DESCRIBE, EXPLAIN only)
        params: Optional list of parameters for the query
        fetch_all: If True, fetches all results. If False, fetches one row.
        row_limit: Maximum number of rows to return (default 1000)
    
    Returns:
        Dictionary containing query results and metadata
    """
    config = get_db_config()
    
    # Clean and validate the query
    query = query.strip()
    
    # Remove trailing semicolon if present
    if query.endswith(';'):
        query = query[:-1].strip()
    
    # Check for multiple statements by looking for semicolons not inside quotes
    def contains_multiple_statements(sql: str) -> bool:
        in_single_quote = False
        in_double_quote = False
        escaped = False
        for char in sql:
            if escaped:
                escaped = False
                continue
            if char == '\\':
                escaped = True
                continue
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == ';' and not in_single_quote and not in_double_quote:
                return True
        return False
    
    if contains_multiple_statements(query):
        raise ValueError("Multiple SQL statements are not allowed")
    
    # Normalize query for validation
    query_normalized = ' '.join(query.lower().split())
    
    # List of allowed read-only statement prefixes
    allowed_prefixes = [
        'select',
        'show',
        'describe',
        'desc', 
        'explain',
        'with'  # Common Table Expressions that start with WITH
    ]
    
    # Check if query starts with allowed prefix
    if not any(query_normalized.startswith(prefix) for prefix in allowed_prefixes):
        raise ValueError("Only SELECT, WITH, SHOW, DESCRIBE, and EXPLAIN queries are allowed")
    
    # Additional safety checks - block dangerous keywords even in allowed queries
    dangerous_keywords = [
        'insert', 'update', 'delete', 'drop', 'create', 'alter', 
        'truncate', 'replace', 'merge', 'call', 'exec', 'execute',
        'grant', 'revoke', 'set', 'reset', 'flush', 'kill',
        'load', 'import', 'outfile', 'dumpfile', 'into outfile',
        'into dumpfile', 'load_file'
    ]
    
    # Check for dangerous keywords (but allow them in string literals)
    def contains_dangerous_keywords(sql: str) -> tuple[bool, str]:
        # Remove string literals to avoid false positives
        cleaned_sql = sql
        
        # Remove single-quoted strings
        import re
        cleaned_sql = re.sub(r"'[^']*'", "''", cleaned_sql)
        # Remove double-quoted strings  
        cleaned_sql = re.sub(r'"[^"]*"', '""', cleaned_sql)
        # Remove backtick-quoted identifiers
        cleaned_sql = re.sub(r'`[^`]*`', '``', cleaned_sql)
        
        # Normalize whitespace
        cleaned_sql = ' '.join(cleaned_sql.lower().split())
        
        for keyword in dangerous_keywords:
            # Check for keyword as whole word (with word boundaries)
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, cleaned_sql):
                return True, keyword
        return False, ""
    
    has_dangerous, dangerous_word = contains_dangerous_keywords(query_normalized)
    if has_dangerous:
        raise ValueError(f"Query contains potentially dangerous keyword '{dangerous_word}'. Only read-only operations are allowed.")
    
    params = params or []
    
    with MySQLConnection(config) as conn:
        cursor = conn.cursor()
        
        try:
            # Only add LIMIT if query doesn't already have one and it's a SELECT query
            if 'limit' not in query_normalized and query_normalized.startswith('select'):
                query = f"{query} LIMIT {row_limit}"
            
            cursor.execute(query, params)
            
            if fetch_all:
                results = cursor.fetchall()
            else:
                results = [cursor.fetchone()]
                
            # Convert results to list of dictionaries
            result_data = [dict(row) for row in results if row is not None]
            
            # Return query results with metadata
            return {
                "data": result_data,
                "metadata": {
                    "query": query,
                    "params": params,
                    "row_count": len(result_data),
                    "fetch_all": fetch_all,
                    "row_limit": row_limit,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except pymysql.Error as e:
            raise ValueError(f"MySQL error: {str(e)}")

def save_query_results(query: str, data: List[Dict[str, Any]], file_format: str, params: Optional[List[Any]] = None, custom_filename: Optional[str] = None) -> Dict[str, Any]:
    """Save query results to temp_data folder with custom or auto-generated filename.
    
    Args:
        query: The SQL query that was executed
        data: The query results to save
        file_format: Format to save in ('json' or 'csv')
        params: Query parameters used
        custom_filename: Custom filename (without extension). If None, auto-generates.
        
    Returns:
        Dictionary containing file information
    """
    # Ensure temp_data directory exists
    os.makedirs("temp_data", exist_ok=True)
    
    if custom_filename:
        # Use custom filename, sanitize it for safety
        safe_filename = "".join(c for c in custom_filename if c.isalnum() or c in (' ', '_', '-', '.')).strip()
        safe_filename = safe_filename.replace(' ', '_')
        # Remove any existing extension
        if '.' in safe_filename:
            safe_filename = safe_filename.rsplit('.', 1)[0]
        filename = f"{safe_filename}.{file_format}"
    else:
        # Auto-generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a safe filename from query (first 50 chars, replace unsafe chars)
        query_snippet = query.replace('\n', ' ').replace('\r', '')[:50]
        safe_query = "".join(c for c in query_snippet if c.isalnum() or c in (' ', '_', '-')).strip()
        safe_query = safe_query.replace(' ', '_')
        
        filename = f"query_{timestamp}_{safe_query}.{file_format}"
    
    filepath = os.path.join("temp_data", filename)
    
    try:
        if file_format.lower() == 'json':
            # Save as JSON with metadata
            output_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "query": query,
                    "params": params,
                    "row_count": len(data),
                    "filename": filename
                },
                "data": data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
                
        elif file_format.lower() == 'csv':
            # Save as CSV
            if data:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                    
                # Also save metadata as separate JSON file
                metadata_filepath = filepath.replace('.csv', '_metadata.json')
                metadata = {
                    "timestamp": datetime.now().isoformat(),
                    "query": query,
                    "params": params,
                    "row_count": len(data),
                    "csv_file": filename
                }
                with open(metadata_filepath, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
        else:
            raise ValueError(f"Unsupported file format: {file_format}. Use 'json' or 'csv'.")
        
        # Get file size
        file_size = os.path.getsize(filepath)
        
        print(f"SUCCESS: Query results saved to: {filepath}")
        
        # Return only essential file information
        return {
            "filename": filename,
            "format": file_format,
            "size": format_file_size(file_size),
            "row_count": len(data)
        }
        
    except Exception as e:
        print(f"WARNING: Failed to save query results to file: {str(e)}")
        return {
            "error": f"Failed to save file: {str(e)}",
            "row_count": len(data)
        }

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

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
            
            # Extract table names from the results
            # The result format is [{'Tables_in_database_name': 'table_name'}, ...]
            table_names = []
            for row in results:
                # Get the first (and only) value from each row dictionary
                table_name = list(row.values())[0]
                table_names.append(table_name)
            
            return sorted(table_names)
            
        except pymysql.Error as e:
            raise ValueError(f"MySQL error: {str(e)}")

@mcp.tool()
def describe_table(table_name: str) -> List[Dict[str, Any]]:
    """Get detailed information about a table's schema.
    
    Args:
        table_name: Name of the table to describe
        
    Returns:
        List of dictionaries containing column information:
        - Field: Column name
        - Type: Column data type
        - Null: Whether the column can contain NULL values
        - Key: Key information (PRI for primary key, etc.)
        - Default: Default value for the column
        - Extra: Extra information (auto_increment, etc.)
    """
    config = get_db_config()
    
    with MySQLConnection(config) as conn:
        cursor = conn.cursor()
        
        try:
            # Verify table exists
            cursor.execute("SHOW TABLES LIKE %s", [table_name])
            if not cursor.fetchone():
                raise ValueError(f"Table '{table_name}' does not exist")
            
            # Get table schema
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = cursor.fetchall()
            
            return [dict(row) for row in columns]
            
        except pymysql.Error as e:
            raise ValueError(f"MySQL error: {str(e)}")

@mcp.tool()
def show_table_indexes(table_name: str) -> List[Dict[str, Any]]:
    """Show indexes for a specific table.
    
    Args:
        table_name: Name of the table to show indexes for
        
    Returns:
        List of dictionaries containing index information
    """
    config = get_db_config()
    
    with MySQLConnection(config) as conn:
        cursor = conn.cursor()
        
        try:
            # Verify table exists
            cursor.execute("SHOW TABLES LIKE %s", [table_name])
            if not cursor.fetchone():
                raise ValueError(f"Table '{table_name}' does not exist")
            
            # Get table indexes
            cursor.execute(f"SHOW INDEX FROM `{table_name}`")
            indexes = cursor.fetchall()
            
            return [dict(row) for row in indexes]
            
        except pymysql.Error as e:
            raise ValueError(f"MySQL error: {str(e)}")

@mcp.tool()
def show_create_table(table_name: str) -> str:
    """Show the CREATE TABLE statement for a specific table.
    
    Args:
        table_name: Name of the table to show CREATE statement for
        
    Returns:
        The CREATE TABLE statement as a string
    """
    config = get_db_config()
    
    with MySQLConnection(config) as conn:
        cursor = conn.cursor()
        
        try:
            # Verify table exists
            cursor.execute("SHOW TABLES LIKE %s", [table_name])
            if not cursor.fetchone():
                raise ValueError(f"Table '{table_name}' does not exist")
            
            # Get CREATE TABLE statement
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            result = cursor.fetchone()
            
            if result:
                # The result contains table name and create statement
                return list(result.values())[1]  # Get the CREATE TABLE statement
            else:
                raise ValueError(f"Could not retrieve CREATE TABLE statement for '{table_name}'")
            
        except pymysql.Error as e:
            raise ValueError(f"MySQL error: {str(e)}")

@mcp.tool()
def get_database_info() -> Dict[str, Any]:
    """Get general information about the MySQL database.
    
    Returns:
        Dictionary containing database information
    """
    config = get_db_config()
    
    with MySQLConnection(config) as conn:
        cursor = conn.cursor()
        
        try:
            info = {}
            
            # Get database name
            cursor.execute("SELECT DATABASE()")
            result = cursor.fetchone()
            info['database_name'] = list(result.values())[0] if result else None
            
            # Get MySQL version
            cursor.execute("SELECT VERSION()")
            result = cursor.fetchone()
            info['mysql_version'] = list(result.values())[0] if result else None
            
            # Get current user
            cursor.execute("SELECT USER()")
            result = cursor.fetchone()
            info['current_user'] = list(result.values())[0] if result else None
            
            # Get table count
            cursor.execute("SHOW TABLES")
            info['table_count'] = len(cursor.fetchall())
            
            return info
            
        except pymysql.Error as e:
            raise ValueError(f"MySQL error: {str(e)}")

if __name__ == "__main__":
    mcp.run(transport="stdio")