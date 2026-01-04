"""Base synthesizer interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import pandas as pd


class BaseSynthesizer(ABC):
    """Abstract base class for all synthesizers."""

    def __init__(self, constraints: Optional[Dict[str, Any]] = None):
        """
        Initialize synthesizer.

        Args:
            constraints: Optional constraints configuration
        """
        self.constraints = constraints
        self.fitted = False

    @abstractmethod
    def fit(self, data: pd.DataFrame) -> None:
        """
        Fit the synthesizer on sample data.

        Args:
            data: Sample data to learn from
        """
        pass

    @abstractmethod
    def sample(self, num_rows: int) -> pd.DataFrame:
        """
        Generate synthetic samples.

        Args:
            num_rows: Number of rows to generate

        Returns:
            DataFrame with synthetic data
        """
        pass

    def validate(self) -> None:
        """Validate that synthesizer is ready to sample."""
        if not self.fitted:
            raise RuntimeError("Synthesizer must be fitted before sampling")
