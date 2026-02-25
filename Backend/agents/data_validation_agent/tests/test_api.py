"""
Test FastAPI endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from validate_agent import app

client = TestClient(app)


def test_root_endpoint():
    """Test health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Data Validation Agent"
    assert data["status"] == "running"


def test_validate_clean_csv(fixtures_dir):
    """Test validation with clean CSV file."""
    csv_path = fixtures_dir / "sample_clean.csv"
    
    with open(csv_path, 'rb') as f:
        response = client.post(
            "/validate",
            files={"file": ("sample_clean.csv", f, "text/csv")}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "dataset_id" in data
    assert data["status"] == "READY"
    assert data["analytics_ready"] is True
    assert "summary" in data
    assert "schema" in data
    assert "issues" in data
    assert "column_profile" in data
    assert "clean_data_ref" in data
    
    # Check summary
    assert data["summary"]["rows_before"] == 10
    assert data["summary"]["rows_after"] == 10
    assert data["summary"]["health_score"] >= 0.9  # Should be high for clean data


def test_validate_missing_values(fixtures_dir):
    """Test validation with missing values."""
    csv_path = fixtures_dir / "sample_missing_values.csv"
    
    with open(csv_path, 'rb') as f:
        response = client.post(
            "/validate",
            files={"file": ("sample_missing_values.csv", f, "text/csv")}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should detect missing values
    issues = data["issues"]
    missing_issues = [i for i in issues if i["issue"] == "Missing values"]
    assert len(missing_issues) > 0
    
    # Check that fixes were applied
    for issue in missing_issues:
        assert issue["fix_applied"] is not None
        assert issue["why"] is not None
        assert issue["impact"] is not None


def test_validate_duplicates(fixtures_dir):
    """Test validation with duplicates."""
    csv_path = fixtures_dir / "sample_duplicates.csv"
    
    with open(csv_path, 'rb') as f:
        response = client.post(
            "/validate",
            files={"file": ("sample_duplicates.csv", f, "text/csv")}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should detect duplicates
    issues = data["issues"]
    dup_issues = [i for i in issues if i["issue"] == "Duplicate records"]
    assert len(dup_issues) > 0
    
    # In lenient mode, duplicates should be removed
    dup_issue = dup_issues[0]
    assert "Removed duplicate rows" in dup_issue["fix_applied"]
    
    # Check row count
    rows_before = data["summary"]["rows_before"]
    rows_after = data["summary"]["rows_after"]
    assert rows_after < rows_before


def test_validate_mixed_dates(fixtures_dir):
    """Test validation with mixed date formats."""
    csv_path = fixtures_dir / "sample_mixed_dates.csv"
    
    with open(csv_path, 'rb') as f:
        response = client.post(
            "/validate",
            files={"file": ("sample_mixed_dates.csv", f, "text/csv")}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check schema detected date column
    schema = data["schema"]
    date_cols = [s for s in schema if s["type"] == "date"]
    assert len(date_cols) > 0


def test_validate_outliers(fixtures_dir):
    """Test validation with outliers."""
    csv_path = fixtures_dir / "sample_outliers.csv"
    
    with open(csv_path, 'rb') as f:
        response = client.post(
            "/validate",
            files={"file": ("sample_outliers.csv", f, "text/csv")}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should detect outliers
    issues = data["issues"]
    outlier_issues = [i for i in issues if i["issue"] == "Extreme outliers detected"]
    
    if len(outlier_issues) > 0:
        # Outliers should be flagged but not removed
        outlier_issue = outlier_issues[0]
        assert "flagged but not removed" in outlier_issue["fix_applied"]
        assert outlier_issue["impact"] == "No data removed"


def test_strict_mode_duplicates(fixtures_dir):
    """Test strict mode doesn't remove duplicates."""
    csv_path = fixtures_dir / "sample_duplicates.csv"
    
    with open(csv_path, 'rb') as f:
        response = client.post(
            "/validate",
            files={"file": ("sample_duplicates.csv", f, "text/csv")},
            headers={"X-Validation-Mode": "strict"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # In strict mode, duplicates should be flagged only
    issues = data["issues"]
    dup_issues = [i for i in issues if i["issue"] == "Duplicate records"]
    
    if len(dup_issues) > 0:
        dup_issue = dup_issues[0]
        assert "manual review" in dup_issue["fix_applied"].lower()
        
        # Rows should not be removed in strict mode
        rows_before = data["summary"]["rows_before"]
        rows_after = data["summary"]["rows_after"]
        assert rows_after == rows_before


def test_file_too_large():
    """Test file size validation."""
    # Create a mock large file
    large_content = b"x" * (21 * 1024 * 1024)  # 21 MB
    
    response = client.post(
        "/validate",
        files={"file": ("large.csv", large_content, "text/csv")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "ERROR"
    assert "exceeds maximum" in data["summary"]["message"].lower()


def test_unsupported_format():
    """Test unsupported file format."""
    response = client.post(
        "/validate",
        files={"file": ("test.txt", b"some text", "text/plain")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "ERROR"
    assert "unsupported" in data["summary"]["message"].lower()


def test_empty_file():
    """Test empty file."""
    response = client.post(
        "/validate",
        files={"file": ("empty.csv", b"", "text/csv")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "ERROR"
    assert "empty" in data["summary"]["message"].lower()
