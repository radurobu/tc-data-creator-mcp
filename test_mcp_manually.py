"""Manual test script for the MCP server tools."""

import asyncio
import json
from pathlib import Path

# Import the tool functions directly
from src.tc_data_creator_mcp.tools.analyze import analyze_sample_data
from src.tc_data_creator_mcp.tools.generate import generate_synthetic_data
from src.tc_data_creator_mcp.tools.validate import validate_synthetic_quality


async def test_analyze():
    """Test the analyze_sample_data tool."""
    print("\n" + "="*60)
    print("TEST 1: Analyzing Sample Data")
    print("="*60)

    sample_path = "tests/fixtures/sample_users.csv"
    result = await analyze_sample_data(file_path=sample_path)

    print(f"\n[OK] Analyzed {result['row_count']} rows, {result['column_count']} columns")
    print(f"  Data size: {result['size_mb']} MB")
    print(f"\n  Recommended synthesizer: {result['recommendations']['synthesizer']}")
    print(f"  Reason: {result['recommendations']['reason']}")

    print(f"\n  Sample columns:")
    for col in result['columns'][:3]:
        print(f"    - {col['name']}: {col['type']} ({col['unique_count']} unique values)")

    return result


async def test_generate():
    """Test the generate_synthetic_data tool."""
    print("\n" + "="*60)
    print("TEST 2: Generating Synthetic Data")
    print("="*60)

    sample_path = "tests/fixtures/sample_users.csv"

    # Test with constraints
    constraints = {
        "age": {"min": 18, "max": 100},
        "balance": {"min": 0},
    }

    result = await generate_synthetic_data(
        file_path=sample_path,
        synthesizer="gaussian_copula",
        num_rows=50,
        constraints=constraints,
        output_format="csv"
    )

    print(f"\n[OK] Generated {result['rows_generated']} synthetic rows")
    print(f"  Output file: {result['file_path']}")
    print(f"  Quality score: {result['quality_score']:.3f}")
    print(f"  Generation time: {result['generation_time_seconds']}s")

    if result['warnings']:
        print(f"\n  Warnings:")
        for warning in result['warnings']:
            print(f"    [WARN] {warning}")

    return result


async def test_validate():
    """Test the validate_synthetic_quality tool."""
    print("\n" + "="*60)
    print("TEST 3: Validating Quality")
    print("="*60)

    # First generate some data
    sample_path = "tests/fixtures/sample_users.csv"
    gen_result = await generate_synthetic_data(
        file_path=sample_path,
        synthesizer="gaussian_copula",
        num_rows=30,
        output_format="csv"
    )

    synthetic_path = gen_result['file_path']

    # Now validate it
    result = await validate_synthetic_quality(
        original_data_path=sample_path,
        synthetic_data_path=synthetic_path
    )

    print(f"\n[OK] Overall quality score: {result['overall_score']:.3f}")
    print(f"  Schema valid: {result['summary']['schema_valid']}")
    print(f"  Real rows: {result['summary']['rows_real']}")
    print(f"  Synthetic rows: {result['summary']['rows_synthetic']}")

    # Show some column quality scores
    if 'column_metrics' in result['metrics']:
        print(f"\n  Column quality scores:")
        for col, score in list(result['metrics']['column_metrics'].items())[:5]:
            print(f"    - {col}: {score:.3f}")

    if result['warnings']:
        print(f"\n  Warnings:")
        for warning in result['warnings']:
            print(f"    [WARN] {warning}")

    return result


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("TC DATA CREATOR MCP - MANUAL TESTS")
    print("="*60)

    try:
        # Run all tests
        await test_analyze()
        await test_generate()
        await test_validate()

        print("\n" + "="*60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("="*60)
        print("\nYour MCP server is working correctly!")
        print("You can now use it in Claude Code conversations.")

    except Exception as e:
        print(f"\n[FAILED] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
