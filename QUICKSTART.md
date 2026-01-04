# Quick Start Guide

## Installation (5 minutes)

### 1. Install Dependencies

```bash
cd tc-data-creator-mcp
pip install -r requirements.txt
```

### 2. Configure Claude Desktop

**Windows**: Edit `%APPDATA%\Claude\claude_desktop_config.json`
**MacOS**: Edit `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "tc-data-creator": {
      "command": "python",
      "args": ["-m", "tc_data_creator_mcp.server"]
    }
  }
}
```

### 3. Restart Claude Desktop

Close and reopen Claude Desktop to load the MCP server.

## First Test (2 minutes)

### Option 1: Using the included sample data

Open Claude and try:

```
I have a sample CSV file at tests/fixtures/sample_users.csv.
Can you analyze it and generate 100 synthetic user records?
```

Claude will:
1. Call `analyze_sample_data` to understand your data
2. Call `generate_synthetic_data` to create realistic test data
3. Save the output to `./synthetic_output/synthetic_*.csv`
4. Show you the quality score

### Option 2: Create your own sample data

Create a file `my_data.csv`:

```csv
name,age,salary,department
Alice,28,75000,Engineering
Bob,35,85000,Engineering
Carol,42,95000,Management
David,29,70000,Sales
Eve,31,72000,Sales
```

Then ask Claude:

```
Generate 500 synthetic employee records based on my_data.csv
with these constraints:
- age between 22 and 65
- salary between 50000 and 200000
- department must be one of the existing values
```

## Typical Workflow

### 1. Analyze Your Sample Data

```
Analyze the data in sample_data.csv and tell me what you find
```

Claude calls `analyze_sample_data` and reports:
- Number of rows and columns
- Data types
- Statistics for each column
- Recommended synthesizer

### 2. Generate Synthetic Data

```
Generate 1000 synthetic rows using the GaussianCopula synthesizer.
Add constraints so age is between 18-100 and email addresses are unique.
Save as CSV.
```

Claude calls `generate_synthetic_data` with your constraints.

### 3. Validate Quality (Optional)

```
Validate the quality of the generated data compared to the original
```

Claude calls `validate_synthetic_quality` and shows detailed metrics.

## Advanced Examples

### Example 1: E-commerce Orders

```
I have order data with columns: order_id, customer_id, order_date,
ship_date, quantity, unit_price, total.

Generate 5000 synthetic orders with these rules:
- order_date must be before ship_date
- total = quantity * unit_price
- order_id must be unique
- quantity between 1 and 100
```

### Example 2: Time Series Data

```
I have sensor data with timestamp, temperature, humidity, pressure.
Generate 10000 synthetic readings using TVAE synthesizer.
Temperature should be between -10 and 45 degrees.
```

### Example 3: Database Source

```
Connect to my PostgreSQL database at postgresql://localhost:5432/mydb
and generate synthetic data from the 'transactions' table.
Generate 20000 rows using TVAE.
```

## Troubleshooting

### MCP Server Not Found

1. Check Claude Desktop config file path
2. Verify Python is in your PATH
3. Restart Claude Desktop

### Import Errors

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Low Quality Scores

- Use more sample data (at least 100+ rows)
- Try TVAE instead of GaussianCopula
- Check your sample data quality

## Tips for Best Results

1. **Sample Size**: Provide at least 50-100 rows of sample data
2. **Data Quality**: Ensure sample data is clean and representative
3. **Constraints**: Start simple, add complexity gradually
4. **Synthesizer Choice**:
   - Use GaussianCopula for quick iteration
   - Use TVAE for production-quality data
5. **Validation**: Always check quality scores before using synthetic data

## Next Steps

- Read the full README.md for detailed documentation
- Check out tests/test_basic_generation.py for code examples
- Explore advanced constraints in the README
- Try different synthesizers and compare quality

## Getting Help

If you encounter issues:
1. Check the logs in Claude Desktop
2. Verify your configuration
3. Review the README.md
4. Create an issue on GitHub

Happy synthetic data generation!
