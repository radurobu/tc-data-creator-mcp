@echo off
REM Startup script for MCP server with venv activation
cd /d "%~dp0"
call venv\Scripts\activate.bat
python -m tc_data_creator_mcp.server
