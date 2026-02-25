"""
Phase 2: Data Standardization
Clean and normalize data by handling nulls and empty rows.


- String values are stripped of whitespace.
- Common null placeholders are converted to np.nan.
- Completely empty rows are removed.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any


def standardize(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Standardize data by cleaning nulls and removing empty rows.
    
    Args:
        df: Raw DataFrame from ingestion
        
    Returns:
        Tuple of (standardized DataFrame, log dict)
    """
    initial_rows = len(df)
    initial_shape = df.shape
    
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # Strip whitespace from string columns
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    
    # Replace common null placeholders with np.nan
    null_placeholders = ['', 'NA', 'N/A', 'null', 'NULL', 'None', 'NONE', 'nan', 'NaN', '-', '--']
    df = df.replace(null_placeholders, np.nan)
    
    # Count nulls before removing empty rows
    nulls_replaced = df.isna().sum().sum()
    
    # Remove completely empty rows (all columns are NaN)
    df_before_drop = df.copy()
    df = df.dropna(how='all')
    empty_rows_removed = len(df_before_drop) - len(df)
    
    # Reset index
    df = df.reset_index(drop=True)
    
    # Create log
    log = {
        'rows_before': initial_rows,
        'rows_after': len(df),
        'empty_rows_removed': empty_rows_removed,
        'nulls_replaced': int(nulls_replaced),
        'shape_before': initial_shape,
        'shape_after': df.shape
    }
    
    return df, log
