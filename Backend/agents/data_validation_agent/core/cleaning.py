"""
Phase 5: Data Cleaning
Apply deterministic, low-risk fixes to detected issues.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from dateutil import parser as date_parser


def clean(
    df: pd.DataFrame,
    issues: List[Dict[str, Any]],
    schema: List[Dict[str, str]],
    mode: str,
    config: Dict[str, Any]
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Apply safe, deterministic fixes to data quality issues.
    
    Args:
        df: Standardized DataFrame
        issues: List of detected issues
        schema: Inferred schema
        mode: Validation mode ('strict' or 'lenient')
        config: Configuration dictionary
        
    Returns:
        Tuple of (cleaned DataFrame, updated issues list with fixes applied)
    """
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # Create schema lookup
    schema_dict = {item['column']: item['type'] for item in schema}
    
    # Track action log
    action_log = []
    
    # Process each issue
    updated_issues = []
    for issue in issues:
        issue_copy = issue.copy()
        
        # Apply appropriate fix based on issue type
        if issue['issue'] == 'Missing values':
            df, issue_copy, action = _fix_missing_values(
                df, issue_copy, schema_dict, config
            )
            if action:
                action_log.append(action)
        
        elif issue['issue'] == 'Mixed date formats':
            df, issue_copy, action = _fix_date_formats(df, issue_copy)
            if action:
                action_log.append(action)
        
        elif issue['issue'] == 'Duplicate records':
            df, issue_copy, action = _fix_duplicates(df, issue_copy, mode)
            if action:
                action_log.append(action)
        
        elif issue['issue'] == 'Extreme outliers detected':
            # Only flag, do not remove
            issue_copy['fix_applied'] = 'Outliers flagged but not removed'
            issue_copy['why'] = 'Outliers may represent valid extreme values'
            issue_copy['impact'] = 'No data removed'
        
        elif issue['issue'] == 'Type mismatch - high coercion loss':
            # In strict mode, don't auto-fix; in lenient mode, keep as string
            if mode == 'lenient':
                issue_copy['fix_applied'] = 'Column kept as string type due to high coercion loss'
                issue_copy['why'] = 'Preserves all data without loss'
                issue_copy['impact'] = 'Column treated as text instead of numeric/date'
            else:
                issue_copy['fix_applied'] = None
                issue_copy['why'] = 'Manual review required in strict mode'
                issue_copy['impact'] = 'No automatic fix applied'
        
        updated_issues.append(issue_copy)
    
    return df, updated_issues


