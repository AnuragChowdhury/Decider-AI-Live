"""
Phase 7: Health Score Calculation
Calculate overall data quality health score.
"""

import pandas as pd
from typing import List, Dict, Any


def calculate_health_score(
    df: pd.DataFrame,
    issues: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> float:
    """
    Calculate overall health score based on data quality metrics.
    
    Args:
        df: Cleaned DataFrame
        issues: List of detected issues
        config: Configuration dictionary
        
    Returns:
        Health score between 0.0 and 1.0
    """
    weights = config['health_weights']
    
    # Calculate component scores
    completeness = _calculate_completeness(df, issues)
    uniqueness = _calculate_uniqueness(df, issues)
    consistency = _calculate_consistency(df, issues)
    validity = _calculate_validity(df, issues)
    outlier_penalty = _calculate_outlier_penalty(df, issues)
    
    # Weighted sum
    health_score = (
        completeness * weights['completeness'] +
        uniqueness * weights['uniqueness'] +
        consistency * weights['consistency'] +
        validity * weights['validity'] -
        outlier_penalty * weights['outlier_penalty']
    )
    
    # Ensure score is between 0 and 1
    health_score = max(0.0, min(1.0, health_score))
    
    return round(health_score, 2)


def _calculate_completeness(df: pd.DataFrame, issues: List[Dict[str, Any]]) -> float:
    """
    Calculate completeness score (1 - missing_ratio).
    
    Returns:
        Score between 0.0 and 1.0
    """
    total_cells = df.shape[0] * df.shape[1]
    
    if total_cells == 0:
        return 0.0
    
    # Count missing values from issues
    total_missing = 0
    for issue in issues:
        if issue['issue'] == 'Missing values':
            total_missing += issue['rows_affected']
    
    completeness = 1.0 - (total_missing / total_cells)
    return max(0.0, completeness)


def _calculate_uniqueness(df: pd.DataFrame, issues: List[Dict[str, Any]]) -> float:
    """
    Calculate uniqueness score (1 - duplicate_ratio).
    
    Returns:
        Score between 0.0 and 1.0
    """
    total_rows = len(df)
    
    if total_rows == 0:
        return 0.0
    
    # Count duplicates from issues
    duplicate_count = 0
    for issue in issues:
        if issue['issue'] == 'Duplicate records':
            duplicate_count = issue['rows_affected']
            break
    
    uniqueness = 1.0 - (duplicate_count / total_rows)
    return max(0.0, uniqueness)


def _calculate_consistency(df: pd.DataFrame, issues: List[Dict[str, Any]]) -> float:
    """
    Calculate consistency score based on type coercion and format issues.
    
    Returns:
        Score between 0.0 and 1.0
    """
    total_rows = len(df)
    
    if total_rows == 0:
        return 0.0
    
    # Count rows affected by consistency issues
    consistency_issues = 0
    for issue in issues:
        if issue['issue'] in ['Mixed date formats', 'Type mismatch - high coercion loss']:
            consistency_issues += issue['rows_affected']
    
    consistency = 1.0 - (consistency_issues / (total_rows * df.shape[1]))
    return max(0.0, consistency)


def _calculate_validity(df: pd.DataFrame, issues: List[Dict[str, Any]]) -> float:
    """
    Calculate validity score based on constraint violations.
    
    Returns:
        Score between 0.0 and 1.0
    """
    total_rows = len(df)
    
    if total_rows == 0:
        return 0.0
    
    # Count rows with validity issues (excluding outliers which are handled separately)
    validity_issues = 0
    for issue in issues:
        if issue['issue'] not in ['Missing values', 'Duplicate records', 
                                   'Mixed date formats', 'Type mismatch - high coercion loss',
                                   'Extreme outliers detected']:
            validity_issues += issue['rows_affected']
    
    # For now, validity is high if no specific constraint violations
    validity = 1.0 - (validity_issues / total_rows)
    return max(0.0, validity)


def _calculate_outlier_penalty(df: pd.DataFrame, issues: List[Dict[str, Any]]) -> float:
    """
    Calculate outlier penalty.
    
    Returns:
        Penalty between 0.0 and 1.0
    """
    total_rows = len(df)
    
    if total_rows == 0:
        return 0.0
    
    # Count outliers from issues
    outlier_count = 0
    for issue in issues:
        if issue['issue'] == 'Extreme outliers detected':
            outlier_count += issue['rows_affected']
    
    # Penalty is proportional to outlier ratio, but capped
    penalty = min(1.0, outlier_count / total_rows)
    return penalty


def get_health_message(health_score: float, issues: List[Dict[str, Any]]) -> str:
    """
    Generate human-readable health message based on score and issues.
    
    Args:
        health_score: Calculated health score
        issues: List of issues
        
    Returns:
        Human-readable message
    """
    if health_score >= 0.9:
        return "Excellent data quality. Your data is ready for analysis."
    elif health_score >= 0.75:
        return "Good data quality with minor issues that were safely resolved. Your data is ready for analysis."
    elif health_score >= 0.6:
        return "Minor data quality issues were found and safely resolved. Your data is ready for analysis."
    elif health_score >= 0.4:
        return "Moderate data quality issues detected. Some issues were resolved, but manual review is recommended."
    else:
        return "Significant data quality issues detected. Manual review and correction strongly recommended before analysis."
