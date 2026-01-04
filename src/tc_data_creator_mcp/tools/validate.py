"""Tool for validating synthetic data quality."""

from pathlib import Path
from typing import Optional
import pandas as pd

from ..validators.quality_validator import generate_quality_report


async def validate_synthetic_quality(
    original_data_path: str,
    synthetic_data_path: str,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Validate quality of synthetic data against original data.

    Args:
        original_data_path: Path to original data
        synthetic_data_path: Path to synthetic data
        metadata: Optional metadata about columns and constraints

    Returns:
        Dictionary with detailed quality metrics
    """
    # Load both datasets
    original_path = Path(original_data_path)
    synthetic_path = Path(synthetic_data_path)

    # Determine file type and load
    if original_path.suffix == ".csv":
        original_df = pd.read_csv(original_path)
    elif original_path.suffix == ".json":
        original_df = pd.read_json(original_path)
    elif original_path.suffix == ".parquet":
        original_df = pd.read_parquet(original_path)
    else:
        raise ValueError(f"Unsupported file format: {original_path.suffix}")

    if synthetic_path.suffix == ".csv":
        synthetic_df = pd.read_csv(synthetic_path)
    elif synthetic_path.suffix == ".json":
        synthetic_df = pd.read_json(synthetic_path)
    elif synthetic_path.suffix == ".parquet":
        synthetic_df = pd.read_parquet(synthetic_path)
    else:
        raise ValueError(f"Unsupported file format: {synthetic_path.suffix}")

    # Generate comprehensive quality report
    quality_report = generate_quality_report(original_df, synthetic_df, metadata)

    return quality_report
