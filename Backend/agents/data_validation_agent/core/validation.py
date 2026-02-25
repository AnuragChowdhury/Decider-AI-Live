"""
Phase 4: Data Validation
Detect data quality issues without applying fixes.

Here's what work it does and how it works:
- For each column in the standardized DataFrame, we check for common data quality issues such as missing values, mixed date formats, extreme outliers, and type coercion Losses.
- We use statistical methods like IQR and Z-score for outlier detection, and Leverage pandas' parsing capabilities to identify date inconsistencies.
- The validation process generates a list of issues, each detailing the column affected, the nature of the issue, number of rows impacted, and placeholders for fixes, reasons, and impact assessments.


List of steps:
1. Check for missing values in each column.
2. For date columns, check for mixed date formats by attempting to parse values and measuring success rates.
3. For numeric columns, detect extreme outliers using IQR and Z-score methods, with
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from sklearn.ensemble import IsolationForest
from scipy import stats


def validate(df: pd.DataFrame, schema: List[Dict[str, str]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate data and detect quality issues.
    
    Args:
        df: Standardized DataFrame
        schema: Inferred schema
        config: Configuration dictionary
        
    Returns:
        List of issues detected
    """
    issues = []
    schema_dict = {item['column']: item['type'] for item in schema}
    
    # Check each column
    for col in df.columns:
        col_type = schema_dict.get(col, 'string')
        col_issues = []
        
        # 1. Check for missing values
        missing_issue = _check_missing_values(df, col)
        if missing_issue:
            col_issues.append(missing_issue)
        
        # 2. Check for type-specific issues
        if col_type == 'date':
            date_issue = _check_date_consistency(df, col, config)
            if date_issue:
                col_issues.append(date_issue)
        
        elif col_type == 'numeric':
            # Check for outliers
            outlier_issue = _check_outliers(df, col, config)
            if outlier_issue:
                col_issues.append(outlier_issue)
        
        # 3. Check for type coercion loss
        coercion_issue = _check_coercion_loss(df, col, col_type, config)
        if coercion_issue:
            col_issues.append(coercion_issue)
        
        issues.extend(col_issues)
    
    # 4. Check for duplicate rows (dataset-level)
    duplicate_issue = _check_duplicates(df)
    if duplicate_issue:
        issues.append(duplicate_issue)
    
    return issues


def _check_missing_values(df: pd.DataFrame, col: str) -> Dict[str, Any]:
    """Check for missing values in a column."""
    missing_count = df[col].isna().sum()
    
    if missing_count > 0:
        return {
            'column': col,
            'issue': 'Missing values',
            'rows_affected': int(missing_count),
            'fix_applied': None,
            'why': None,
            'impact': None
        }
    return None


def _check_date_consistency(df: pd.DataFrame, col: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check for mixed date formats."""
    non_null = df[col].dropna()
    
    if len(non_null) == 0:
        return None
    
    # Try parsing with pandas
    parsed = pd.to_datetime(non_null, errors='coerce')
    parse_success_ratio = parsed.notna().sum() / len(non_null)
    
    # If less than 95% can be parsed consistently, flag as mixed formats
    if parse_success_ratio < 0.95:
        rows_affected = (parsed.isna()).sum()
        return {
            'column': col,
            'issue': 'Mixed date formats',
            'rows_affected': int(rows_affected),
            'fix_applied': None,
            'why': None,
            'impact': None
        }
    
    return None


def _check_outliers(df: pd.DataFrame, col: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Detect outliers using IQR and optionally IsolationForest."""
    non_null = df[col].dropna()
    
    # Convert to numeric
    numeric_vals = pd.to_numeric(non_null, errors='coerce').dropna()
    
    if len(numeric_vals) < 4:  # Need at least 4 values for IQR
        return None
    
    outlier_config = config['outlier']
    
    # Method 1: IQR-based detection
    q1 = numeric_vals.quantile(0.25)
    q3 = numeric_vals.quantile(0.75)
    iqr = q3 - q1
    
    lower_bound = q1 - outlier_config['iqr_multiplier'] * iqr
    upper_bound = q3 + outlier_config['iqr_multiplier'] * iqr
    
    iqr_outliers = ((numeric_vals < lower_bound) | (numeric_vals > upper_bound)).sum()
    
    # Method 2: Z-score based detection
    z_scores = np.abs(stats.zscore(numeric_vals))
    z_outliers = (z_scores > outlier_config['zscore_threshold']).sum()
    
    # Use the more conservative estimate
    outlier_count = max(iqr_outliers, z_outliers)
    
    # Optionally use IsolationForest for multivariate detection
    if len(numeric_vals) >= outlier_config['isolationforest_min_rows']:
        try:
            iso_forest = IsolationForest(
                contamination=outlier_config['contamination'],
                random_state=42
            )
            predictions = iso_forest.fit_predict(numeric_vals.values.reshape(-1, 1))
            iso_outliers = (predictions == -1).sum()
            outlier_count = max(outlier_count, iso_outliers)
        except:
            pass  # Fall back to IQR/Z-score only
    
    if outlier_count > 0:
        return {
            'column': col,
            'issue': 'Extreme outliers detected',
            'rows_affected': int(outlier_count),
            'fix_applied': None,
            'why': None,
            'impact': None
        }
    
    return None


def _check_coercion_loss(df: pd.DataFrame, col: str, col_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if type coercion causes significant data loss."""
    non_null = df[col].dropna()
    
    if len(non_null) == 0:
        return None
    
    if col_type == 'numeric':
        converted = pd.to_numeric(non_null, errors='coerce')
        loss_ratio = converted.isna().sum() / len(non_null)
    elif col_type == 'date':
        converted = pd.to_datetime(non_null, errors='coerce')
        loss_ratio = converted.isna().sum() / len(non_null)
    else:
        return None
    
    threshold = config['manual_review']['coercion_loss_threshold']
    
    if loss_ratio > threshold:
        rows_affected = int(converted.isna().sum())
        return {
            'column': col,
            'issue': 'Type mismatch - high coercion loss',
            'rows_affected': rows_affected,
            'fix_applied': None,
            'why': None,
            'impact': None
        }
    
    return None


def _check_duplicates(df: pd.DataFrame) -> Dict[str, Any]:
    """Check for duplicate rows."""
    duplicate_count = df.duplicated().sum()
    
    if duplicate_count > 0:
        return {
            'column': None,  # Dataset-level issue
            'issue': 'Duplicate records',
            'rows_affected': int(duplicate_count),
            'fix_applied': None,
            'why': None,
            'impact': None
        }
    
    return None
