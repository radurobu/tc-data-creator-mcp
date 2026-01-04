"""MCP server with file logging for debugging."""

import logging
import sys
from pathlib import Path

# Set up file logging
log_file = Path(__file__).parent.parent.parent / "mcp_server_debug.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Starting MCP server with debug logging to: {log_file}")

# Import and run the main server
from .server import main

if __name__ == "__main__":
    main()
