"""
SQL Query Tool for Dynamic Data Analysis
Allows the chat agent to execute validated SQL queries against DuckDB.
"""


import re
from typing import Dict, Any, List

class SQLQueryTool:
    """
    Executes SQL queries against DuckDB with safety validation.
    """
    
    def __init__(self, db_path: str = "agent_data.db"):
        self.db_path = db_path
        
    def validate_query(self, query: str) -> tuple[bool, str]:
        """
        Validates SQL query for safety.
        Returns: (is_valid, error_message)
        """
        query_lower = query.lower().strip()
        
        # 1. Only allow SELECT queries
        if not query_lower.startswith('select'):
            return False, "Only SELECT queries are allowed"
        
        # 2. Block dangerous keywords
        dangerous_keywords = [
            'drop', 'delete', 'insert', 'update', 'alter', 
            'create', 'truncate', 'exec', 'execute'
        ]
        
        for keyword in dangerous_keywords:
            if re.search(rf'\b{keyword}\b', query_lower):
                return False, f"Dangerous keyword '{keyword}' not allowed"
        
        # 3. Limit result size (must have LIMIT clause)
        if 'limit' not in query_lower:
            return False, "Query must include a LIMIT clause (max 100)"
        
        # 4. Extract and validate LIMIT value
        limit_match = re.search(r'limit\s+(\d+)', query_lower)
        if limit_match:
            limit_val = int(limit_match.group(1))
            if limit_val > 100:
                return False, "LIMIT cannot exceed 100 rows"
        
        return True, ""
    
    def execute_query(self, query: str, dataset_id: str, bypass_validation: bool = False) -> Dict[str, Any]:
        """
        Executes a validated SQL query and returns results.
        
        Args:
            query: SQL SELECT query
            dataset_id: Dataset ID to query
            bypass_validation: If True, skips safety checks (LIMIT, restricted keywords). 
                               Use ONLY for internal trusted agents (Prediction/Diagnostic).
        """
        # Validate query ONLY if not bypassed
        if not bypass_validation:
            is_valid, error = self.validate_query(query)
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Query validation failed: {error}",
                    "data": [],
                    "columns": [],
                    "row_count": 0
                }
        
        try:
            # Connect to MySQL
            from sqlalchemy import create_engine, text
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            
            DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
            DB_PORT = os.getenv("DB_PORT", "3306")
            DB_USER = os.getenv("DB_USER", "root")
            DB_PASSWORD = os.getenv("DB_PASSWORD", "")
            DB_NAME = os.getenv("DB_NAME", "decider_ai")
            
            db_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            engine = create_engine(db_url)
            
            # Replace placeholder table name with actual dataset table
            # User might write: SELECT * FROM data LIMIT 10
            # We replace with: SELECT * FROM ds_6a20c7e5_cleaned LIMIT 10
            # Note: MySQL tables from persistence.py are named "{dataset_id}_cleaned"
            query_adjusted = query.replace('FROM data', f'FROM {dataset_id}_cleaned')
            query_adjusted = query_adjusted.replace('from data', f'FROM {dataset_id}_cleaned')
            # Handle quoted variations just in case
            query_adjusted = query_adjusted.replace('FROM "data"', f'FROM {dataset_id}_cleaned')
            
            # Execute query
            with engine.connect() as conn:
                result = conn.execute(text(query_adjusted))
                columns = list(result.keys())
                data = [dict(zip(columns, row)) for row in result.fetchall()]
            
            engine.dispose()
            
            return {
                "success": True,
                "data": data,
                "columns": columns,
                "row_count": len(data),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Query execution failed: {str(e)}",
                "data": [],
                "columns": [],
                "row_count": 0
            }

# Singleton instance
sql_tool = SQLQueryTool()

def query_data(query: str, dataset_id: str, bypass_validation: bool = False) -> Dict[str, Any]:
    """
    Helper function to query data from DuckDB.
    
    Example:
        result = query_data(
            "SELECT ...",
            "ds_6a20c7e5",
            bypass_validation=True # For internal agents
        )
    """
    return sql_tool.execute_query(query, dataset_id, bypass_validation)

from langchain_core.tools import tool

@tool
def execute_sql_query(query: str) -> str:
    """
    Execute a SQL query against the dataset. 
    Use ONLY if the answer is NOT in the pre-computed aggregates/KPIs.
    Query must SELECT from 'data' table with LIMIT clause.
    """
    # Logic is handled manually in the graph, this is just for schema binding
    return ""
