"""Script to restart MCP server with clean cache."""

import shutil
import subprocess
import sys
from pathlib import Path


def clean_cache():
    """Remove all Python cache files."""
    print("Cleaning Python cache...")
    count = 0
    for pycache in Path("src").rglob("__pycache__"):
        try:
            shutil.rmtree(pycache)
            count += 1
        except Exception as e:
            print(f"Warning: Could not remove {pycache}: {e}")

    for pyc in Path("src").rglob("*.pyc"):
        try:
            pyc.unlink()
            count += 1
        except Exception as e:
            print(f"Warning: Could not remove {pyc}: {e}")

    print(f"Cleaned {count} cache files/directories\n")


def test_imports():
    """Test that all modules import correctly."""
    print("Testing module imports...")

    sys.path.insert(0, "src")

    try:
        from tc_data_creator_mcp.server import main
        print("[OK] server module imports")
    except Exception as e:
        print(f"[FAIL] server module: {e}")
        return False

    try:
        from tc_data_creator_mcp.tools.analyze import analyze_sample_data
        print("[OK] analyze tool imports")
    except Exception as e:
        print(f"[FAIL] analyze tool: {e}")
        return False

    try:
        from tc_data_creator_mcp.tools.generate import generate_synthetic_data
        print("[OK] generate tool imports")
    except Exception as e:
        print(f"[FAIL] generate tool: {e}")
        return False

    print()
    return True


def test_tools():
    """Test that tools work correctly."""
    import asyncio
    sys.path.insert(0, "src")

    from tc_data_creator_mcp.tools.analyze import analyze_sample_data
    from tc_data_creator_mcp.tools.generate import generate_synthetic_data

    async def run_tests():
        print("Testing analyze tool...")
        try:
            result = await analyze_sample_data(
                file_path="tests/fixtures/sample_users.csv"
            )
            print(f"[OK] Analyzed {result['row_count']} rows\n")
        except Exception as e:
            print(f"[FAIL] Analyze failed: {e}\n")
            return False

        print("Testing generate tool...")
        try:
            result = await generate_synthetic_data(
                file_path="tests/fixtures/sample_users.csv",
                num_rows=10,
                output_format="csv"
            )
            print(f"[OK] Generated {result['rows_generated']} rows in {result['generation_time_seconds']}s\n")
        except Exception as e:
            print(f"[FAIL] Generate failed: {e}\n")
            return False

        return True

    return asyncio.run(run_tests())


def main():
    """Run all checks and restart server."""
    print("=" * 60)
    print("MCP SERVER RESTART & DIAGNOSTIC TOOL")
    print("=" * 60)
    print()

    # Step 1: Clean cache
    clean_cache()

    # Step 2: Test imports
    if not test_imports():
        print("\n[ERROR] Import test failed!")
        return 1

    # Step 3: Test tools
    if not test_tools():
        print("\n[ERROR] Tool test failed!")
        return 1

    print("=" * 60)
    print("[SUCCESS] All checks passed!")
    print("=" * 60)
    print()
    print("Your MCP server is ready to use.")
    print("Claude Code will automatically start it when needed.")
    print()
    print("If you still have issues in a new Claude session:")
    print("1. Run this script again: python restart_mcp_server.py")
    print("2. Completely restart Claude Code (File > Quit)")
    print("3. Check .mcp.json configuration is correct")

    return 0


if __name__ == "__main__":
    sys.exit(main())
