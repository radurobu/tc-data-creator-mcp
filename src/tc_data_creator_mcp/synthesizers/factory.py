"""Factory for creating synthesizers."""

from typing import Any, Dict, Optional

from .base import BaseSynthesizer
from .gaussian_copula import GaussianCopulaSynthesizerWrapper
from .tvae import TVAESynthesizerWrapper
from ..config import SUPPORTED_SYNTHESIZERS


def create_synthesizer(
    synthesizer_type: str,
    constraints: Optional[Dict[str, Any]] = None
) -> BaseSynthesizer:
    """
    Create a synthesizer instance.

    Args:
        synthesizer_type: Type of synthesizer ('gaussian_copula' or 'tvae')
        constraints: Optional constraints configuration

    Returns:
        Synthesizer instance

    Raises:
        ValueError: If synthesizer type is not supported
    """
    if synthesizer_type not in SUPPORTED_SYNTHESIZERS:
        raise ValueError(
            f"Unsupported synthesizer: {synthesizer_type}. "
            f"Supported types: {', '.join(SUPPORTED_SYNTHESIZERS)}"
        )

    if synthesizer_type == "gaussian_copula":
        return GaussianCopulaSynthesizerWrapper(constraints)
    elif synthesizer_type == "tvae":
        return TVAESynthesizerWrapper(constraints)
    else:
        raise ValueError(f"Unknown synthesizer type: {synthesizer_type}")
