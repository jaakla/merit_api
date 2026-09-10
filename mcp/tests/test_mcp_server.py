import asyncio
import json
from unittest.mock import Mock

from merit_api import MeritAPI
from merit_api_mcp.config import MeritMCPConfig
from merit_api_mcp.registry import get_tool_specs
from merit_api_mcp.server import build_mcp_server


def _mock_response(status_code=200, payload=None, text=""):
    response = Mock()
    response.status_code = status_code
    response.text = text
    if payload is None:
        response.json.side_effect = ValueError("no json")
    else:
        response.json.return_value = payload
    return response


def _valid_sales_invoice_payload():
    return {
        "Customer": {"Id": "cust-1"},
        "DocDate": "20260510",
        "TransactionDate": "20260510",
        "DueDate": "20260520",
        "InvoiceNo": "21179",
        "CurrencyCode": "EUR",
        "PriceInclVat": False,
        "InvoiceRow": [
            {
                "Item": {
                    "Code": "SVC01",
                    "Description": "Consulting services",
                    "UOMName": "tk",
                },
                "Quantity": 1,
                "Price": 100,
                "TaxId": "tax-1",
                "Account": "30001",
            }
        ],
        "TaxAmount": [{"TaxId": "tax-1", "Amount": 0}],
        "TotalAmount": 100,
    }


async def _preview_and_confirm(server, tool_name, arguments):
    preview = await server.call_tool(tool_name, arguments)
    preview_payload = preview.structured_content

    assert preview_payload["mode"] == "preview"
    assert preview_payload["tool"] == tool_name
    assert preview_payload["requires_confirmation"] is True
    assert preview_payload["confirmation_tool"] == f"{tool_name}_confirm"
    assert preview_payload["confirmation_code"]

    return await server.call_tool(
        preview_payload["confirmation_tool"],
        {
            **arguments,
            "confirmation_code": preview_payload["confirmation_code"],
            "confirmed": True,
        },
    )


def test_mcp_registry_exposes_consolidated_tool_names_with_stable_annotations():
    async def scenario():
        server = build_mcp_server(env={})
        tools = await server.list_tools()
        expected_names = ["get_setup_instructions"]
        for spec in get_tool_specs():
            expected_names.append(spec.name)
            if spec.mutating:
                expected_names.append(spec.confirm_name)
        actual_names = [tool.name for tool in tools]

        assert actual_names == expected_names
        assert actual_names == [
            "get_setup_instructions",
            "merit_read_master_data",
            "merit_read_sales",
            "merit_read_purchases",
            "merit_read_financial",
            "merit_read_inventory",
            "merit_read_reports",
            "merit_write_customers",
            "merit_write_customers_confirm",
            "merit_write_sales",
            "merit_write_sales_confirm",
        ]

        by_name = {tool.name: tool for tool in tools}
        for spec in get_tool_specs():
            tool = by_name[spec.name]
            assert tool.annotations.readOnlyHint is True
            assert tool.annotations.destructiveHint is False
            if spec.mutating:
                confirm_tool = by_name[spec.confirm_name]
                assert confirm_tool.annotations.readOnlyHint is False
                assert confirm_tool.annotations.destructiveHint is True

        write_sales_description = by_name["merit_write_sales"].description
        assert "sales_invoice_create" in write_sales_description
        assert "InvoiceRow (singular)" in write_sales_description
        assert "InvoiceNo" in write_sales_description
        assert "YYYYMMDD" in write_sales_description

    asyncio.run(scenario())


def test_setup_mode_returns_setup_guidance_for_all_consolidated_tools():
    async def scenario():
        server = build_mcp_server(env={})
        for spec in get_tool_specs():
            first_action = spec.actions[0]
            result = await server.call_tool(spec.name, {"action": first_action.name})

            assert result.structured_content["mode"] == "setup"
            assert result.structured_content["blocked_tool"] == spec.name
            assert result.structured_content["blocked_api_method"] == first_action.api_method

    asyncio.run(scenario())


def test_get_setup_instructions_reports_setup_mode_when_credentials_missing():
    async def scenario():
        server = build_mcp_server(env={})

        result = await server.call_tool("get_setup_instructions", {})

        payload = result.structured_content
        assert payload["mode"] == "setup"
        assert payload["error"] == "Merit API credentials are not configured."
        assert "MERIT_API_ID" in payload["supported_env_vars"]
        assert set(payload["versions"]) == {"mcp_server", "sdk"}

    asyncio.run(scenario())


