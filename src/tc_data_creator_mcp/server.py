"""MCP server for synthetic test data generation."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config import (
    DEFAULT_OUTPUT_DIR,
    SUPPORTED_SYNTHESIZERS,
    SUPPORTED_INPUT_FORMATS,
    SUPPORTED_OUTPUT_FORMATS,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the MCP server instance
app = Server("tc-data-creator-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="analyze_sample_data",
            description=(
                "Analyze sample data to understand structure, types, and statistics. "
                "Provides recommendations for synthesizer selection and constraints. "
                "Accepts file path, inline JSON data, or database connection."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": f"Path to data file ({', '.join(SUPPORTED_INPUT_FORMATS)}). Provide exactly one of: file_path, inline_data, or db_connection+table_name.",
                    },
                    "inline_data": {
                        "type": "string",
                        "description": "JSON string containing inline data (array of objects). Provide exactly one of: file_path, inline_data, or db_connection+table_name.",
                    },
                    "db_connection": {
                        "type": "string",
                        "description": "Database connection string (e.g., postgresql://user:pass@host/db). Provide exactly one of: file_path, inline_data, or db_connection+table_name.",
                    },
                    "table_name": {
                        "type": "string",
                        "description": "Table name (required if using db_connection)",
                    },
                },
            },
        ),
        Tool(
            name="generate_synthetic_data",
            description=(
                "Generate realistic synthetic test data using SDV. "
                "Supports GaussianCopula and TVAE synthesizers with advanced constraints. "
                "Returns path to generated data file and quality metrics."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": f"Path to sample data file ({', '.join(SUPPORTED_INPUT_FORMATS)})",
                    },
                    "inline_data": {
                        "type": "string",
                        "description": "JSON string containing inline sample data",
                    },
                    "db_connection": {
                        "type": "string",
                        "description": "Database connection string",
                    },
                    "table_name": {
                        "type": "string",
                        "description": "Table name (required with db_connection)",
                    },
                    "synthesizer": {
                        "type": "string",
                        "enum": SUPPORTED_SYNTHESIZERS,
                        "description": f"Synthesizer to use: {', '.join(SUPPORTED_SYNTHESIZERS)}",
                        "default": "gaussian_copula",
                    },
                    "num_rows": {
                        "type": "integer",
                        "description": "Number of synthetic rows to generate",
                        "minimum": 1,
                    },
                    "constraints": {
                        "type": "object",
                        "description": "Advanced constraints for data generation (ranges, relationships, formulas)",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": SUPPORTED_OUTPUT_FORMATS,
                        "description": f"Output format: {', '.join(SUPPORTED_OUTPUT_FORMATS)}",
                        "default": "csv",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Custom output file path (optional)",
                    },
                },
                "required": ["num_rows"],
            },
        ),
        Tool(
            name="validate_synthetic_quality",
            description=(
                "Validate quality of synthetic data by comparing with original data. "
                "Provides statistical similarity scores, constraint validation, and quality metrics."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "original_data_path": {
                        "type": "string",
                        "description": "Path to original/sample data file",
                    },
                    "synthetic_data_path": {
                        "type": "string",
                        "description": "Path to synthetic data file",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Optional metadata about columns and constraints",
                    },
                },
                "required": ["original_data_path", "synthetic_data_path"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        logger.info(f"Tool called: {name}")

        if name == "analyze_sample_data":
            logger.info("Importing analyze tool...")
            from .tools.analyze import analyze_sample_data

            logger.info("Calling analyze_sample_data...")
            result = await analyze_sample_data(
                file_path=arguments.get("file_path"),
                inline_data=arguments.get("inline_data"),
                db_connection=arguments.get("db_connection"),
                table_name=arguments.get("table_name"),
            )
            logger.info("Analyze completed")
            return [TextContent(type="text", text=str(result))]

        elif name == "generate_synthetic_data":
            logger.info("Importing generate tool...")
            from .tools.generate import generate_synthetic_data

            logger.info("Calling generate_synthetic_data...")
            result = await generate_synthetic_data(
                file_path=arguments.get("file_path"),
                inline_data=arguments.get("inline_data"),
                db_connection=arguments.get("db_connection"),
                table_name=arguments.get("table_name"),
                synthesizer=arguments.get("synthesizer", "gaussian_copula"),
                num_rows=arguments["num_rows"],
                constraints=arguments.get("constraints"),
                output_format=arguments.get("output_format", "csv"),
                output_path=arguments.get("output_path"),
            )
            logger.info(f"Generate completed: {result.get('rows_generated', 0)} rows")
            return [TextContent(type="text", text=str(result))]

        elif name == "validate_synthetic_quality":
            logger.info("Importing validate tool...")
            from .tools.validate import validate_synthetic_quality

            logger.info("Calling validate_synthetic_quality...")
            result = await validate_synthetic_quality(
                original_data_path=arguments["original_data_path"],
                synthetic_data_path=arguments["synthetic_data_path"],
                metadata=arguments.get("metadata"),
            )
            logger.info("Validate completed")
            return [TextContent(type="text", text=str(result))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def run_server():
    """Run the MCP server."""
    # Ensure output directory exists
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Starting TC Data Creator MCP server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    """Main entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
