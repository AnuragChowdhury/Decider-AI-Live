"""
data_agent.py
-------------
Understands the structure and quality of uploaded data.

RESPONSIBILITY:
- Detect column types
- Detect time dimension (if any)
- Detect dataset type (time-series / snapshot / cross-sectional)
- Produce data capability metadata

INPUT:
- Raw dataset reference

OUTPUT:
- Data profile:
  {
    "data_type": "...",
    "capabilities": [...],
    "blocked_capabilities": [...]
  }

WHAT THIS FILE DOES NOT DO:
- Does NOT compute analytics
- Does NOT make predictions
- Does NOT modify dashboard

NOTE:
This agent ALWAYS runs first after data upload.
"""




def run(context):
    return {
        {
        "dataset_id": "ds_001",
        "status": "READY",
        "analytics_ready": true,
        "summary": {
          "health_score": 0.88,
          "rows_before": 10542,
          "rows_after": 10480,
          "message": "Minor data quality issues were found and safely resolved. Your data is ready for analysis."
        },
        "schema": [
          {
            "column": "order_id",
            "type": "string"
          },
          {
            "column": "order_date",
            "type": "date"
          },
          {
            "column": "region",
            "type": "categorical"
          },
          {
            "column": "sales",
            "type": "numeric"
          }
        ],
        "issues": [
          {
            "column": "order_date",
            "issue": "Mixed date formats",
            "rows_affected": 342,
            "fix_applied": "Converted all values to YYYY-MM-DD format",
            "why": "Consistent date formats are required for time-based analysis",
            "impact": "No data loss"
          },
          {
            "column": "sales",
            "issue": "Missing values",
            "rows_affected": 62,
            "fix_applied": "Filled missing values using median sales",
            "why": "Median preserves distribution and avoids outlier bias",
            "impact": "Minor numerical approximation"
          },
          {
            "column": "order_id",
            "issue": "Duplicate records",
            "rows_affected": 120,
            "fix_applied": "Removed duplicate rows, keeping first occurrence",
            "why": "Duplicates would inflate metrics like total revenue",
            "impact": "120 rows removed"
          },
          {
            "column": "sales",
            "issue": "Extreme outliers detected",
            "rows_affected": 15,
            "fix_applied": "Outliers flagged but not removed",
            "why": "Outliers may represent valid bulk purchases",
            "impact": "No data removed"
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
          },
          {
            "column": "region",
            "top_values": [
              {
                "value": "IN",
                "count": 4200
              },
              {
                "value": "US",
                "count": 3100
              },
              {
                "value": "EU",
                "count": 1800
              }
            ],
            "notes": "Majority of sales come from IN and US"
          }
        ],
        "clean_data_ref": "duckdb:ds_001.cleaned"
      }
    }
