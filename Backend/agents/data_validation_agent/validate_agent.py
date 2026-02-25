"""
Data Validation Agent - FastAPI Application
Main entry point for the validation service.
"""

from fastapi import FastAPI, File, UploadFile, Header, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import hashlib
from pathlib import Path

# Import utilities
from .utils.config_loader import load_config
from .utils.logger import setup_logger, get_context_logger
from .utils.validators import validate_file_upload, validate_validation_mode, ValidationError

# Import core pipeline modules
from .core.ingestion import ingest, IngestionError
from .core.standardization import standardize
from .core.schema_inference import infer_schema
from .core.validation import validate
from .core.cleaning import clean
from .core.analysis import analyze
from .core.scoring import calculate_health_score
from .core.persistence import persist_to_sql, persist_to_duckdb, persist_action_log
from .core.reporter import assemble_report, assemble_error_report


# Initialize FastAPI app
app = FastAPI(
    title="Data Validation Agent",
    description="Deterministic data validation and cleaning service",
    version="1.0.0"
)

# Load configuration
config = load_config()

# Setup logger
logger = setup_logger(
    level=config['logging']['level'],
    format_type=config['logging']['format'],
    mask_pii=config['logging']['mask_pii']
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Data Validation Agent",
        "status": "running",
        "version": "1.0.0"
    }



async def run_validation_pipeline(
    file_bytes: bytes,
    filename: str,
    persist: bool = True,
    validation_mode: Optional[str] = "lenient"
) -> Dict[str, Any]:
    """
    Core validation logic, decoupled from FastAPI.
    """
    dataset_id = None
    
    try:
        # Validate and normalize validation mode
        try:
            mode = validate_validation_mode(validation_mode)
        except ValidationError as e:
            logger.error(f"Invalid validation mode: {str(e)}")
            return assemble_error_report(None, str(e))
        
        # Generate deterministic dataset ID from file content
        dataset_id = _generate_dataset_id(file_bytes)
        
        # Get context logger with dataset_id
        ctx_logger = get_context_logger(dataset_id=dataset_id)
        ctx_logger.info(f"Starting validation for file: {filename}")
        
        # ===== PIPELINE EXECUTION =====
        
        # Phase 1: Ingestion
        ctx_logger.info("Phase 1: Ingesting data", extra={'step': 'ingestion'})
        try:
            df, ingest_metadata = ingest(file_bytes, filename)
            ctx_logger.info(
                f"Ingested {ingest_metadata['rows_before']} rows, {ingest_metadata['columns_raw']} columns",
                extra={'step': 'ingestion', 'metrics': ingest_metadata}
            )
        except IngestionError as e:
            ctx_logger.error(f"Ingestion failed: {str(e)}", extra={'step': 'ingestion'})
            return assemble_error_report(dataset_id, f"Failed to parse file: {str(e)}")
        
        rows_before = ingest_metadata['rows_before']
        
        # Phase 2: Standardization
        ctx_logger.info("Phase 2: Standardizing data", extra={'step': 'standardization'})
        df, std_log = standardize(df)
        ctx_logger.info(
            f"Standardized data: {std_log['empty_rows_removed']} empty rows removed",
            extra={'step': 'standardization', 'metrics': std_log}
        )
        
        # Phase 3: Schema Inference
        ctx_logger.info("Phase 3: Inferring schema", extra={'step': 'schema_inference'})
        schema = infer_schema(df, config)
        ctx_logger.info(
            f"Inferred schema for {len(schema)} columns",
            extra={'step': 'schema_inference', 'metrics': {'schema': schema}}
        )
        
        # Phase 4: Validation
        ctx_logger.info("Phase 4: Validating data", extra={'step': 'validation'})
        issues = validate(df, schema, config)
        ctx_logger.info(
            f"Detected {len(issues)} data quality issues",
            extra={'step': 'validation', 'metrics': {'issue_count': len(issues)}}
        )
        
        # Phase 5: Cleaning
        ctx_logger.info("Phase 5: Cleaning data", extra={'step': 'cleaning'})
        df, issues = clean(df, issues, schema, mode, config)
        rows_after = len(df)
        ctx_logger.info(
            f"Cleaned data: {rows_before - rows_after} rows removed",
            extra={'step': 'cleaning', 'metrics': {'rows_after': rows_after}}
        )
        
        # Phase 6: Analysis
        ctx_logger.info("Phase 6: Analyzing data", extra={'step': 'analysis'})
        column_profile = analyze(df, schema, config)
        ctx_logger.info(
            f"Generated profiles for {len(column_profile)} columns",
            extra={'step': 'analysis', 'metrics': {'profile_count': len(column_profile)}}
        )
        
        # Phase 7: Scoring
        ctx_logger.info("Phase 7: Calculating health score", extra={'step': 'scoring'})
        health_score = calculate_health_score(df, issues, config)
        ctx_logger.info(
            f"Health score: {health_score}",
            extra={'step': 'scoring', 'metrics': {'health_score': health_score}}
        )
        
        # Phase 8: Persistence
        clean_data_ref = None
        if persist:
            ctx_logger.info("Phase 8: Persisting to MySQL", extra={'step': 'persistence'})
            # We ignore db_path as persistence is now ENV configured MySQL
            try:
                clean_data_ref = persist_to_sql(df, dataset_id)
                ctx_logger.info(f"Persisted to MySQL → {clean_data_ref}")
            except Exception as sql_err:
                ctx_logger.warning(f"MySQL persist failed ({sql_err}), trying DuckDB fallback...")
                clean_data_ref = persist_to_duckdb(df, dataset_id, None)
            
            # Persist action log if enabled
            if config.get('persistence', {}).get('enable_action_log', True):
                 # Extract actions... code omitted for brevity but logic handles it
                pass
            # Just calling persist_action_log logic is handled inside persistence.py if we kept it
            # But wait, original code extracts actions. I should keep that.
            
            # Re-implementing action log persistence call using new persistence module
            # We need to extract actions first
            actions = [
                {
                    'column': issue['column'],
                    'issue': issue['issue'],
                    'fix_applied': issue['fix_applied'],
                    'rows_affected': issue['rows_affected']
                }
                for issue in issues if issue['fix_applied']
            ]
            persist_action_log(actions, dataset_id)
            
            ctx_logger.info(
                f"Persisted to {clean_data_ref}",
                extra={'step': 'persistence', 'metrics': {'reference': clean_data_ref}}
            )
        
        # Phase 9: Report Assembly
        ctx_logger.info("Phase 9: Assembling report", extra={'step': 'reporter'})
        report = assemble_report(
            dataset_id=dataset_id,
            status='READY',
            rows_before=rows_before,
            rows_after=rows_after,
            health_score=health_score,
            schema=schema,
            issues=issues,
            column_profile=column_profile,
            clean_data_ref=clean_data_ref,
            config=config
        )
        
        ctx_logger.info("Validation completed successfully", extra={'step': 'complete'})
        
        return report
        
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error during validation: {str(e)}", exc_info=True)
        return assemble_error_report(
            dataset_id,
            f"Unexpected error during validation: {str(e)}"
        )


