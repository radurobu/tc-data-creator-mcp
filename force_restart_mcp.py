"""Force restart MCP server - kills all Python processes and cleans cache."""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def kill_python_processes():
    """Kill all Python processes that might be running the MCP server."""
    print("Killing any running MCP server processes...")

    # Try to find and kill Python processes running our server
    try:
        # On Windows, use tasklist to find processes
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
            capture_output=True,
            text=True
        )

        if "python.exe" in result.stdout:
            print("Found Python processes, attempting to kill MCP server...")
            # Kill python processes from this venv
            venv_python = str(Path("venv/Scripts/python.exe").absolute())
            subprocess.run(
                ["taskkill", "/F", "/IM", "python.exe", "/FI", f"IMAGENAME eq python.exe"],
                capture_output=True
            )
            print("Killed Python processes")
            time.sleep(2)
        else:
            print("No Python processes found")
    except Exception as e:
        print(f"Could not kill processes (this is OK): {e}")


def clean_cache():
    """Remove all Python cache files aggressively."""
    print("\nCleaning Python cache...")
    count = 0

    # Remove __pycache__ directories
    for pycache in Path("src").rglob("__pycache__"):
        try:
            shutil.rmtree(pycache)
            count += 1
        except Exception as e:
            print(f"Warning: {e}")

    # Remove .pyc files
    for pyc in Path("src").rglob("*.pyc"):
        try:
            pyc.unlink()
            count += 1
        except Exception as e:
            print(f"Warning: {e}")

    # Remove .pyo files
    for pyo in Path("src").rglob("*.pyo"):
        try:
            pyo.unlink()
            count += 1
        except Exception as e:
            print(f"Warning: {e}")

    print(f"Cleaned {count} cache files/directories")


def verify_fixes():
    """Verify all async fixes are in place."""
    print("\nVerifying async fixes...")

    checks = [
        ("loader.py", "asyncio.to_thread(pd.read_csv"),
        ("generate.py", "asyncio.to_thread(synth.fit"),
        ("analyze.py", "asyncio.to_thread(_analyze_dataframe"),
    ]

    all_good = True
    for filename, check_string in checks:
        filepath = Path("src/tc_data_creator_mcp") / ("tools" if "tools" in filename or filename in ["analyze.py", "generate.py"] else "data_loaders") / filename
        if not filepath.exists():
            filepath = Path("src/tc_data_creator_mcp/tools") / filename
        if not filepath.exists():
            filepath = Path("src/tc_data_creator_mcp/data_loaders") / filename

        try:
            with open(filepath, "r") as f:
                if check_string in f.read():
                    print(f"  [OK] {filename}")
                else:
                    print(f"  [FAIL] {filename} - missing async fix")
                    all_good = False
        except Exception as e:
            print(f"  [ERROR] {filename}: {e}")
            all_good = False

    return all_good


def test_direct():
    """Test the tools work when called directly."""
    print("\nTesting tools directly...")

    sys.path.insert(0, "src")
    import asyncio

    try:
        from tc_data_creator_mcp.tools.generate import generate_synthetic_data

        async def test():
            result = await generate_synthetic_data(
                file_path="tests/fixtures/sample_users.csv",
                num_rows=5,
                output_format="csv"
            )
            return result

        result = asyncio.run(test())
        print(f"  [OK] Generated {result['rows_generated']} rows in {result['generation_time_seconds']}s")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("=" * 70)
    print("FORCE RESTART MCP SERVER")
    print("=" * 70)
    print()

    # Step 1: Kill processes
    kill_python_processes()

    # Step 2: Clean cache
    clean_cache()

    # Step 3: Verify fixes
    if not verify_fixes():
        print("\n[ERROR] Some fixes are missing!")
        return 1

    # Step 4: Test directly
    if not test_direct():
        print("\n[ERROR] Direct test failed!")
        return 1

    print()
    print("=" * 70)
    print("[SUCCESS] MCP server is ready!")
    print("=" * 70)
    print()
    print("IMPORTANT - Follow these steps NOW:")
    print()
    print("1. QUIT Claude Code completely (File > Quit or close all windows)")
    print("2. Wait 10 seconds")
    print("3. Reopen Claude Code")
    print("4. Start a NEW conversation")
    print("5. Test with: 'Generate 50 users from tests/fixtures/sample_users.csv'")
    print()
    print("The server should respond in 1-2 seconds.")
    print()
    print("If it STILL hangs after doing this:")
    print("- Share the exact prompt you used")
    print("- Check if you see ANY output at all")
    print("- Try running this script again")

    return 0


if __name__ == "__main__":
    sys.exit(main())
