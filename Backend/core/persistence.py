"""
Phase 8: Data Persistence
Store cleaned data and action logs to Local MySQL Database.
"""

import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
import os
import sqlalchemy
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# DB Config
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "decider_ai")

def get_db_url() -> str:
    """Constructs database URL with database name included."""
    return f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def persist_to_sql(
    df: pd.DataFrame,
    dataset_id: str
) -> str:
    """
    Persist cleaned DataFrame to MySQL.
    """
    engine = create_engine(get_db_url())
    table_name = f"{dataset_id}_cleaned"
    
    try:
        # Write to SQL
        print(f"DEBUG: Persisting to {table_name}...")
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        
        # Verify row count
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
            row_count = result[0] if result else 0
            
        print(f"SUCCESS: Persisted {row_count} rows to MySQL table {table_name}")
        return f"sql:{table_name}"
        
    except Exception as e:
        print(f"ERROR in persist_to_sql: {e}")
        raise e
    finally:
        engine.dispose()

def persist_to_duckdb(df: pd.DataFrame, dataset_id: str, db_path: str = None) -> str:
    """Redirect to SQL persistence."""
    return persist_to_sql(df, dataset_id)

def persist_action_log(
    actions: List[Dict[str, Any]],
    dataset_id: str,
    db_path: str = None
) -> None:
    """
    Persist action log to MySQL.
    """
    if not actions:
        return
        
    engine = create_engine(get_db_url())
    table_name = f"{dataset_id}_action_log"
    
    try:
        action_df = pd.DataFrame(actions)
        action_df['dataset_id'] = dataset_id
        action_df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"SUCCESS: Persisted action log to {table_name}")
    except Exception as e:
        print(f"ERROR in persist_action_log: {e}")
    finally:
        engine.dispose()

def get_dataset_from_sql(dataset_id: str) -> pd.DataFrame:
    """Retrieve dataset from MySQL."""
    engine = create_engine(get_db_url())
    table_name = f"{dataset_id}_cleaned"
    
    try:
        return pd.read_sql(f"SELECT * FROM {table_name}", engine)
    except Exception as e:
        print(f"ERROR in get_dataset_from_sql: {e}")
        return pd.DataFrame()
    finally:
        engine.dispose()

def get_dataset_from_duckdb(dataset_id: str, db_path: str = None) -> pd.DataFrame:
    """Redirect to MySQL retrieval."""
    if dataset_id.startswith("duckdb:") or dataset_id.startswith("sql:"):
        dataset_id = dataset_id.split(":")[1].replace("_cleaned", "")
    return get_dataset_from_sql(dataset_id)