@app.post("/validate")
async def validate_data(
    file: UploadFile = File(...),
    persist: bool = True,
    x_validation_mode: Optional[str] = Header(None, alias="X-Validation-Mode")
):
    """
    Validate and clean uploaded data file.
    
    Args:
        file: Uploaded CSV or XLSX file
        persist: Whether to persist cleaned data (default: True)
        x_validation_mode: Validation mode ('strict' or 'lenient', default: 'lenient')
        
    Returns:
        JSON report with validation results
    """
    try:
        # Read file bytes
        file_bytes = await file.read()
        filename = file.filename
        
        # Validate file upload (Keep this check here as it acts on the raw file metadata from HTTP)
        try:
            validate_file_upload(
                filename=filename,
                file_size=len(file_bytes),
                allowed_extensions=config['upload']['allowed_extensions'],
                max_bytes=config['upload']['max_bytes']
            )
        except ValidationError as e:
            logger.error(f"File validation failed: {str(e)}")
            return JSONResponse(
                status_code=400,
                content=assemble_error_report(None, str(e))
            )
            
        result = await run_validation_pipeline(
            file_bytes=file_bytes,
            filename=filename,
            persist=persist,
            validation_mode=x_validation_mode
        )
        
        # Determine status code based on result 'status'
        status_code = 200
        if result.get("status") == "ERROR":
            status_code = 400
            
        return JSONResponse(status_code=status_code, content=result)
        
    except Exception as e:
        logger.error(f"Endpoint error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=assemble_error_report(None, f"Endpoint error: {str(e)}")
        )


def _generate_dataset_id(file_bytes: bytes) -> str:
    """
    Generate deterministic dataset ID from file content.
    
    Args:
        file_bytes: Raw file bytes
        
    Returns:
        Dataset ID (e.g., 'ds_a1b2c3d4')
    """
    content_hash = hashlib.sha256(file_bytes).hexdigest()[:8]
    return f"ds_{content_hash}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
