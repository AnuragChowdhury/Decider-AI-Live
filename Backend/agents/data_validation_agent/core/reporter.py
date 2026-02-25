"""
Phase 9: Report Assembly
Assemble final JSON report with all validation results.
"""

from typing import List, Dict, Any, Optional
from .scoring import get_health_message


def assemble_report(
    dataset_id: str,
    status: str,
    rows_before: int,
    rows_after: int,
    health_score: float,
    schema: List[Dict[str, str]],
    issues: List[Dict[str, Any]],
    column_profile: List[Dict[str, Any]],
    clean_data_ref: Optional[str],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Assemble final JSON report.
    
    Args:
        dataset_id: Unique dataset identifier
        status: Status ('READY' or 'ERROR')
        rows_before: Row count before cleaning
        rows_after: Row count after cleaning
        health_score: Calculated health score
        schema: Inferred schema
        issues: List of issues with fixes
        column_profile: Column analysis results
        clean_data_ref: Reference to cleaned data in DuckDB
        config: Configuration dictionary
        
    Returns:
        Complete JSON report matching API contract
    """
    # Determine if analytics ready
    health_threshold = config['manual_review']['health_threshold']
    analytics_ready = health_score >= health_threshold and status == 'READY'
    
    # Generate summary message
    message = get_health_message(health_score, issues)
    
    # Build report
    report = {
        'dataset_id': dataset_id,
        'status': status,
        'analytics_ready': analytics_ready,
        'summary': {
            'health_score': health_score,
            'rows_before': rows_before,
            'rows_after': rows_after,
            'message': message
        },
        'schema': schema,
        'issues': issues,
        'column_profile': column_profile,
        'clean_data_ref': clean_data_ref
    }
    
    return report


def assemble_error_report(
    dataset_id: Optional[str],
    error_message: str
) -> Dict[str, Any]:
    """
    Assemble error report when validation fails.
    
    Args:
        dataset_id: Dataset ID if available
        error_message: Error message to return
        
    Returns:
        Error JSON report
    """
    return {
        'dataset_id': dataset_id,
        'status': 'ERROR',
        'analytics_ready': False,
        'summary': {
            'health_score': 0.0,
            'rows_before': 0,
            'rows_after': 0,
            'message': error_message
        },
        'schema': [],
        'issues': [],
        'column_profile': [],
        'clean_data_ref': None
    }