def test_get_setup_instructions_reports_configured_when_credentials_present():
    async def scenario():
        client = MeritAPI("api-id", "api-key", session=Mock())
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key", country="PL"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool("get_setup_instructions", {})

        payload = result.structured_content
        assert payload["mode"] == "configured"
        assert payload["credentials_present"] is True
        assert payload["country"] == "PL"
        assert "error" not in payload
        assert set(payload["versions"]) == {"mcp_server", "sdk"}

    asyncio.run(scenario())


def test_connected_mode_read_master_data_routes_to_sdk_method():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload=[{"Id": "cust-1"}])
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_read_master_data",
            {"action": "customers_list", "filters": {"Name": "Acme"}},
        )

        assert json.loads(result.content[0].text) == [{"Id": "cust-1"}]
        assert session.post.call_args.args[0].endswith("/v1/getcustomers")

    asyncio.run(scenario())


def test_connected_mode_read_sales_routes_invoice_get_with_add_attachment():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"Id": "inv-5"})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_read_sales",
            {"action": "invoice_get", "id": "inv-5", "add_attachment": True},
        )

        assert json.loads(result.content[0].text) == {"Id": "inv-5"}
        payload = json.loads(session.post.call_args.kwargs["data"].decode("utf-8"))
        assert payload == {"AddAttachment": True, "Id": "inv-5"}

    asyncio.run(scenario())


def test_connected_mode_read_purchases_routes_invoice_get():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"BillId": "bill-1"})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_read_purchases",
            {"action": "invoice_get", "id": "bill-1"},
        )

        assert json.loads(result.content[0].text) == {"BillId": "bill-1"}
        payload = json.loads(session.post.call_args.kwargs["data"].decode("utf-8"))
        assert payload == {"Id": "bill-1", "SkipAttachment": True}

    asyncio.run(scenario())


def test_connected_mode_read_financial_routes_bank_scoped_get_action():
    async def scenario():
        session = Mock()
        session.get.return_value = _mock_response(status_code=200, payload=[{"Id": "expense-1"}])
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_read_financial",
            {
                "action": "expense_payments_list",
                "bank_id": "bank-1",
                "filters": {"docDateFrom": "2026-01-01", "docDateTo": "2026-01-31"},
            },
        )

        assert json.loads(result.content[0].text) == [{"Id": "expense-1"}]
        assert session.get.call_args.args[0].endswith("/v2/Banks/bank-1/ExpensePayments")
        assert session.get.call_args.kwargs["params"]["docDateFrom"] == "2026-01-01"

    asyncio.run(scenario())


def test_connected_mode_read_inventory_routes_price_get():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"ItemCode": "A1", "Price": 12})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_read_inventory",
            {"action": "price_get", "filters": {"ItemCode": "A1", "CustomerId": "cust-1", "DocDate": "20260131"}},
        )

        assert json.loads(result.content[0].text) == {"ItemCode": "A1", "Price": 12}
        payload = json.loads(session.post.call_args.kwargs["data"].decode("utf-8"))
        assert payload["ItemCode"] == "A1"
        assert payload["DocDate"] == "20260131"

    asyncio.run(scenario())


def test_connected_mode_read_reports_routes_profit_report():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"Data": []})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_read_reports",
            {"action": "profit_report_get", "filters": {"EndDate": "20260131", "PerCount": 3, "DepFilter": ""}},
        )

        assert json.loads(result.content[0].text) == {"Data": []}
        assert session.post.call_args.args[0].endswith("/v1/getprofitrep")

    asyncio.run(scenario())


def test_connected_mode_write_sales_routes_invoice_create():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"Id": "inv-1", "Status": "Created"})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await _preview_and_confirm(
            server,
            "merit_write_sales",
            {"action": "sales_invoice_create", "payload": _valid_sales_invoice_payload()},
        )

        assert result.structured_content == {"Id": "inv-1", "Status": "Created"}
        assert session.post.call_args.args[0].endswith("/v1/sendinvoice")

    asyncio.run(scenario())


