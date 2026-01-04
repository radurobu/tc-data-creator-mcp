"""GaussianCopula synthesizer wrapper."""

from typing import Any, Dict, Optional
import pandas as pd
from sdv.single_table import GaussianCopulaSynthesizer
from sdv.metadata import SingleTableMetadata

from .base import BaseSynthesizer
from .constraints_handler import ConstraintsHandler


class GaussianCopulaSynthesizerWrapper(BaseSynthesizer):
    """Wrapper for SDV's GaussianCopula synthesizer."""

    def __init__(self, constraints: Optional[Dict[str, Any]] = None):
        """
        Initialize GaussianCopula synthesizer.

        Args:
            constraints: Optional constraints configuration
        """
        super().__init__(constraints)
        self.synthesizer = None
        self.metadata = None
        self.constraints_handler = ConstraintsHandler(constraints)

    def fit(self, data: pd.DataFrame) -> None:
        """
        Fit the synthesizer on sample data.

        Args:
            data: Sample data to learn from
        """
        # Create metadata
        self.metadata = SingleTableMetadata()
        self.metadata.detect_from_dataframe(data)

        # Build constraints (only for advanced constraints like Unique, Inequality)
        sdv_constraints = self.constraints_handler.build_constraints(data)

        # Create and fit synthesizer with built-in enforcement
        self.synthesizer = GaussianCopulaSynthesizer(
            metadata=self.metadata,
            enforce_min_max_values=True,  # Handles min/max automatically
            enforce_rounding=True,
        )

        # Add only non-deprecated constraints (Unique, Inequality, FixedCombinations)
        valid_constraints = [
            c for c in sdv_constraints
            if type(c).__name__ in ['Unique', 'Inequality', 'FixedCombinations']
        ]

        if valid_constraints:
            self.synthesizer.add_constraints(valid_constraints)

        # Fit the model
        self.synthesizer.fit(data)
        self.fitted = True

    def sample(self, num_rows: int) -> pd.DataFrame:
        """
        Generate synthetic samples.

        Args:
            num_rows: Number of rows to generate

        Returns:
            DataFrame with synthetic data
        """
        self.validate()

        # Generate synthetic data
        synthetic_data = self.synthesizer.sample(num_rows)

        return synthetic_data
