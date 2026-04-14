from typing import Sequence

from fastmcp import FastMCP

from .config import SUPPORTED_COUNTRIES, SUPPORTED_ENV_VARS
from .registry import ToolSpec, tool_catalog_entry


def register_resources(
    mcp: FastMCP,
    *,
    package_version: str,
    setup_mode: bool,
    tool_specs: Sequence[ToolSpec],
) -> None:
    @mcp.resource(
        "merit://server/info",
        name="merit_server_info",
        title="Merit API Server Info",
        description="Basic discovery information for the Merit API MCP server.",
    )
    def server_info() -> dict:
        return {
            "name": "merit-api",
            "version": package_version,
            "setup_mode": setup_mode,
            "supported_env_vars": list(SUPPORTED_ENV_VARS),
            "supported_countries": list(SUPPORTED_COUNTRIES),
            "warning": "Mutating tools operate on live accounting data.",
        }

    @mcp.resource(
        "merit://tools/catalog",
        name="merit_tools_catalog",
        title="Merit API Tool Catalog",
        description="Catalog of all registered Merit API MCP tools.",
    )
    def tool_catalog() -> dict:
        return {
            "setup_mode": setup_mode,
            "tools": [tool_catalog_entry(spec) for spec in tool_specs],
        }
