"""
Test DuckDB persistence.
"""

import pytest
import duckdb
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.persistence import persist_to_duckdb, persist_action_log, get_dataset_from_duckdb, list_datasets
import pandas as pd


@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary database path."""
    return str(tmp_path / "test_agent_data.db")


def test_persist_to_duckdb(sample_clean_df, test_db_path):
    """Test persisting DataFrame to DuckDB."""
    dataset_id = "ds_test001"
    
    # Persist data
    ref = persist_to_duckdb(sample_clean_df, dataset_id, test_db_path)
    
    # Check reference format
    assert ref == f"duckdb:{dataset_id}.cleaned"
    
    # Verify data was persisted
    conn = duckdb.connect(test_db_path)
    result = conn.execute(f"SELECT COUNT(*) FROM {dataset_id}_cleaned").fetchone()
    conn.close()
    
    assert result[0] == len(sample_clean_df)


def test_persist_action_log(test_db_path):
    """Test persisting action log."""
    dataset_id = "ds_test002"
    actions = [
        {
            'column': 'sales',
            'action': 'impute_missing',
            'rows_affected': 5,
            'method': 'median',
            'fill_value': 100.5
        },
        {
            'column': 'region',
            'action': 'impute_missing',
            'rows_affected': 3,
            'method': 'mode',
            'fill_value': 'US'
        }
    ]
    
    # Persist action log
    persist_action_log(actions, dataset_id, test_db_path)
    
    # Verify action log was persisted
    conn = duckdb.connect(test_db_path)
    result = conn.execute(f"SELECT COUNT(*) FROM {dataset_id}_action_log").fetchone()
    conn.close()
    
    assert result[0] == len(actions)


def test_get_dataset_from_duckdb(sample_clean_df, test_db_path):
    """Test retrieving dataset from DuckDB."""
    dataset_id = "ds_test003"
    
    # Persist data
    persist_to_duckdb(sample_clean_df, dataset_id, test_db_path)
    
    # Retrieve data
    retrieved_df = get_dataset_from_duckdb(dataset_id, test_db_path)
    
    # Check data matches
    assert len(retrieved_df) == len(sample_clean_df)
    assert list(retrieved_df.columns) == list(sample_clean_df.columns)


def test_list_datasets(sample_clean_df, test_db_path):
    """Test listing datasets."""
    # Persist multiple datasets
    persist_to_duckdb(sample_clean_df, "ds_test004", test_db_path)
    persist_to_duckdb(sample_clean_df, "ds_test005", test_db_path)
    
    # List datasets
    datasets = list_datasets(test_db_path)
    
    # Check datasets are listed
    assert "ds_test004" in datasets
    assert "ds_test005" in datasets
    assert len(datasets) >= 2
