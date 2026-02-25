"""
Test determinism - same input should produce same output.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from validate_agent import app

client = TestClient(app)


def test_deterministic_dataset_id(fixtures_dir):
    """Test that same file produces same dataset_id."""
    csv_path = fixtures_dir / "sample_clean.csv"
    
    # Upload same file twice
    with open(csv_path, 'rb') as f:
        response1 = client.post(
            "/validate",
            files={"file": ("sample_clean.csv", f, "text/csv")}
        )
    
    with open(csv_path, 'rb') as f:
        response2 = client.post(
            "/validate",
            files={"file": ("sample_clean.csv", f, "text/csv")}
        )
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Same file should produce same dataset_id
    assert data1["dataset_id"] == data2["dataset_id"]


def test_deterministic_health_score(fixtures_dir):
    """Test that same file produces same health score."""
    csv_path = fixtures_dir / "sample_missing_values.csv"
    
    # Upload same file twice
    with open(csv_path, 'rb') as f:
        response1 = client.post(
            "/validate",
            files={"file": ("sample_missing_values.csv", f, "text/csv")}
        )
    
    with open(csv_path, 'rb') as f:
        response2 = client.post(
            "/validate",
            files={"file": ("sample_missing_values.csv", f, "text/csv")}
        )
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Same file should produce same health score
    assert data1["summary"]["health_score"] == data2["summary"]["health_score"]


def test_deterministic_issues(fixtures_dir):
    """Test that same file produces same issues."""
    csv_path = fixtures_dir / "sample_duplicates.csv"
    
    # Upload same file twice
    with open(csv_path, 'rb') as f:
        response1 = client.post(
            "/validate",
            files={"file": ("sample_duplicates.csv", f, "text/csv")}
        )
    
    with open(csv_path, 'rb') as f:
        response2 = client.post(
            "/validate",
            files={"file": ("sample_duplicates.csv", f, "text/csv")}
        )
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Same number of issues
    assert len(data1["issues"]) == len(data2["issues"])
    
    # Same issue types
    issues1 = sorted([i["issue"] for i in data1["issues"]])
    issues2 = sorted([i["issue"] for i in data2["issues"]])
    assert issues1 == issues2


def test_deterministic_schema(fixtures_dir):
    """Test that same file produces same schema."""
    csv_path = fixtures_dir / "sample_clean.csv"
    
    # Upload same file twice
    with open(csv_path, 'rb') as f:
        response1 = client.post(
            "/validate",
            files={"file": ("sample_clean.csv", f, "text/csv")}
        )
    
    with open(csv_path, 'rb') as f:
        response2 = client.post(
            "/validate",
            files={"file": ("sample_clean.csv", f, "text/csv")}
        )
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Same schema
    assert data1["schema"] == data2["schema"]
