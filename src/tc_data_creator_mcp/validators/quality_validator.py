"""Comprehensive quality validation for synthetic data."""

from typing import Any, Dict, Optional
import pandas as pd
import numpy as np
from sdmetrics.reports.single_table import QualityReport
from sdmetrics.single_table import (
    KSComplement,
    CorrelationSimilarity,
    ContingencySimilarity,
)

from ..config import MIN_QUALITY_SCORE, QUALITY_SCORE_WARNING_THRESHOLD


def generate_quality_report(
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate comprehensive quality report for synthetic data.

    Args:
        real_data: Original/sample data
        synthetic_data: Generated synthetic data
        metadata: Optional metadata about columns

    Returns:
        Dictionary with quality metrics and report
    """
    warnings = []
    metrics = {}

    # 1. Schema Validation
    schema_validation = _validate_schema(real_data, synthetic_data)
    metrics["schema_validation"] = schema_validation

    if not schema_validation["valid"]:
        warnings.append("Schema mismatch between real and synthetic data")

    # 2. Basic Statistics Comparison
    stats_comparison = _compare_statistics(real_data, synthetic_data)
    metrics["statistics"] = stats_comparison

    # 3. Column-wise Quality Metrics
    column_metrics = _compute_column_metrics(real_data, synthetic_data)
    metrics["column_metrics"] = column_metrics

    # 4. Correlation Analysis
    correlation_metrics = _analyze_correlations(real_data, synthetic_data)
    metrics["correlation"] = correlation_metrics

    # 5. Use SDMetrics Quality Report
    try:
        quality_report = QualityReport()
        quality_report.generate(real_data, synthetic_data, verbose=False)

        # Get overall score
        overall_score = quality_report.get_score()
        metrics["sdmetrics_score"] = overall_score

        # Get detailed properties
        properties = quality_report.get_properties()
        metrics["sdmetrics_properties"] = properties.to_dict() if hasattr(properties, 'to_dict') else str(properties)

    except Exception as e:
        # If SDMetrics fails, continue with other metrics
        warnings.append(f"SDMetrics quality report failed: {str(e)}")
        overall_score = 0.5  # Default neutral score

    # 6. Privacy Metrics (basic nearest neighbor distance)
    privacy_score = _compute_privacy_score(real_data, synthetic_data)
    metrics["privacy_score"] = privacy_score

    # 7. Diversity Score
    diversity_score = _compute_diversity_score(synthetic_data)
    metrics["diversity_score"] = diversity_score

    # Calculate overall quality score
    # Weighted average of different metrics
    overall_quality = _calculate_overall_quality(metrics)

    # Generate warnings based on scores
    if overall_quality < MIN_QUALITY_SCORE:
        warnings.append(
            f"Quality score ({overall_quality:.2f}) is below minimum threshold ({MIN_QUALITY_SCORE})"
        )
    elif overall_quality < QUALITY_SCORE_WARNING_THRESHOLD:
        warnings.append(
            f"Quality score ({overall_quality:.2f}) is below recommended threshold ({QUALITY_SCORE_WARNING_THRESHOLD})"
        )

    return {
        "overall_score": round(overall_quality, 3),
        "metrics": metrics,
        "warnings": warnings,
        "summary": {
            "rows_real": len(real_data),
            "rows_synthetic": len(synthetic_data),
            "columns": len(real_data.columns),
            "schema_valid": schema_validation["valid"],
        }
    }


def _validate_schema(real_data: pd.DataFrame, synthetic_data: pd.DataFrame) -> Dict[str, Any]:
    """Validate that schemas match."""
    real_cols = set(real_data.columns)
    synth_cols = set(synthetic_data.columns)

    missing_cols = real_cols - synth_cols
    extra_cols = synth_cols - real_cols

    # Check data types
    type_mismatches = []
    for col in real_cols.intersection(synth_cols):
        if real_data[col].dtype != synthetic_data[col].dtype:
            type_mismatches.append({
                "column": col,
                "real_type": str(real_data[col].dtype),
                "synthetic_type": str(synthetic_data[col].dtype),
            })

    return {
        "valid": len(missing_cols) == 0 and len(extra_cols) == 0 and len(type_mismatches) == 0,
        "missing_columns": list(missing_cols),
        "extra_columns": list(extra_cols),
        "type_mismatches": type_mismatches,
    }


def _compare_statistics(real_data: pd.DataFrame, synthetic_data: pd.DataFrame) -> Dict[str, Any]:
    """Compare basic statistics between datasets."""
    stats = {}

    for col in real_data.columns:
        if col not in synthetic_data.columns:
            continue

        real_col = real_data[col]
        synth_col = synthetic_data[col]

        col_stats = {
            "null_percentage_real": float(real_col.isna().sum() / len(real_col) * 100),
            "null_percentage_synthetic": float(synth_col.isna().sum() / len(synth_col) * 100),
        }

        if real_col.dtype in ["int64", "float64"]:
            col_stats.update({
                "mean_real": float(real_col.mean()) if not real_col.isna().all() else None,
                "mean_synthetic": float(synth_col.mean()) if not synth_col.isna().all() else None,
                "std_real": float(real_col.std()) if not real_col.isna().all() else None,
                "std_synthetic": float(synth_col.std()) if not synth_col.isna().all() else None,
                "min_real": float(real_col.min()) if not real_col.isna().all() else None,
                "min_synthetic": float(synth_col.min()) if not synth_col.isna().all() else None,
                "max_real": float(real_col.max()) if not real_col.isna().all() else None,
                "max_synthetic": float(synth_col.max()) if not synth_col.isna().all() else None,
            })

        stats[col] = col_stats

    return stats


def _compute_column_metrics(real_data: pd.DataFrame, synthetic_data: pd.DataFrame) -> Dict[str, Any]:
    """Compute column-wise quality metrics using SDMetrics."""
    column_scores = {}

    for col in real_data.columns:
        if col not in synthetic_data.columns:
            continue

        try:
            # Use KS Complement for numerical columns
            if real_data[col].dtype in ["int64", "float64"]:
                score = KSComplement.compute(
                    real_data=real_data[[col]],
                    synthetic_data=synthetic_data[[col]],
                    column_name=col
                )
            else:
                # For categorical, use contingency similarity
                score = ContingencySimilarity.compute(
                    real_data=real_data[[col]],
                    synthetic_data=synthetic_data[[col]],
                    column_name=col
                )

            column_scores[col] = float(score) if not np.isnan(score) else 0.0

        except Exception:
            column_scores[col] = 0.5  # Neutral score if computation fails

    return column_scores


def _analyze_correlations(real_data: pd.DataFrame, synthetic_data: pd.DataFrame) -> Dict[str, Any]:
    """Analyze correlation preservation."""
    try:
        # Get numeric columns only
        numeric_cols = real_data.select_dtypes(include=["int64", "float64"]).columns

        if len(numeric_cols) < 2:
            return {"score": 1.0, "note": "Not enough numeric columns for correlation analysis"}

        # Compute correlation similarity
        score = CorrelationSimilarity.compute(
            real_data=real_data[numeric_cols],
            synthetic_data=synthetic_data[numeric_cols]
        )

        return {
            "score": float(score) if not np.isnan(score) else 0.5,
            "numeric_columns_analyzed": len(numeric_cols),
        }

    except Exception as e:
        return {"score": 0.5, "error": str(e)}


def _compute_privacy_score(real_data: pd.DataFrame, synthetic_data: pd.DataFrame) -> float:
    """
    Compute privacy score based on nearest neighbor distance.
    Higher score means synthetic data is less similar to any real record (better privacy).
    """
    try:
        # Get numeric columns for distance calculation
        numeric_cols = real_data.select_dtypes(include=["int64", "float64"]).columns

        if len(numeric_cols) == 0:
            return 1.0  # No numeric data to compare

        # Normalize the data
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()

        real_normalized = scaler.fit_transform(real_data[numeric_cols].fillna(0))
        synth_normalized = scaler.transform(synthetic_data[numeric_cols].fillna(0))

        # Compute minimum distance from each synthetic row to real data
        from scipy.spatial.distance import cdist
        distances = cdist(synth_normalized[:100], real_normalized, metric='euclidean')  # Sample 100 rows
        min_distances = distances.min(axis=1)

        # Average minimum distance (normalized to 0-1 scale)
        avg_min_distance = np.mean(min_distances)
        privacy_score = min(avg_min_distance / 10, 1.0)  # Scale to 0-1

        return float(privacy_score)

    except Exception:
        return 0.5  # Neutral score if computation fails


def _compute_diversity_score(synthetic_data: pd.DataFrame) -> float:
    """
    Compute diversity score of synthetic data.
    Higher score means more diverse/unique records.
    """
    try:
        # Count duplicate rows
        duplicate_count = synthetic_data.duplicated().sum()
        diversity = 1 - (duplicate_count / len(synthetic_data))

        return float(diversity)

    except Exception:
        return 0.5


def _calculate_overall_quality(metrics: Dict[str, Any]) -> float:
    """Calculate weighted overall quality score."""
    scores = []

    # SDMetrics score (weight: 40%)
    if "sdmetrics_score" in metrics:
        scores.append(metrics["sdmetrics_score"] * 0.4)

    # Column metrics average (weight: 30%)
    if "column_metrics" in metrics and metrics["column_metrics"]:
        col_avg = np.mean(list(metrics["column_metrics"].values()))
        scores.append(col_avg * 0.3)

    # Correlation score (weight: 15%)
    if "correlation" in metrics and "score" in metrics["correlation"]:
        scores.append(metrics["correlation"]["score"] * 0.15)

    # Privacy score (weight: 10%)
    if "privacy_score" in metrics:
        scores.append(metrics["privacy_score"] * 0.1)

    # Diversity score (weight: 5%)
    if "diversity_score" in metrics:
        scores.append(metrics["diversity_score"] * 0.05)

    # If no scores available, return neutral
    if not scores:
        return 0.5

    return sum(scores)
