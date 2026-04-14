import asyncio
import json
from unittest.mock import Mock

from merit_api import MeritAPI
from merit_api.mcp.config import MeritMCPConfig
from merit_api.mcp.registry import get_tool_specs
from merit_api.mcp.server import build_mcp_server


def _mock_response(status_code=200, payload=None, text=""):
    response = Mock()
    response.status_code = status_code
    response.text = text
    if payload is None:
        response.json.side_effect = ValueError("no json")
    else:
        response.json.return_value = payload
    return response


def test_mcp_registry_exposes_all_current_tools_with_stable_names():
    async def scenario():
        server = build_mcp_server(env={})
        tools = await server.list_tools()
        expected_names = ["get_setup_instructions", *[spec.name for spec in get_tool_specs()]]
        actual_names = [tool.name for tool in tools]

        assert actual_names == expected_names
        assert len(set(actual_names)) == len(actual_names)

        by_name = {tool.name: tool for tool in tools}
        for spec in get_tool_specs():
            tool = by_name[spec.name]
            assert tool.annotations.readOnlyHint is (not spec.mutating)
            assert tool.annotations.destructiveHint is spec.mutating

    asyncio.run(scenario())


def test_setup_mode_returns_setup_guidance_for_api_tools():
    async def scenario():
        server = build_mcp_server(env={})
        result = await server.call_tool("customers_get_list", {"filters": {"Name": "Acme"}})

        assert result.structured_content["mode"] == "setup"
        assert result.structured_content["blocked_tool"] == "customers_get_list"
        assert result.structured_content["blocked_api_method"] == "customers.get_list"

    asyncio.run(scenario())


def test_connected_mode_read_only_tool_calls_underlying_sdk_method():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload=[{"Id": "cust-1"}])
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool("customers_get_list", {"filters": {"Name": "Acme"}})

        assert json.loads(result.content[0].text) == [{"Id": "cust-1"}]
        assert session.post.call_args.args[0].endswith("/v1/getcustomers")

    asyncio.run(scenario())


def test_connected_mode_mutating_tool_returns_raw_sdk_payload():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"Id": "inv-1", "Status": "Created"})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "sales_send_invoice",
            {"payload": {"InvoiceNo": "INV-1", "Customer": {"Id": "cust-1"}}},
        )

        assert result.structured_content == {"Id": "inv-1", "Status": "Created"}
        assert session.post.call_args.args[0].endswith("/v1/sendinvoice")

    asyncio.run(scenario())


def test_connected_mode_scalar_tool_uses_explicit_arguments():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"Id": "inv-5"})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool("sales_get_invoice", {"id": "inv-5", "add_attachment": True})

        assert result.structured_content == {"Id": "inv-5"}
        payload = json.loads(session.post.call_args.kwargs["data"].decode("utf-8"))
        assert payload == {"AddAttachment": True, "Id": "inv-5"}

    asyncio.run(scenario())


def test_mcp_resources_and_prompts_are_available():
    async def scenario():
        server = build_mcp_server(env={})
        resources = await server.list_resources()
        prompts = await server.list_prompts()

        assert [str(resource.uri) for resource in resources] == [
            "merit://server/info",
            "merit://tools/catalog",
        ]
        assert [prompt.name for prompt in prompts] == [
            "setup-merit-api",
            "create-sales-invoice",
            "find-or-create-customer",
        ]

        info = await server.read_resource("merit://server/info")
        catalog = await server.read_resource("merit://tools/catalog")
        setup_prompt = await server.render_prompt("setup-merit-api")
        customer_prompt = await server.render_prompt(
            "find-or-create-customer",
            {"customer_name": "Acme"},
        )

        info_payload = json.loads(info.contents[0].content)
        catalog_payload = json.loads(catalog.contents[0].content)

        assert info_payload["setup_mode"] is True
        assert "tools" in catalog_payload
        assert "MERIT_API_ID" in setup_prompt.messages[0].content.text
        assert "Acme" in customer_prompt.messages[0].content.text

    asyncio.run(scenario())