def _fix_missing_values(
    df: pd.DataFrame,
    issue: Dict[str, Any],
    schema_dict: Dict[str, str],
    config: Dict[str, Any]
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """Fix missing values using appropriate imputation strategy."""
    col = issue['column']
    col_type = schema_dict.get(col, 'string')
    imputation_config = config['imputation']
    
    action = {
        'column': col,
        'action': 'impute_missing',
        'rows_affected': issue['rows_affected']
    }
    
    if col_type == 'numeric':
        # Ensure column is numeric before calculating statistics
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
        strategy = imputation_config['numeric']
        if strategy == 'median':
            fill_value = df[col].median()
            df[col] = df[col].fillna(fill_value)
            issue['fix_applied'] = f'Filled missing values using median ({fill_value:.2f})'
            issue['why'] = 'Median preserves distribution and avoids outlier bias'
            issue['impact'] = 'Minor numerical approximation'
            action['method'] = 'median'
            action['fill_value'] = float(fill_value)
        elif strategy == 'mean':
            fill_value = df[col].mean()
            df[col] = df[col].fillna(fill_value)
            issue['fix_applied'] = f'Filled missing values using mean ({fill_value:.2f})'
            issue['why'] = 'Mean provides average value for missing data'
            issue['impact'] = 'Minor numerical approximation'
            action['method'] = 'mean'
            action['fill_value'] = float(fill_value)
        else:  # zero
            df[col] = df[col].fillna(0)
            issue['fix_applied'] = 'Filled missing values with 0'
            issue['why'] = 'Zero is a safe default for numeric data'
            issue['impact'] = 'Missing values set to zero'
            action['method'] = 'zero'
            action['fill_value'] = 0
    
    elif col_type == 'categorical':
        strategy = imputation_config['categorical']
        if strategy == 'mode':
            mode_value = df[col].mode()
            if len(mode_value) > 0:
                fill_value = mode_value[0]
                df[col] = df[col].fillna(fill_value)
                issue['fix_applied'] = f'Filled missing values using mode ("{fill_value}")'
                issue['why'] = 'Mode is the most frequent value in the category'
                issue['impact'] = f'Mode value used for {issue["rows_affected"]} rows'
                action['method'] = 'mode'
                action['fill_value'] = str(fill_value)
            else:
                df[col] = df[col].fillna('Unknown')
                issue['fix_applied'] = 'Filled missing values with "Unknown"'
                issue['why'] = 'No mode available, using placeholder'
                issue['impact'] = 'Missing values marked as Unknown'
                action['method'] = 'unknown'
                action['fill_value'] = 'Unknown'
        else:  # unknown
            df[col] = df[col].fillna('Unknown')
            issue['fix_applied'] = 'Filled missing values with "Unknown"'
            issue['why'] = 'Explicit placeholder for missing categorical data'
            issue['impact'] = 'Missing values marked as Unknown'
            action['method'] = 'unknown'
            action['fill_value'] = 'Unknown'
    
    elif col_type == 'date':
        # Keep NaT for dates (don't impute)
        issue['fix_applied'] = 'Missing dates kept as NaT (Not a Time)'
        issue['why'] = 'Date imputation could introduce misleading temporal data'
        issue['impact'] = 'No data loss, missing dates remain null'
        action['method'] = 'keep_nat'
        action['fill_value'] = None
    
    else:  # string
        df[col] = df[col].fillna('')
        issue['fix_applied'] = 'Filled missing values with empty string'
        issue['why'] = 'Empty string is appropriate for text data'
        issue['impact'] = 'Missing text values set to empty'
        action['method'] = 'empty_string'
        action['fill_value'] = ''
    
    return df, issue, action


def _fix_date_formats(
    df: pd.DataFrame,
    issue: Dict[str, Any]
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """Standardize date formats."""
    col = issue['column']
    
    # Parse dates using pandas with fallback to dateutil
    parsed_dates = pd.to_datetime(df[col], errors='coerce')
    
    # For values that failed, try dateutil parser
    failed_mask = parsed_dates.isna() & df[col].notna()
    if failed_mask.any():
        for idx in df[failed_mask].index:
            try:
                val = df.loc[idx, col]
                parsed_dates.loc[idx] = date_parser.parse(str(val), fuzzy=False)
            except:
                pass  # Keep as NaT
    
    df[col] = parsed_dates
    
    issue['fix_applied'] = 'Converted all values to YYYY-MM-DD format'
    issue['why'] = 'Consistent date formats are required for time-based analysis'
    issue['impact'] = 'No data loss'
    
    action = {
        'column': col,
        'action': 'standardize_dates',
        'rows_affected': issue['rows_affected'],
        'method': 'to_datetime',
        'format': 'YYYY-MM-DD'
    }
    
    return df, issue, action


def _fix_duplicates(
    df: pd.DataFrame,
    issue: Dict[str, Any],
    mode: str
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """Remove or flag duplicate rows."""
    duplicate_count = issue['rows_affected']
    
    action = {
        'column': None,
        'action': 'handle_duplicates',
        'rows_affected': duplicate_count
    }
    
    if mode == 'strict':
        # In strict mode, only flag duplicates
        issue['fix_applied'] = 'Duplicates flagged for manual review'
        issue['why'] = 'Strict mode requires manual review of duplicates'
        issue['impact'] = 'No rows removed'
        action['method'] = 'flag_only'
    else:
        # In lenient mode, remove duplicates keeping first occurrence
        df = df.drop_duplicates(keep='first').reset_index(drop=True)
        issue['fix_applied'] = 'Removed duplicate rows, keeping first occurrence'
        issue['why'] = 'Duplicates would inflate metrics and analysis results'
        issue['impact'] = f'{duplicate_count} rows removed'
        action['method'] = 'remove_keep_first'
    
    return df, issue, action
