"""
Phase 1: Data Ingestion
Parse CSV/XLSX files and normalize columns.
Give metadata about the file (format, size, row/column counts) for downstream processing.
handle dupicate columns
"""

import pandas as pd
import io
from typing import Tuple, Dict, Any
from pathlib import Path
from ..utils.validators import sanitize_column_name


class IngestionError(Exception):
    """Exception raised during data ingestion."""
    pass


def ingest(file_bytes: bytes, filename: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Ingest data from uploaded file.
    
    Args:
        file_bytes: Raw file bytes
        filename: Original filename
        
    Returns:
        Tuple of (DataFrame, metadata dict)
        
    Raises:
        IngestionError: If file cannot be parsed
    """
    file_ext = Path(filename).suffix.lower()
    
    try:
        # Parse based on file extension
        if file_ext == '.csv':
            df = _parse_csv(file_bytes)
        elif file_ext == '.xlsx':
            df = _parse_excel(file_bytes)
        else:
            raise IngestionError(f"Unsupported file format: {file_ext}")
        
        # Check if DataFrame is empty
        if df.empty:
            raise IngestionError("File contains no data")
        
        # Store original column names
        original_columns = df.columns.tolist()
        
        # Normalize column names
        df.columns = [sanitize_column_name(col) for col in df.columns]
        
        # Handle duplicate column names
        df = _handle_duplicate_columns(df)
        
        # Create metadata
        metadata = {
            'filename': filename,
            'file_format': file_ext,
            'rows_before': len(df),
            'columns_raw': len(df.columns),
            'original_columns': original_columns,
            'normalized_columns': df.columns.tolist(),
            'file_size_bytes': len(file_bytes)
        }
        
        return df, metadata
        
    except pd.errors.EmptyDataError:
        raise IngestionError("File is empty or contains no parseable data")
    except pd.errors.ParserError as e:
        raise IngestionError(f"Failed to parse file: {str(e)}")
    except Exception as e:
        raise IngestionError(f"Unexpected error during ingestion: {str(e)}")


def _parse_csv(file_bytes: bytes) -> pd.DataFrame:
    """
    Parse CSV file with automatic encoding detection.
    
    Args:
        file_bytes: Raw CSV bytes
        
    Returns:
        DataFrame
    """
    # Try common encodings
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                encoding=encoding,
                skipinitialspace=True,
                on_bad_lines='skip',
                na_values=['', 'NA', 'N/A', 'null', 'NULL', 'None', 'NONE', 'nan', 'NaN']
            )
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            # If it's not an encoding error, raise it
            if 'codec' not in str(e).lower():
                raise
    
    # If all encodings failed
    raise IngestionError("Could not detect file encoding. Please ensure file is valid CSV.")


def _parse_excel(file_bytes: bytes) -> pd.DataFrame:
    """
    Parse Excel file.
    
    Args:
        file_bytes: Raw Excel bytes
        
    Returns:
        DataFrame
    """
    try:
        # Read first sheet by default
        df = pd.read_excel(
            io.BytesIO(file_bytes),
            engine='openpyxl',
            na_values=['', 'NA', 'N/A', 'null', 'NULL', 'None', 'NONE', 'nan', 'NaN']
        )
        return df
    except Exception as e:
        raise IngestionError(f"Failed to parse Excel file: {str(e)}")


def _handle_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle duplicate column names by appending numeric suffixes.
    
    Args:
        df: DataFrame with potentially duplicate columns
        
    Returns:
        DataFrame with unique column names
    """
    columns = df.columns.tolist()
    seen = {}
    new_columns = []
    
    for col in columns:
        if col in seen:
            seen[col] += 1
            new_col = f"{col}_{seen[col]}"
        else:
            seen[col] = 0
            new_col = col
        new_columns.append(new_col)
    
    df.columns = new_columns
    return df
