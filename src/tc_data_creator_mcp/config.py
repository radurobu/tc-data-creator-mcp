"""Configuration and constants for the MCP server."""

from pathlib import Path

# Data size limits
MAX_SAMPLE_ROWS = 50000
MAX_SAMPLE_SIZE_MB = 100
MAX_GENERATED_ROWS = 1000000
MAX_COLUMNS = 200

# Output configuration
DEFAULT_OUTPUT_DIR = Path("./synthetic_output")
SUPPORTED_INPUT_FORMATS = ["csv", "json", "parquet"]
SUPPORTED_OUTPUT_FORMATS = ["csv", "json", "parquet"]

# Synthesizer configuration
SUPPORTED_SYNTHESIZERS = ["gaussian_copula", "tvae"]
DEFAULT_SYNTHESIZER = "gaussian_copula"

# Validation thresholds
MIN_QUALITY_SCORE = 0.5
QUALITY_SCORE_WARNING_THRESHOLD = 0.7
