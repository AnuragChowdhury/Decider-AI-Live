# Data Validation Agent

A **deterministic, explainable, and fully testable** data validation service that processes CSV/XLSX files through a comprehensive validation pipeline, persists cleaned data to DuckDB, and returns detailed JSON reports with actionable insights.

## Features

✅ **Deterministic Processing** - Same input always produces same output  
✅ **9-Phase Pipeline** - Ingestion → Standardization → Schema Inference → Validation → Cleaning → Analysis → Scoring → Persistence → Reporting  
✅ **Explainable Fixes** - Every fix includes `why` and `impact` fields  
✅ **DuckDB Persistence** - Cleaned data stored with audit logs  
✅ **Configurable Thresholds** - All behavior controlled via `config.yaml`  
✅ **Comprehensive Testing** - Unit, integration, and determinism tests  
✅ **FastAPI + Swagger** - RESTful API with interactive docs  

---

## Quick Start

### 1. Installation

```bash
# Navigate to the agent directory
cd Backend/agents/data_validation_agent

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Server

```bash
# Start the FastAPI server
uvicorn validate_agent:app --reload

# Server will start at http://127.0.0.1:8000
```

### 3. Access Swagger UI

Open your browser and navigate to:
```
http://127.0.0.1:8000/docs
```

You can upload files and test the API interactively through the Swagger interface.

---

## API Usage

### Endpoint

```
POST /validate
```

### Request

**Multipart Form Data:**
- `file`: CSV or XLSX file (required)

**Optional Headers:**
- `X-Validation-Mode`: `strict` or `lenient` (default: `lenient`)
- `X-DuckDB-Path`: Custom path for DuckDB file (default: `agent_data.db`)

**Query Parameters:**
- `persist`: `true` or `false` (default: `true`) - Whether to persist cleaned data

### Response (Success - HTTP 200)

```json
{
  "dataset_id": "ds_a1b2c3d4",
  "status": "READY",
  "analytics_ready": true,
  "summary": {
    "health_score": 0.88,
    "rows_before": 10542,
    "rows_after": 10480,
    "message": "Minor data quality issues were found and safely resolved. Your data is ready for analysis."
  },
  "schema": [
    {"column": "order_id", "type": "string"},
    {"column": "order_date", "type": "date"},
    {"column": "region", "type": "categorical"},
    {"column": "sales", "type": "numeric"}
  ],
  "issues": [
    {
      "column": "order_date",
      "issue": "Mixed date formats",
      "rows_affected": 342,
      "fix_applied": "Converted all values to YYYY-MM-DD format",
      "why": "Consistent date formats are required for time-based analysis",
      "impact": "No data loss"
    }
  ],
  "column_profile": [
    {
      "column": "sales",
      "min": 5.0,
      "max": 9800.0,
      "mean": 123.45,
      "median": 98.0,
      "notes": "Sales are right-skewed; top 10% contribute ~45% of revenue"
    }
  ],
  "clean_data_ref": "duckdb:ds_a1b2c3d4.cleaned"
}
```

### Response (Error - HTTP 4xx/5xx)

```json
{
  "dataset_id": null,
  "status": "ERROR",
  "analytics_ready": false,
  "summary": {
    "health_score": 0.0,
    "rows_before": 0,
    "rows_after": 0,
    "message": "Detailed error message"
  },
  "schema": [],
  "issues": [],
  "column_profile": [],
  "clean_data_ref": null
}
```

---

## cURL Examples

### Basic Upload

```bash
curl -X POST "http://127.0.0.1:8000/validate" \
  -F "file=@tests/fixtures/sample_clean.csv"
```

### Strict Mode

```bash
curl -X POST "http://127.0.0.1:8000/validate" \
  -H "X-Validation-Mode: strict" \
  -F "file=@tests/fixtures/sample_duplicates.csv"
```

### Custom DuckDB Path

```bash
curl -X POST "http://127.0.0.1:8000/validate" \
  -H "X-DuckDB-Path: /path/to/custom.db" \
  -F "file=@data.csv"
```

### Without Persistence

```bash
curl -X POST "http://127.0.0.1:8000/validate?persist=false" \
  -F "file=@data.csv"
```

---

## Configuration

Edit `config.yaml` to customize validation behavior:

```yaml
# Type inference thresholds
coercion_thresholds:
  numeric: 0.8          # 80% of values must be numeric
  date: 0.7             # 70% of values must be dates
  categorical_unique_ratio: 0.3  # Max 30% unique for categorical

# Imputation strategies
imputation:
  numeric: median       # Options: median, mean, zero
  categorical: mode     # Options: mode, unknown
  date: keep_nat        # Options: keep_nat, forward_fill

# Duplicate handling
duplicates:
  default_action: remove_keep_first  # Options: remove_keep_first, flag_only

# Outlier detection
outlier:
  zscore_threshold: 3.0
  iqr_multiplier: 1.5
  isolationforest_min_rows: 50

# Health score weights
health_weights:
  completeness: 0.35
  uniqueness: 0.2
  consistency: 0.2
  validity: 0.15
  outlier_penalty: 0.1

# File upload limits
upload:
  max_bytes: 20000000   # 20 MB
```

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Files

```bash
# API endpoint tests
pytest tests/test_api.py -v

# Determinism tests
pytest tests/test_determinism.py -v

