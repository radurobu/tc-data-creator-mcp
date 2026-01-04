"""Unified data loader for all input sources."""

import asyncio
import json
from pathlib import Path
from typing import Optional
import pandas as pd
from sqlalchemy import create_engine

from ..config import (
    MAX_SAMPLE_ROWS,
    MAX_SAMPLE_SIZE_MB,
    MAX_COLUMNS,
    SUPPORTED_INPUT_FORMATS,
)


async def load_data(
    file_path: Optional[str] = None,
    inline_data: Optional[str] = None,
    db_connection: Optional[str] = None,
    table_name: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load data from various sources.

    Args:
        file_path: Path to data file (CSV, JSON, Parquet)
        inline_data: JSON string with array of objects
        db_connection: Database connection string
        table_name: Table name for database query

    Returns:
        pandas DataFrame with loaded data

    Raises:
        ValueError: If no valid input source provided or data exceeds limits
    """
    # Validate that exactly one input source is provided
    sources_provided = sum([
        bool(file_path),
        bool(inline_data),
        bool(db_connection and table_name),
    ])

    if sources_provided == 0:
        raise ValueError(
            "Must provide exactly one of: file_path, inline_data, or (db_connection + table_name)"
        )
    elif sources_provided > 1:
        raise ValueError(
            "Provide only one input source: file_path, inline_data, or (db_connection + table_name)"
        )

    df = None

    # Load from file
    if file_path:
        df = await _load_from_file(file_path)

    # Load from inline data
    elif inline_data:
        df = await _load_from_inline(inline_data)

    # Load from database
    elif db_connection and table_name:
        df = await _load_from_database(db_connection, table_name)

    # Validate loaded data
    _validate_data(df)

    return df


async def _load_from_file(file_path: str) -> pd.DataFrame:
    """Load data from a file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check file size before loading
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_SAMPLE_SIZE_MB:
        raise ValueError(
            f"File size ({size_mb:.2f}MB) exceeds maximum ({MAX_SAMPLE_SIZE_MB}MB)"
        )

    # Load based on extension (run in thread pool to avoid blocking)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = await asyncio.to_thread(pd.read_csv, path)
    elif suffix == ".json":
        df = await asyncio.to_thread(pd.read_json, path)
    elif suffix == ".parquet":
        df = await asyncio.to_thread(pd.read_parquet, path)
    else:
        raise ValueError(
            f"Unsupported file format: {suffix}. "
            f"Supported formats: {', '.join(SUPPORTED_INPUT_FORMATS)}"
        )

    return df


async def _load_from_inline(inline_data: str) -> pd.DataFrame:
    """Load data from inline JSON string."""
    try:
        data = json.loads(inline_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")

    if not isinstance(data, list):
        raise ValueError("Inline data must be a JSON array of objects")

    if len(data) == 0:
        raise ValueError("Inline data cannot be empty")

    df = await asyncio.to_thread(pd.DataFrame, data)
    return df


async def _load_from_database(db_connection: str, table_name: str) -> pd.DataFrame:
    """Load data from a database table."""
    def _load_db():
        """Inner function to run in thread pool."""
        try:
            engine = create_engine(db_connection)

            # Load with row limit to prevent loading huge tables
            query = f"SELECT * FROM {table_name} LIMIT {MAX_SAMPLE_ROWS}"

            with engine.connect() as conn:
                df = pd.read_sql(query, conn)

            return df

        except Exception as e:
            raise ValueError(f"Database connection error: {e}")

    return await asyncio.to_thread(_load_db)


def _validate_data(df: pd.DataFrame) -> None:
    """Validate loaded data against size limits."""
    if df is None or len(df) == 0:
        raise ValueError("Loaded data is empty")

    row_count = len(df)
    col_count = len(df.columns)
    size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

    if row_count > MAX_SAMPLE_ROWS:
        raise ValueError(
            f"Data has too many rows ({row_count} > {MAX_SAMPLE_ROWS}). "
            "Please provide a smaller sample."
        )

    if col_count > MAX_COLUMNS:
        raise ValueError(
            f"Data has too many columns ({col_count} > {MAX_COLUMNS})"
        )

    if size_mb > MAX_SAMPLE_SIZE_MB:
        raise ValueError(
            f"Data size ({size_mb:.2f}MB) exceeds maximum ({MAX_SAMPLE_SIZE_MB}MB)"
        )