def test_write_sales_invoice_create_rejects_get_response_shape_before_preview():
    async def scenario():
        session = Mock()
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        invalid_payload = {
            "Customer": {"Id": "cust-1"},
            "DocDate": "2026-05-10",
            "DueDate": "20260520",
            "InvoiceNo": 21179,
            "CurrencyCode": "EUR",
            "InvoiceRows": [
                {
                    "Item": {"Code": "SVC01", "Description": "Consulting"},
                    "UOMName": "tk",
                    "Quantity": 1,
                    "Price": 100,
                    "TaxName": "Ei ole käive",
                    "AccountCode": "30001",
                }
            ],
            "TotalAmount": 100,
        }

        result = await server.call_tool(
            "merit_write_sales",
            {"action": "sales_invoice_create", "payload": invalid_payload},
        )

        assert result.structured_content["error"] == "ValidationError"
        validation_errors = result.structured_content["validation_errors"]
        assert any("InvoiceRow (singular)" in error for error in validation_errors)
        assert any("TransactionDate" in error for error in validation_errors)
        assert any("YYYYMMDD" in error for error in validation_errors)
        assert any("InvoiceNo" in error for error in validation_errors)
        assert any("TaxAmount" in error for error in validation_errors)
        assert any("UOMName" in error for error in validation_errors)
        assert any("AccountCode" in error for error in validation_errors)
        assert any("TaxId GUID" in error for error in validation_errors)
        assert session.post.call_count == 0

    asyncio.run(scenario())


def test_read_filters_accepts_json_string_from_bridge():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload=[{"Id": "cust-1"}])
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_read_master_data",
            {"action": "customers_list", "filters": '{"Name": "Acme"}'},
        )

        assert json.loads(result.content[0].text) == [{"Id": "cust-1"}]
        sent_body = json.loads(session.post.call_args.kwargs["data"].decode("utf-8"))
        assert sent_body["Name"] == "Acme"

    asyncio.run(scenario())


def test_write_payload_accepts_json_string_from_bridge():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"Id": "cust-1"})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await _preview_and_confirm(
            server,
            "merit_write_customers",
            {"action": "customer_upsert", "payload": json.dumps({"Name": "Acme OÜ"})},
        )

        assert result.structured_content == {"Id": "cust-1"}
        sent_body = json.loads(session.post.call_args.kwargs["data"].decode("utf-8"))
        assert sent_body["Name"] == "Acme OÜ"

    asyncio.run(scenario())


def test_payload_invalid_json_string_returns_structured_error():
    async def scenario():
        session = Mock()
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_write_customers",
            {"action": "customer_upsert", "payload": "{not valid json"},
        )

        assert result.structured_content["error"] == "ValidationError"
        assert "JSON" in result.structured_content["message"]
        assert any("payload" in error for error in result.structured_content["json_errors"])
        assert session.post.call_count == 0

    asyncio.run(scenario())


def test_connected_mode_write_customers_routes_customer_upsert():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"Id": "cust-1"})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await _preview_and_confirm(
            server,
            "merit_write_customers",
            {"action": "customer_upsert", "payload": {"Name": "Acme OÜ"}},
        )

        assert result.structured_content == {"Id": "cust-1"}
        assert session.post.call_args.args[0].endswith("/v2/sendcustomer")

    asyncio.run(scenario())


def test_removed_write_actions_are_not_available():
    """The write surface is intentionally minimal: preparation only.

    Purchase invoices, payments, taxes, dimensions, items, credit invoices,
    invoice deletion, and delivery (email/e-invoice) must stay unexposed so
    agents cannot write ledger data that is costly to correct later.
    """

    async def scenario():
        server = build_mcp_server(env={})
        tools = {tool.name: tool for tool in await server.list_tools()}

        # The purchases and financial write tools are gone entirely.
        assert "merit_write_purchases" not in tools
        assert "merit_write_purchases_confirm" not in tools
        assert "merit_write_financial" not in tools
        assert "merit_write_financial_confirm" not in tools

        # The remaining write tools keep only the preparation actions.
        assert tools["merit_write_customers"].meta["actions"] == ["customer_upsert"]
        assert tools["merit_write_sales"].meta["actions"] == ["sales_invoice_create"]

        catalog = json.loads((await server.read_resource("merit://tools/catalog")).contents[0].content)
        for action in (
            "vendor_upsert",
            "vendor_update",
            "sales_invoice_delete",
            "credit_invoice_create",
            "sales_invoice_send_email",
            "sales_invoice_send_einvoice",
            "purchase_invoice_create",
            "purchase_invoice_payment_create",
            "tax_upsert",
            "dimensions_add",
            "items_add",
            "item_update",
        ):
            assert action not in [a["name"] for tool in catalog["tools"] for a in tool["actions"]]

    asyncio.run(scenario())