# Persistence tests
pytest tests/test_persistence.py -v
```

### Run with Coverage

```bash
pytest tests/ -v --cov=core --cov=utils
```

### Test Fixtures

Sample files are available in `tests/fixtures/`:
- `sample_clean.csv` - Clean data with no issues
- `sample_missing_values.csv` - Data with missing values
- `sample_duplicates.csv` - Data with duplicate rows
- `sample_mixed_dates.csv` - Data with inconsistent date formats
- `sample_outliers.csv` - Data with extreme outliers

---

## Pipeline Phases

The validation pipeline consists of 9 deterministic phases:

### 1. **Ingestion**
- Parse CSV/XLSX files
- Normalize column names to snake_case
- Handle encoding detection

### 2. **Standardization**
- Replace null placeholders with `np.nan`
- Strip whitespace from strings
- Remove completely empty rows

### 3. **Schema Inference**
- Detect column types using deterministic rules
- Types: `numeric`, `date`, `categorical`, `string`

### 4. **Validation**
- Detect missing values
- Detect mixed date formats
- Detect duplicates
- Detect outliers (IQR + Z-score + IsolationForest)
- Detect type coercion loss

### 5. **Cleaning**
- Fill missing numeric values with median
- Fill missing categorical values with mode
- Standardize date formats
- Remove duplicates (lenient mode) or flag (strict mode)
- Flag outliers (never removed)

### 6. **Analysis**
- Profile numeric columns (min, max, mean, median, skewness)
- Profile categorical columns (top values, unique count)
- Profile date columns (range, frequency)
- Generate human-readable insights

### 7. **Scoring**
- Calculate health score from weighted components:
  - Completeness (35%)
  - Uniqueness (20%)
  - Consistency (20%)
  - Validity (15%)
  - Outlier penalty (10%)

### 8. **Persistence**
- Store cleaned data to DuckDB
- Persist action log for auditability
- Generate data reference (e.g., `duckdb:ds_001.cleaned`)

### 9. **Reporting**
- Assemble final JSON report
- Include all metadata, issues, and insights

---

## Validation Modes

### Lenient Mode (Default)
- Automatically applies safe fixes
- Removes duplicates
- Fills missing values
- Standardizes formats

### Strict Mode
- Only flags issues, minimal auto-fixing
- Duplicates are flagged but NOT removed
- Requires manual review for critical issues

---

## DuckDB Storage

Cleaned data is stored in `agent_data.db` (configurable) with the following structure:

### Tables
- `{dataset_id}_cleaned` - Cleaned data
- `{dataset_id}_action_log` - Audit trail of all fixes applied

### Querying Data

```python
import duckdb

conn = duckdb.connect('agent_data.db')

# List all datasets
conn.execute("SHOW TABLES").fetchall()

# Query cleaned data
conn.execute("SELECT * FROM ds_a1b2c3d4_cleaned LIMIT 10").fetchdf()

# View action log
conn.execute("SELECT * FROM ds_a1b2c3d4_action_log").fetchdf()

conn.close()
```

---

## Project Structure

```
data_validation_agent/
├── validate_agent.py          # Main FastAPI app
├── requirements.txt            # Dependencies
├── config.yaml                 # Configuration
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
│
├── core/                       # Pipeline modules
│   ├── ingestion.py
│   ├── standardization.py
│   ├── schema_inference.py
│   ├── validation.py
│   ├── cleaning.py
│   ├── analysis.py
│   ├── scoring.py
│   ├── persistence.py
│   └── reporter.py
│
├── utils/                      # Utilities
│   ├── config_loader.py
│   ├── logger.py
│   └── validators.py
│
└── tests/                      # Test suite
    ├── conftest.py
    ├── test_api.py
    ├── test_determinism.py
    ├── test_persistence.py
    └── fixtures/
        ├── sample_clean.csv
        ├── sample_missing_values.csv
        ├── sample_duplicates.csv
        ├── sample_mixed_dates.csv
        └── sample_outliers.csv
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError`
**Solution:** Ensure you're in the correct directory and virtual environment is activated.

```bash
cd Backend/agents/data_validation_agent
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: `Port 8000 already in use`
**Solution:** Use a different port:

```bash
uvicorn validate_agent:app --reload --port 8001
```

### Issue: `File too large` error
**Solution:** Increase `upload.max_bytes` in `config.yaml` or compress your file.

### Issue: Tests failing
**Solution:** Ensure all dependencies are installed and you're running from the correct directory:

```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## Performance

- **Target**: Process 10k rows in < 8 seconds
- **Memory**: Operates in-memory for datasets up to 10k rows
- **Scalability**: For larger datasets, consider chunked processing (future enhancement)

---

## Security & Privacy

- **No PII logging**: Column values are masked in logs
- **File size limits**: Configurable maximum upload size (default: 20 MB)
- **Local storage**: All data stored locally unless `STORAGE_S3_URL` env var is set
- **Input validation**: Strict file format and size checks

---

## Future Enhancements

- [ ] LLM-based advisory layer (suggestions only, no data modification)
- [ ] Support for JSON and Parquet formats
- [ ] Custom column-level constraints
- [ ] Streaming processing for large files
- [ ] Web UI for file upload and visualization
- [ ] Export cleaned data to CSV/XLSX

---

## License

This project is part of the Decider-AI system.

---

## Support

For issues or questions, please refer to the main Decider-AI documentation.

---

**Built with ❤️ using FastAPI, pandas, DuckDB, and scikit-learn**
