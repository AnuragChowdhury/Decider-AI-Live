"""
Phase 6: Data Analysis
Profile columns and generate insights.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from scipy import stats


def analyze(df: pd.DataFrame, schema: List[Dict[str, str]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analyze data and generate column profiles with insights.
    
    Args:
        df: Cleaned DataFrame
        schema: Inferred schema
        config: Configuration dictionary
        
    Returns:
        List of column profile dictionaries
    """
    schema_dict = {item['column']: item['type'] for item in schema}
    analysis_config = config['analysis']
    column_profiles = []
    
    for col in df.columns:
        col_type = schema_dict.get(col, 'string')
        
        if col_type == 'numeric':
            profile = _analyze_numeric(df, col, analysis_config)
        elif col_type == 'categorical':
            profile = _analyze_categorical(df, col, analysis_config)
        elif col_type == 'date':
            profile = _analyze_date(df, col, analysis_config)
        else:
            # Skip string columns for now (could add text analysis later)
            continue
        
        if profile:
            column_profiles.append(profile)
    
    return column_profiles


def _analyze_numeric(df: pd.DataFrame, col: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze numeric column."""
    # Convert to numeric (should already be clean)
    numeric_data = pd.to_numeric(df[col], errors='coerce').dropna()
    
    if len(numeric_data) == 0:
        return None
    
    # Calculate statistics
    profile = {
        'column': col,
        'min': float(numeric_data.min()),
        'max': float(numeric_data.max()),
        'mean': float(numeric_data.mean()),
        'median': float(numeric_data.median()),
    }
    
    # Add standard deviation if enough data
    if len(numeric_data) > 1:
        profile['std'] = float(numeric_data.std())
    
    # Calculate skewness if enough data
    if len(numeric_data) >= 3:
        skewness = stats.skew(numeric_data)
        profile['skewness'] = float(skewness)
    
    # Generate insights
    notes = _generate_numeric_insights(numeric_data, profile, config)
    profile['notes'] = notes
    
    return profile


def _generate_numeric_insights(data: pd.Series, profile: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Generate human-readable insights for numeric data."""
    insights = []
    
    # Check for skewness
    if 'skewness' in profile:
        skew_threshold = config['skewness_threshold']
        skewness = profile['skewness']
        
        if abs(skewness) > skew_threshold:
            if skewness > 0:
                insights.append(f"{profile['column'].replace('_', ' ').title()} is right-skewed")
            else:
                insights.append(f"{profile['column'].replace('_', ' ').title()} is left-skewed")
    
    # Check top-k contribution
    top_k_pct = config['top_k_contribution_pct']
    sorted_data = data.sort_values(ascending=False)
    top_k_count = max(1, int(len(sorted_data) * top_k_pct / 100))
    top_k_sum = sorted_data.head(top_k_count).sum()
    total_sum = sorted_data.sum()
    
    if total_sum > 0:
        contribution_pct = (top_k_sum / total_sum) * 100
        if contribution_pct > 50:  # If top k% contributes more than 50%
            insights.append(f"top {top_k_pct}% contribute ~{contribution_pct:.0f}% of total")
    
    # Check for concentration around median
    if 'median' in profile and 'mean' in profile:
        median = profile['median']
        mean = profile['mean']
        
        if abs(median - mean) / (abs(mean) + 1e-10) > 0.2:  # 20% difference
            if median < mean:
                insights.append("distribution has high-value outliers")
            else:
                insights.append("distribution has low-value outliers")
    
    # Default insight if none generated
    if not insights:
        insights.append(f"Values range from {profile['min']:.2f} to {profile['max']:.2f}")
    
    return '; '.join(insights)


def _analyze_categorical(df: pd.DataFrame, col: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze categorical column."""
    value_counts = df[col].value_counts()
    
    if len(value_counts) == 0:
        return None
    
    # Get top N values
    top_n = config['top_values_count']
    top_values = []
    
    for value, count in value_counts.head(top_n).items():
        top_values.append({
            'value': str(value),
            'count': int(count)
        })
    
    profile = {
        'column': col,
        'top_values': top_values,
        'unique_count': int(df[col].nunique())
    }
    
    # Generate insights
    notes = _generate_categorical_insights(value_counts, col)
    profile['notes'] = notes
    
    return profile


def _generate_categorical_insights(value_counts: pd.Series, col: str) -> str:
    """Generate human-readable insights for categorical data."""
    insights = []
    
    total_count = value_counts.sum()
    
    # Check for dominance
    if len(value_counts) > 0:
        top_value = value_counts.index[0]
        top_count = value_counts.iloc[0]
        top_pct = (top_count / total_count) * 100
        
        if top_pct > 50:
            insights.append(f"Majority ({top_pct:.0f}%) are '{top_value}'")
        elif len(value_counts) >= 2:
            top_2_count = value_counts.iloc[:2].sum()
            top_2_pct = (top_2_count / total_count) * 100
            
            if top_2_pct > 70:
                top_2_values = ' and '.join([f"'{v}'" for v in value_counts.index[:2]])
                insights.append(f"Majority come from {top_2_values}")
    
    # Check for diversity
    unique_ratio = len(value_counts) / total_count
    if unique_ratio > 0.8:
        insights.append("High diversity in values")
    elif unique_ratio < 0.1:
        insights.append(f"Limited to {len(value_counts)} distinct values")
    
    # Default insight
    if not insights:
        insights.append(f"{len(value_counts)} unique values")
    
    return '; '.join(insights)


def _analyze_date(df: pd.DataFrame, col: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze date column."""
    # Convert to datetime
    date_data = pd.to_datetime(df[col], errors='coerce').dropna()
    
    if len(date_data) == 0:
        return None
    
    profile = {
        'column': col,
        'min_date': date_data.min().strftime('%Y-%m-%d'),
        'max_date': date_data.max().strftime('%Y-%m-%d'),
        'date_range_days': int((date_data.max() - date_data.min()).days)
    }
    
    # Estimate frequency
    if len(date_data) > 1:
        sorted_dates = date_data.sort_values()
        gaps = sorted_dates.diff().dropna()
        median_gap = gaps.median()
        
        if median_gap.days <= 1:
            frequency = "daily"
        elif median_gap.days <= 7:
            frequency = "weekly"
        elif median_gap.days <= 31:
            frequency = "monthly"
        elif median_gap.days <= 92:
            frequency = "quarterly"
        else:
            frequency = "yearly"
        
        profile['estimated_frequency'] = frequency
    
    # Generate insights
    notes = _generate_date_insights(profile)
    profile['notes'] = notes
    
    return profile


def _generate_date_insights(profile: Dict[str, Any]) -> str:
    """Generate human-readable insights for date data."""
    insights = []
    
    date_range = profile['date_range_days']
    
    if date_range < 7:
        insights.append("Covers less than a week")
    elif date_range < 31:
        insights.append("Covers approximately one month")
    elif date_range < 365:
        insights.append(f"Covers {date_range // 30} months")
    else:
        insights.append(f"Covers {date_range // 365} years")
    
    if 'estimated_frequency' in profile:
        insights.append(f"appears to be {profile['estimated_frequency']} data")
    
    return '; '.join(insights)
