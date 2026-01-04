"""Basic tests for synthetic data generation."""

import pytest
import pandas as pd
from pathlib import Path

from tc_data_creator_mcp.data_loaders.loader import load_data
from tc_data_creator_mcp.synthesizers.factory import create_synthesizer
from tc_data_creator_mcp.validators.quality_validator import generate_quality_report


@pytest.fixture
def sample_data_path():
    """Path to sample CSV file."""
    return Path(__file__).parent / "fixtures" / "sample_users.csv"


@pytest.mark.asyncio
async def test_load_csv_file(sample_data_path):
    """Test loading CSV file."""
    df = await load_data(file_path=str(sample_data_path))

    assert df is not None
    assert len(df) == 20
    assert "user_id" in df.columns
    assert "age" in df.columns


@pytest.mark.asyncio
async def test_load_inline_data():
    """Test loading inline JSON data."""
    inline_json = '''[
        {"id": 1, "value": 100, "category": "A"},
        {"id": 2, "value": 200, "category": "B"},
        {"id": 3, "value": 150, "category": "A"}
    ]'''

    df = await load_data(inline_data=inline_json)

    assert df is not None
    assert len(df) == 3
    assert "id" in df.columns
    assert "value" in df.columns


@pytest.mark.asyncio
async def test_gaussian_copula_synthesis(sample_data_path):
    """Test GaussianCopula synthesizer."""
    # Load sample data
    df = await load_data(file_path=str(sample_data_path))

    # Create and fit synthesizer
    synthesizer = create_synthesizer("gaussian_copula")
    synthesizer.fit(df)

    # Generate synthetic data
    synthetic_df = synthesizer.sample(num_rows=10)

    assert len(synthetic_df) == 10
    assert set(synthetic_df.columns) == set(df.columns)


@pytest.mark.asyncio
async def test_tvae_synthesis(sample_data_path):
    """Test TVAE synthesizer."""
    # Load sample data
    df = await load_data(file_path=str(sample_data_path))

    # Create and fit synthesizer
    synthesizer = create_synthesizer("tvae")
    synthesizer.fit(df)

    # Generate synthetic data
    synthetic_df = synthesizer.sample(num_rows=10)

    assert len(synthetic_df) == 10
    assert set(synthetic_df.columns) == set(df.columns)


@pytest.mark.asyncio
async def test_quality_validation(sample_data_path):
    """Test quality validation."""
    # Load sample data
    df = await load_data(file_path=str(sample_data_path))

    # Generate synthetic data
    synthesizer = create_synthesizer("gaussian_copula")
    synthesizer.fit(df)
    synthetic_df = synthesizer.sample(num_rows=20)

    # Validate quality
    quality_report = generate_quality_report(df, synthetic_df)

    assert "overall_score" in quality_report
    assert "metrics" in quality_report
    assert "warnings" in quality_report
    assert 0.0 <= quality_report["overall_score"] <= 1.0


@pytest.mark.asyncio
async def test_constraints():
    """Test basic constraints."""
    # Create sample data
    df = pd.DataFrame({
        "age": [25, 30, 35, 40, 45],
        "salary": [50000, 60000, 70000, 80000, 90000],
    })

    # Create synthesizer with constraints
    constraints = {
        "age": {"min": 18, "max": 65},
        "salary": {"min": 30000, "max": 150000},
    }

    synthesizer = create_synthesizer("gaussian_copula", constraints)
    synthesizer.fit(df)

    synthetic_df = synthesizer.sample(num_rows=10)

    # Check constraints are satisfied
    assert synthetic_df["age"].min() >= 18
    assert synthetic_df["age"].max() <= 65
    assert synthetic_df["salary"].min() >= 30000
    assert synthetic_df["salary"].max() <= 150000
