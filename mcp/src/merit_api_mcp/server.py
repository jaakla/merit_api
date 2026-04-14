from importlib.metadata import PackageNotFoundError, version
from typing import Any, Callable, Mapping, Optional

from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from merit_api import MeritAPI

from .config import MeritMCPConfig, build_setup_payload, load_config_from_env
from .prompts import register_prompts
from .registry import build_tool_handler, get_tool_specs
from .resources import register_resources


ClientFactory = Callable[[MeritMCPConfig], Any]


def _package_version() -> str:
    try:
        return version("merit-api-mcp-server")
    except PackageNotFoundError:
        return "0.1.0"


def _default_client_factory(config: MeritMCPConfig) -> MeritAPI:
    return MeritAPI(config.api_id, config.api_key, country=config.country)


def build_mcp_server(
    config: Optional[MeritMCPConfig] = None,
    *,
    client_factory: Optional[ClientFactory] = None,
    env: Optional[Mapping[str, str]] = None,
) -> FastMCP:
    resolved_config = config or load_config_from_env(env)
    resolved_client_factory = client_factory or _default_client_factory
    setup_mode = resolved_config is None
    client = None if setup_mode else resolved_client_factory(resolved_config)
    tool_specs = get_tool_specs()

    instructions = (
        "Merit API MCP server for the current Python SDK. "
        "Read-only tools can inspect customers, invoices, payments, and reference data. "
        "Mutating tools can create, update, or delete live accounting records."
    )
    mcp = FastMCP("merit-api", instructions=instructions, version=_package_version())

    @mcp.tool(
        name="get_setup_instructions",
        title="Get Setup Instructions",
        description="Explain how to configure MERIT_API_ID and MERIT_API_KEY for this MCP server.",
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    )
    def get_setup_instructions() -> dict:
        return build_setup_payload()

    def current_client() -> Any:
        return client

    for spec in tool_specs:
        handler = build_tool_handler(
            spec,
            client_getter=current_client,
            setup_payload_builder=build_setup_payload,
        )
        mcp.tool(
            name=spec.name,
            title=spec.title,
            description=spec.mcp_description,
            annotations=ToolAnnotations(
                readOnlyHint=not spec.mutating,
                destructiveHint=spec.mutating,
                idempotentHint=not spec.mutating,
            ),
            meta={"namespace": spec.namespace, "mutating": spec.mutating},
        )(handler)

    register_resources(
        mcp,
        package_version=_package_version(),
        setup_mode=setup_mode,
        tool_specs=tool_specs,
    )
    register_prompts(mcp)
    return mcp


def main() -> None:
    build_mcp_server().run(transport="stdio")
