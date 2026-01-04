"""Tool for generating synthetic data."""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..data_loaders.loader import load_data
from ..synthesizers.factory import create_synthesizer
from ..validators.quality_validator import generate_quality_report
from ..config import (
    MAX_GENERATED_ROWS,
    DEFAULT_OUTPUT_DIR,
    SUPPORTED_OUTPUT_FORMATS,
)

logger = logging.getLogger(__name__)


async def generate_synthetic_data(
    file_path: Optional[str] = None,
    inline_data: Optional[str] = None,
    db_connection: Optional[str] = None,
    table_name: Optional[str] = None,
    synthesizer: str = "gaussian_copula",
    num_rows: int = 1000,
    constraints: Optional[dict] = None,
    output_format: str = "csv",
    output_path: Optional[str] = None,
) -> dict:
    """
    Generate synthetic test data using SDV.

    Args:
        file_path: Path to sample data file
        inline_data: JSON string with inline data
        db_connection: Database connection string
        table_name: Table name for database
        synthesizer: Type of synthesizer to use
        num_rows: Number of synthetic rows to generate
        constraints: Advanced constraints for generation
        output_format: Output file format
        output_path: Custom output path

    Returns:
        Dictionary with generation results and quality metrics
    """
    start_time = time.time()
    logger.info(f"Starting generation of {num_rows} rows")

    # Validate num_rows
    if num_rows > MAX_GENERATED_ROWS:
        raise ValueError(
            f"Requested rows ({num_rows}) exceeds maximum ({MAX_GENERATED_ROWS})"
        )

    # Load the sample data
    logger.info("Loading sample data...")
    df = await load_data(
        file_path=file_path,
        inline_data=inline_data,
        db_connection=db_connection,
        table_name=table_name,
    )
    logger.info(f"Loaded {len(df)} rows of sample data")

    # Create synthesizer
    logger.info("Creating synthesizer...")
    synth = create_synthesizer(synthesizer, constraints)
    logger.info("Synthesizer created")

    # Fit the synthesizer on sample data
    logger.info("Fitting synthesizer...")
    synth.fit(df)
    logger.info("Synthesizer fitted")

    # Generate synthetic data
    logger.info("Generating synthetic data...")
    synthetic_df = synth.sample(num_rows)
    logger.info(f"Generated {len(synthetic_df)} rows")

    # Determine output path
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"synthetic_{timestamp}.{output_format}"
        output_path = DEFAULT_OUTPUT_DIR / filename
    else:
        output_path = Path(output_path)

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output file
    if output_format == "csv":
        synthetic_df.to_csv(output_path, index=False)
    elif output_format == "json":
        synthetic_df.to_json(output_path, orient="records", indent=2)
    elif output_format == "parquet":
        synthetic_df.to_parquet(output_path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

    # Generate quality report
    quality_report = generate_quality_report(df, synthetic_df)

    generation_time = time.time() - start_time

    return {
        "file_path": str(output_path.absolute()),
        "rows_generated": len(synthetic_df),
        "columns": len(synthetic_df.columns),
        "quality_score": quality_report.get("overall_score", 0.0),
        "quality_report": quality_report,
        "warnings": quality_report.get("warnings", []),
        "generation_time_seconds": round(generation_time, 2),
    }
