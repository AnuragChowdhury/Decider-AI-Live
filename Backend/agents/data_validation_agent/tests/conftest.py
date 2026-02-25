"""
Pytest configuration and fixtures.
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import load_config


@pytest.fixture
def config():
    """Load configuration for tests."""
    return load_config()


@pytest.fixture
def sample_clean_df():
    """Create a clean sample DataFrame."""
    return pd.DataFrame({
        'order_id': ['ORD001', 'ORD002', 'ORD003', 'ORD004', 'ORD005'],
        'order_date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19'],
        'region': ['US', 'IN', 'EU', 'US', 'IN'],
        'sales': [100.50, 250.75, 175.25, 300.00, 125.50]
    })


@pytest.fixture
def sample_missing_df():
    """Create DataFrame with missing values."""
    return pd.DataFrame({
        'order_id': ['ORD001', 'ORD002', None, 'ORD004', 'ORD005'],
        'order_date': ['2024-01-15', None, '2024-01-17', '2024-01-18', None],
        'region': ['US', 'IN', None, 'US', 'IN'],
        'sales': [100.50, None, 175.25, 300.00, None]
    })


@pytest.fixture
def sample_duplicates_df():
    """Create DataFrame with duplicates."""
    return pd.DataFrame({
        'order_id': ['ORD001', 'ORD002', 'ORD001', 'ORD003'],
        'order_date': ['2024-01-15', '2024-01-16', '2024-01-15', '2024-01-17'],
        'region': ['US', 'IN', 'US', 'EU'],
        'sales': [100.50, 250.75, 100.50, 175.25]
    })


@pytest.fixture
def sample_mixed_dates_df():
    """Create DataFrame with mixed date formats."""
    return pd.DataFrame({
        'order_id': ['ORD001', 'ORD002', 'ORD003', 'ORD004'],
        'order_date': ['2024-01-15', '01/16/2024', '17-01-2024', '2024-01-18'],
        'region': ['US', 'IN', 'EU', 'US'],
        'sales': [100.50, 250.75, 175.25, 300.00]
    })


@pytest.fixture
def sample_outliers_df():
    """Create DataFrame with outliers."""
    return pd.DataFrame({
        'order_id': [f'ORD{i:03d}' for i in range(1, 21)],
        'order_date': [f'2024-01-{i:02d}' for i in range(1, 21)],
        'region': ['US'] * 20,
        'sales': [100, 105, 98, 102, 99, 101, 103, 97, 104, 100,
                  9999, 102, 98, 101, 99, 103, 100, 102, 98, 101]  # One extreme outlier
    })


@pytest.fixture
def fixtures_dir():
    """Get fixtures directory path."""
    return Path(__file__).parent / 'fixtures'