def test_removed_write_action_returns_validation_error_in_connected_mode():
    async def scenario():
        session = Mock()
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool("merit_write_sales", {"action": "sales_invoice_send_email", "id": "inv-7"})

        assert result.structured_content["error"] == "ValidationError"
        assert result.structured_content["allowed_actions"] == ["sales_invoice_create"]
        assert session.post.call_count == 0

    asyncio.run(scenario())


def test_write_tool_preview_does_not_call_sdk_method():
    async def scenario():
        session = Mock()
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_write_sales",
            {"action": "sales_invoice_create", "payload": _valid_sales_invoice_payload()},
        )

        assert result.structured_content["mode"] == "preview"
        assert result.structured_content["confirmation_tool"] == "merit_write_sales_confirm"
        assert result.structured_content["intended_operation"]["api_method"] == "sales.send_invoice"
        assert session.post.call_count == 0

    asyncio.run(scenario())


def test_confirm_tool_without_confirmed_true_only_returns_preview():
    async def scenario():
        session = Mock()
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_write_sales_confirm",
            {"action": "sales_invoice_create", "payload": _valid_sales_invoice_payload()},
        )

        assert result.structured_content["mode"] == "preview"
        assert session.post.call_count == 0

    asyncio.run(scenario())


def test_confirmation_code_is_bound_to_exact_write_arguments():
    async def scenario():
        session = Mock()
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        preview = await server.call_tool(
            "merit_write_sales",
            {"action": "sales_invoice_create", "payload": _valid_sales_invoice_payload()},
        )
        tampered_payload = _valid_sales_invoice_payload()
        tampered_payload["InvoiceNo"] = "99999"
        result = await server.call_tool(
            "merit_write_sales_confirm",
            {
                "action": "sales_invoice_create",
                "payload": tampered_payload,
                "confirmation_code": preview.structured_content["confirmation_code"],
                "confirmed": True,
            },
        )

        assert result.structured_content["error"] == "ConfirmationError"
        assert "does not match" in result.structured_content["message"]
        assert session.post.call_count == 0

    asyncio.run(scenario())


def test_invalid_action_returns_structured_validation_error():
    async def scenario():
        session = Mock()
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool("merit_read_sales", {"action": "not_real"})

        assert result.structured_content["error"] == "ValidationError"
        assert result.structured_content["tool"] == "merit_read_sales"
        assert "invoice_get" in result.structured_content["allowed_actions"]

    asyncio.run(scenario())


def test_missing_required_field_returns_structured_validation_error():
    async def scenario():
        session = Mock()
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool("merit_read_financial", {"action": "expense_payments_list"})

        assert result.structured_content["error"] == "ValidationError"
        assert set(result.structured_content["missing_fields"]) == {"bank_id", "filters"}

    asyncio.run(scenario())


def test_mcp_resources_and_prompts_reference_consolidated_tools():
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
        invoice_prompt = await server.render_prompt("create-sales-invoice")
        customer_prompt = await server.render_prompt(
            "find-or-create-customer",
            {"customer_name": "Acme"},
        )

        info_payload = json.loads(info.contents[0].content)
        catalog_payload = json.loads(catalog.contents[0].content)

        assert info_payload["setup_mode"] is True
        assert set(info_payload["versions"]) == {"mcp_server", "sdk"}
        assert info_payload["sdk_version"] == info_payload["versions"]["sdk"]
        assert [tool["name"] for tool in catalog_payload["tools"]] == [spec.name for spec in get_tool_specs()]
        assert any(action["name"] == "customers_list" for action in catalog_payload["tools"][0]["actions"])
        sales_tool = next(tool for tool in catalog_payload["tools"] if tool["name"] == "merit_write_sales")
        sales_create = next(action for action in sales_tool["actions"] if action["name"] == "sales_invoice_create")
        assert "InvoiceRow (singular)" in sales_create["description"]
        # Tax GUIDs are company-specific and must not be hardcoded; the description
        # instructs resolving them via taxes_list instead.
        assert "7e170b45-fe96-4048-b824-39733c33e734" not in sales_create["description"]
        assert "taxes_list" in sales_create["description"]
        assert "merit_read_master_data" in invoice_prompt.messages[0].content.text
        assert "merit_write_sales" in invoice_prompt.messages[0].content.text
        assert "InvoiceNo" in invoice_prompt.messages[0].content.text
        assert "YYYYMMDD" in invoice_prompt.messages[0].content.text
        assert "merit_write_customers" in customer_prompt.messages[0].content.text

    asyncio.run(scenario())
