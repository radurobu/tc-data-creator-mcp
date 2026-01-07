# TC Data Creator MCP

A Model Context Protocol (MCP) server for generating realistic synthetic test data using the Synthetic Data Vault (SDV) library. This tool helps AI coding assistants like Claude generate high-quality, realistic test cases instead of relying on simple random data generation.

## Overview

When developers use AI for creating automated tests, they often rely on the LLM to produce both the test code and test data. However, LLMs may not generate realistic synthetic data that properly represents real-world distributions and relationships. This MCP server solves that problem by providing specialized tools for creating intricate, statistically sound test data.

## Features

- **Multiple Data Sources**: Load sample data from files (CSV, JSON, Parquet), inline JSON, or database connections
- **Advanced Synthesizers**:
  - GaussianCopula: Fast, suitable for most tabular data
  - TVAE: Deep learning-based, handles complex distributions and mixed data types
- **Advanced Constraints**:
  - Basic: min/max ranges, unique values, categorical constraints
  - Relationships: Column inequalities (e.g., start_date < end_date)
  - Custom formulas: Define calculated columns (e.g., total = quantity * price)
  - Conditional constraints: Rules that apply based on other column values
  - Cross-column dependencies: Maintain realistic combinations
- **Comprehensive Quality Validation**:
  - Schema validation
  - Statistical similarity metrics
  - Correlation preservation
  - Privacy metrics (nearest neighbor distance)
  - Diversity scoring
  - Overall quality scores with SDMetrics
- **Safety Limits**: Built-in data size limits to prevent resource exhaustion
- **File Output**: Generated data written to files (CSV, JSON, Parquet) with quality reports

## Installation

### Prerequisites

- Python 3.10 or higher
- pip or uv package manager

### Install from source

```bash
# Clone the repository
git clone https://github.com/radurobu/tc-data-creator-mcp.git
cd tc-data-creator-mcp

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Install from GitHub (without cloning)

```bash
pip install git+https://github.com/radurobu/tc-data-creator-mcp.git
```

### Configure MCP

# 1. Clone and install
  git clone https://github.com/radurobu/tc-data-creator-mcp.git
  cd tc-data-creator-mcp
  pip install -e .

# 2. Copy the MCP config to their project or use globally

The .mcp.json now works on Windows, macOS, and Linux without modification.
{
  "mcpServers": {
    "tc-data-creator": {
      "command": "python",
      "args": ["-m", "tc_data_creator_mcp.server"]
    }
  }
}
```

## MCP Tools

### 1. `analyze_sample_data`

Analyze sample data to understand structure, types, and statistics. Provides recommendations for synthesizer selection and constraints.

**Parameters:**
- `file_path` (optional): Path to data file (CSV, JSON, Parquet)
- `inline_data` (optional): JSON string with array of objects
- `db_connection` (optional): Database connection string
- `table_name` (optional): Table name (required with db_connection)

**Returns:**
- Row count, column count, data size
- Column-by-column analysis with types, statistics, null percentages
- Suggested constraints for each column
- Synthesizer recommendation

**Example:**
```json
{
  "file_path": "./sample_data/users.csv"
}
```

### 2. `generate_synthetic_data`

Generate realistic synthetic test data using SDV synthesizers.

**Parameters:**
- `file_path` / `inline_data` / `db_connection` + `table_name`: Data source (one required)
- `synthesizer`: Type of synthesizer ("gaussian_copula" or "tvae", default: "gaussian_copula")
- `num_rows`: Number of synthetic rows to generate (required)
- `constraints`: Advanced constraints object (optional)
- `output_format`: Output format ("csv", "json", "parquet", default: "csv")
- `output_path`: Custom output path (optional, defaults to ./synthetic_output/)

**Returns:**
- Path to generated data file
- Number of rows and columns generated
- Quality score and detailed quality report
- Warnings (if any)
- Generation time

**Example:**
```json
{
  "file_path": "./sample_data/users.csv",
  "synthesizer": "gaussian_copula",
  "num_rows": 1000,
  "constraints": {
    "age": {"min": 18, "max": 100},
    "email": {"unique": true},
    "relationships": [
      {
        "type": "inequality",
        "low_column": "start_date",
        "high_column": "end_date"
      }
    ]
  },
  "output_format": "csv"
}
```

### 3. `validate_synthetic_quality`

Validate quality of synthetic data by comparing with original data.

**Parameters:**
- `original_data_path`: Path to original/sample data
- `synthetic_data_path`: Path to synthetic data
- `metadata` (optional): Metadata about columns and constraints

**Returns:**
- Overall quality score (0-1)
- Detailed metrics:
  - Schema validation results
  - Statistical comparison
  - Column-wise quality scores
  - Correlation analysis
  - Privacy and diversity scores
- Warnings and recommendations

## Usage Examples

### Basic Usage with Claude

```
User: I need realistic test data for a users table. Here's a sample CSV with 20 rows.

Claude: Let me first analyze your sample data.
[Calls analyze_sample_data with the file path]

Based on the analysis, I'll generate 1000 rows of synthetic data using GaussianCopula.
[Calls generate_synthetic_data]

Generated synthetic data saved to: ./synthetic_output/synthetic_20260103_143022.csv
Quality score: 0.87 (Good)
```

