"""
Phase 3: Schema Inference
Detect column types using deterministic rules.

"""


"""
How does schema inference work:
- For each column, we analyze the data to determine its type: numeric, data, categorical, or string.
- We use configurable thresholds to decide the type based on the proportion of parseable values.
- We apply heuristics based on column names to improve detection accuracy for dates and IDs.
- The output is a schema list indicating the inferred type for each column.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from dateutil import parser as date_parser


def infer_schema(df: pd.DataFrame, config: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Infer schema by detecting column types using deterministic rules.
    
    Args:
        df: Standardized DataFrame
        config: Configuration dictionary
        
    Returns:
        List of schema entries: [{"column": str, "type": str}, ...]
    """
    thresholds = config['coercion_thresholds']
    """
    For students, here's the meaning of the below code statement:
    - We retrieve the 'schema_heuristics' settings from the configuration dictionary.
    - If 'schema_heuristics' is not present in the config, we default to {'enabled': False}
    - This allows us to check later if heuristics should be applied during schema inference."""
    heuristics = config.get('schema_heuristics', {'enabled': False})
    schema = []
    
    for col in df.columns:
        # Apply heuristics if enabled
        heuristic_type = None
        if heuristics['enabled']:
            heuristic_type = _apply_column_heuristics(col, heuristics['patterns'])
        
        if heuristic_type:
            # If heuristic suggests date, verify it's somewhat date-like
            if heuristic_type == 'date':
                col_type = _infer_date_with_heuristic(df[col], thresholds['date'])
            elif heuristic_type == 'string':
                # Force string for IDs/Text
                col_type = 'string'
            else:
                col_type = _infer_column_type(df[col], thresholds)
        else:
            col_type = _infer_column_type(df[col], thresholds)
        schema.append({
            'column': col,
            'type': col_type
        })
    
    return schema


def _apply_column_heuristics(col_name: str, patterns: Dict[str, List[str]]) -> str:
    """
    Check if column name matches specific patterns.
    """
    import re
    col_lower = col_name.lower()
    
    # Check date patterns
    for pattern in patterns.get('date', []):
        if re.search(pattern, col_lower):
            return 'date'
            
    # Check ID patterns (Treat as string to avoid numeric/categorical misclassification)
    for pattern in patterns.get('ids', []):
        if re.search(pattern, col_lower):
            return 'string'
            
    # Check text patterns
    for pattern in patterns.get('text', []):
        if re.search(pattern, col_lower):
            return 'string'
            
    return None


def _infer_date_with_heuristic(series: pd.Series, threshold: float) -> str:
    """
    Validation logic when column looks like a date by name.
    """
    # Lower validation threshold slightly or just proceed with check
    # We still need to verify content is date-like, otherwise it might be "Update Notes"
    
    # Skip if all null
    if series.isna().all():
        return 'string'
        
    non_null = series.dropna()
    if len(non_null) == 0:
        return 'string'

    # If heuristic says date, we are more lenient.
    # Allow 40% parsable instead of 70%?
    date_ratio = _calculate_date_ratio(non_null)
    if date_ratio >= 0.4:  # significantly more lenient than default 0.7
        return 'date'
        
    return 'string'


def _infer_column_type(series: pd.Series, thresholds: Dict[str, float]) -> str:
    """
    Infer type of a single column.
    
    Args:
        series: Column data
        thresholds: Type detection thresholds
        
    Returns:
        Type string: 'numeric', 'date', 'categorical', or 'string'
    """
    # Skip if all null
    if series.isna().all():
        return 'string'
    
    # Get non-null values
    non_null = series.dropna()
    total_non_null = len(non_null)
    
    if total_non_null == 0:
        return 'string'
    
    # Try numeric conversion
    numeric_converted = pd.to_numeric(non_null, errors='coerce')
    num_ratio = numeric_converted.notna().sum() / total_non_null
    
    if num_ratio >= thresholds['numeric']:
        return 'numeric'
    
    # Try date conversion (only for object/string columns)
    if series.dtype == 'object':
        date_ratio = _calculate_date_ratio(non_null)
        
        if date_ratio >= thresholds['date']:
            return 'date'
    
    # Check for categorical based on unique ratio
    unique_ratio = series.nunique() / len(series)
    
    if unique_ratio <= thresholds['categorical_unique_ratio']:
        return 'categorical'
    
    # Default to string
    return 'string'


def _calculate_date_ratio(series: pd.Series) -> float:
    """
    Calculate the ratio of values that can be parsed as dates.
    
    Args:
        series: Non-null series values
        
    Returns:
        Ratio of parseable dates (0.0 to 1.0)
    """
    # First try pandas to_datetime (fast)
    try:
        parsed = pd.to_datetime(series, errors='coerce')
        return parsed.notna().sum() / len(series)
    except:
        pass
    
    # Fallback to dateutil parser (slower but more flexible)
    parseable_count = 0
    total = len(series)
    
    # Sample if too many rows (for performance)
    if total > 1000:
        sample_series = series.sample(min(1000, total), random_state=42)
    else:
        sample_series = series
    
    for val in sample_series:
        if _is_date_parseable(val):
            parseable_count += 1
    
    return parseable_count / len(sample_series)


def _is_date_parseable(value: Any) -> bool:
    """
    Check if a value can be parsed as a date.
    
    Args:
        value: Value to check
        
    Returns:
        True if parseable as date
    """
    if pd.isna(value):
        return False
    
    try:
        # Convert to string if not already
        str_val = str(value).strip()
        
        # Skip if too short or too long
        if len(str_val) < 6 or len(str_val) > 30:
            return False
        
        # Skip if it's purely numeric (likely not a date)
        if str_val.replace('.', '').replace('-', '').replace('/', '').isdigit():
            # But allow formats like 2023-01-15
            if '-' in str_val or '/' in str_val:
                pass
            else:
                return False
        
        # Try parsing
        date_parser.parse(str_val, fuzzy=False)
        return True
    except (ValueError, TypeError, OverflowError):
        return False


def get_inferred_types_dict(schema: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Convert schema list to dictionary for easy lookup.
    
    Args:
        schema: Schema list from infer_schema
        
    Returns:
        Dictionary mapping column name to type
    """
    return {item['column']: item['type'] for item in schema}
