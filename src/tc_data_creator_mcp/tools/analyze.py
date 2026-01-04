"""Tool for analyzing sample data."""

import json
from typing import Optional

from ..data_loaders.loader import load_data
from ..config import MAX_SAMPLE_ROWS, MAX_SAMPLE_SIZE_MB


async def analyze_sample_data(
    file_path: Optional[str] = None,
    inline_data: Optional[str] = None,
    db_connection: Optional[str] = None,
    table_name: Optional[str] = None,
) -> dict:
    """
    Analyze sample data and provide structure, statistics, and recommendations.

    Args:
        file_path: Path to data file
        inline_data: JSON string with inline data
        db_connection: Database connection string
        table_name: Table name for database

    Returns:
        Dictionary with analysis results
    """
    # Load the data
    df = await load_data(
        file_path=file_path,
        inline_data=inline_data,
        db_connection=db_connection,
        table_name=table_name,
    )

    # Basic statistics
    row_count = len(df)
    column_count = len(df.columns)
    size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

    # Check limits
    if row_count > MAX_SAMPLE_ROWS:
        raise ValueError(f"Sample data exceeds maximum rows: {row_count} > {MAX_SAMPLE_ROWS}")
    if size_mb > MAX_SAMPLE_SIZE_MB:
        raise ValueError(f"Sample data exceeds maximum size: {size_mb:.2f}MB > {MAX_SAMPLE_SIZE_MB}MB")

    # Analyze each column
    columns_info = []
    for col in df.columns:
        col_data = df[col]
        col_info = {
            "name": col,
            "type": str(col_data.dtype),
            "null_count": int(col_data.isna().sum()),
            "null_percentage": float(col_data.isna().sum() / len(df) * 100),
            "unique_count": int(col_data.nunique()),
        }

        # Add type-specific statistics
        if col_data.dtype in ["int64", "float64"]:
            col_info.update({
                "min": float(col_data.min()) if not col_data.isna().all() else None,
                "max": float(col_data.max()) if not col_data.isna().all() else None,
                "mean": float(col_data.mean()) if not col_data.isna().all() else None,
                "std": float(col_data.std()) if not col_data.isna().all() else None,
            })
            # Suggest constraints
            col_info["suggested_constraints"] = {
                "min": float(col_data.min()) if not col_data.isna().all() else None,
                "max": float(col_data.max()) if not col_data.isna().all() else None,
            }
        elif col_data.dtype == "object":
            # For string columns
            unique_vals = col_data.value_counts().head(10).to_dict()
            col_info["sample_values"] = {str(k): int(v) for k, v in unique_vals.items()}

            # Check if it looks like a categorical column
            if col_data.nunique() / len(df) < 0.5:
                col_info["suggested_constraints"] = {
                    "type": "categorical",
                    "values": col_data.unique().tolist()[:50]  # Limit to 50 categories
                }

        columns_info.append(col_info)

    # Determine recommended synthesizer
    synthesizer_recommendation = {
        "synthesizer": "gaussian_copula",
        "reason": "Fast and suitable for most tabular data with mixed types"
    }

    # If mostly numerical data, GaussianCopula is good
    # If complex patterns or many categorical, suggest TVAE
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
    if len(numeric_cols) / len(df.columns) < 0.3:
        synthesizer_recommendation = {
            "synthesizer": "tvae",
            "reason": "TVAE handles categorical and mixed data types better"
        }

    return {
        "row_count": row_count,
        "column_count": column_count,
        "size_mb": round(size_mb, 2),
        "columns": columns_info,
        "recommendations": synthesizer_recommendation,
    }