### Advanced Constraints Example

```python
# Generate user data with complex constraints
{
  "file_path": "./users.csv",
  "num_rows": 5000,
  "constraints": {
    "age": {"min": 18, "max": 65},
    "email": {"unique": true},
    "balance": {"min": 0},
    "relationships": [
      {
        "type": "inequality",
        "low_column": "registration_date",
        "high_column": "last_login_date"
      },
      {
        "type": "custom_formula",
        "column": "total_spent",
        "formula": "num_orders * avg_order_value"
      }
    ],
    "conditional": [
      {
        "if": {"column": "country", "value": "USA"},
        "then": {"column": "state", "regex": "^[A-Z]{2}$"}
      }
    ],
    "dependencies": {
      "column": "city",
      "depends_on": ["country", "state"]
    }
  }
}
```

### Database Source Example

```python
{
  "db_connection": "postgresql://user:password@localhost:5432/mydb",
  "table_name": "transactions",
  "num_rows": 10000,
  "synthesizer": "tvae",
  "output_format": "parquet"
}
```

## Configuration

Configuration is in `src/tc_data_creator_mcp/config.py`:

```python
# Data size limits
MAX_SAMPLE_ROWS = 50000        # Max rows in sample data
MAX_SAMPLE_SIZE_MB = 100       # Max file size
MAX_GENERATED_ROWS = 1000000   # Max synthetic rows
MAX_COLUMNS = 200              # Max columns

# Quality thresholds
MIN_QUALITY_SCORE = 0.5
QUALITY_SCORE_WARNING_THRESHOLD = 0.7
```

## Architecture

```
tc-data-creator-mcp/
├── src/tc_data_creator_mcp/
│   ├── server.py                 # MCP server entry point
│   ├── config.py                 # Configuration constants
│   ├── tools/
│   │   ├── analyze.py            # Data analysis tool
│   │   ├── generate.py           # Synthesis tool
│   │   └── validate.py           # Quality validation tool
│   ├── data_loaders/
│   │   └── loader.py             # Unified data loading
│   ├── synthesizers/
│   │   ├── base.py               # Base synthesizer interface
│   │   ├── factory.py            # Synthesizer factory
│   │   ├── gaussian_copula.py    # GaussianCopula wrapper
│   │   ├── tvae.py               # TVAE wrapper
│   │   └── constraints_handler.py # Advanced constraints
│   └── validators/
│       └── quality_validator.py  # Quality metrics
└── tests/
    ├── fixtures/                 # Sample test data
    └── test_basic_generation.py  # Basic tests
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=tc_data_creator_mcp
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

## Synthesizer Comparison

| Feature | GaussianCopula | TVAE |
|---------|---------------|------|
| Speed | Fast | Slower |
| Quality | Good | Excellent |
| Numerical Data | Excellent | Excellent |
| Categorical Data | Good | Excellent |
| Mixed Types | Good | Excellent |
| Training Time | Seconds | Minutes |
| Best For | General purpose, quick iteration | Complex distributions, production |

## Quality Metrics

The quality validator provides comprehensive metrics:

1. **Overall Score (0-1)**: Weighted combination of all metrics
2. **Schema Validation**: Column names, types, nullability
3. **Statistical Similarity**: Mean, std, min, max comparisons
4. **Column Metrics**: KS test for numerical, contingency for categorical
5. **Correlation**: Preservation of column relationships
6. **Privacy**: Minimum distance to real data points
7. **Diversity**: Percentage of unique records

## Limitations

- Maximum sample size: 50,000 rows, 100MB
- Maximum output: 1,000,000 rows
- Database queries limited to MAX_SAMPLE_ROWS
- Custom formula constraints require valid Python expressions
- TVAE requires more memory and training time

## Troubleshooting

### SDV Installation Issues

If you encounter issues installing SDV:
```bash
pip install --upgrade pip
pip install sdv --no-cache-dir
```

### Database Connection Errors

Ensure you have the appropriate database driver installed:
- PostgreSQL: `psycopg2-binary`
- MySQL: `pymysql`
- SQLite: Built-in

### Quality Score Low

If quality scores are consistently low:
1. Increase sample data size (more rows = better learning)
2. Try TVAE instead of GaussianCopula
3. Simplify constraints
4. Check for data quality issues in sample

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure code quality (black, ruff)
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Credits

Built with:
- [Synthetic Data Vault (SDV)](https://github.com/sdv-dev/SDV)
- [SDMetrics](https://github.com/sdv-dev/SDMetrics)
- [Model Context Protocol (MCP)](https://github.com/anthropics/mcp)

## Support

For issues, questions, or contributions:
- GitHub Issues: [Create an issue](https://github.com/radurobu/tc-data-creator-mcp/issues)
- Documentation: See this README

## Changelog

### v0.1.0 (2026-01-03)
- Initial release
- GaussianCopula and TVAE synthesizers
- Advanced constraints support
- Comprehensive quality validation
- File, inline, and database data sources
- CSV, JSON, Parquet output formats
