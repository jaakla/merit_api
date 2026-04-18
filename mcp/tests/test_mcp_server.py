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


def test_mcp_registry_exposes_consolidated_tool_names_with_stable_annotations():
    async def scenario():
        server = build_mcp_server(env={})
        tools = await server.list_tools()
        expected_names = ["get_setup_instructions", *[spec.name for spec in get_tool_specs()]]
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
            "merit_write_sales",
            "merit_write_purchases",
            "merit_write_financial",
        ]

        by_name = {tool.name: tool for tool in tools}
        for spec in get_tool_specs():
            tool = by_name[spec.name]
            assert tool.annotations.readOnlyHint is (not spec.mutating)
            assert tool.annotations.destructiveHint is spec.mutating

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

        result = await server.call_tool(
            "merit_write_sales",
            {"action": "sales_invoice_create", "payload": {"InvoiceNo": "INV-1", "Customer": {"Id": "cust-1"}}},
        )

        assert result.structured_content == {"Id": "inv-1", "Status": "Created"}
        assert session.post.call_args.args[0].endswith("/v1/sendinvoice")

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

        result = await server.call_tool(
            "merit_write_customers",
            {"action": "customer_upsert", "payload": {"Name": "Acme OÜ"}},
        )

        assert result.structured_content == {"Id": "cust-1"}
        assert session.post.call_args.args[0].endswith("/v1/sendcustomer")

    asyncio.run(scenario())


def test_connected_mode_write_customers_routes_vendor_update():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"Id": "vend-1"})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_write_customers",
            {
                "action": "vendor_update",
                "payload": {
                    "Id": "vend-1",
                    "BankAccount": "EE382200221020145685",
                    "SWIFT_BIC": "HABAEE2X",
                },
            },
        )

        assert result.structured_content == {"Id": "vend-1"}
        assert session.post.call_args.args[0].endswith("/v2/updatevendor")
        sent_body = json.loads(session.post.call_args.kwargs["data"].decode())
        assert sent_body["BankAccount"] == "EE382200221020145685"

    asyncio.run(scenario())


def test_connected_mode_write_purchases_routes_purchase_invoice_create():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"BillId": "bill-1"})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_write_purchases",
            {"action": "purchase_invoice_create", "payload": {"Vendor": {"Id": "ven-1", "Name": "Vendor"}}},
        )

        assert result.structured_content == {"BillId": "bill-1"}
        assert session.post.call_args.args[0].endswith("/v1/sendpurchinvoice")

    asyncio.run(scenario())


def test_connected_mode_write_financial_routes_item_update():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"Id": "item-1"})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_write_financial",
            {"action": "item_update", "payload": {"Id": "item-1", "Code": "A1"}},
        )

        assert result.structured_content == {"Id": "item-1"}
        assert session.post.call_args.args[0].endswith("/v1/updateitem")

    asyncio.run(scenario())


def test_connected_mode_write_sales_routes_send_email_with_delivnote():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"Message": "OK"})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_write_sales",
            {"action": "sales_invoice_send_email", "id": "inv-7", "delivnote": True},
        )

        assert result.structured_content == {"Message": "OK"}
        payload = json.loads(session.post.call_args.kwargs["data"].decode("utf-8"))
        assert payload == {"Id": "inv-7", "DelivNote": True}

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


def test_connected_mode_write_financial_routes_payment_create_eur_uses_v1():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"InvoiceId": "pay-1"})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_write_financial",
            {
                "action": "purchase_invoice_payment_create",
                "payload": {
                    "BankId": "bank-guid-1",
                    "VendorName": "Acme Inc",
                    "PaymentDate": "202604170000",
                    "BillNo": "S260214",
                    "Amount": 0.01,
                    "IBAN": "EE382200221020145685",
                },
            },
        )

        assert result.structured_content == {"InvoiceId": "pay-1"}
        assert session.post.call_args.args[0].endswith("/v1/sendPaymentV")

    asyncio.run(scenario())


def test_connected_mode_write_financial_routes_payment_create_foreign_currency_uses_v2():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(status_code=200, payload={"InvoiceId": "pay-2"})
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_write_financial",
            {
                "action": "purchase_invoice_payment_create",
                "payload": {
                    "BankId": "bank-guid-2",
                    "VendorName": "Acme Inc",
                    "PaymentDate": "202604170000",
                    "BillNo": "USD-001",
                    "Amount": 5.00,
                    "IBAN": "EE382200221020145685",
                    "CurrencyCode": "USD",
                    "CurrencyRate": 0.92,
                },
            },
        )

        assert result.structured_content == {"InvoiceId": "pay-2"}
        assert session.post.call_args.args[0].endswith("/v2/sendPaymentV")

    asyncio.run(scenario())


def test_connected_mode_write_financial_payment_create_auto_fetches_iban_from_vendor():
    async def scenario():
        def post_side_effect(url, **_):
            if "getvendors" in url:
                return _mock_response(
                    status_code=200,
                    payload=[{"Name": "Acme Inc", "BankAccount": "EE382200221020145685"}],
                )
            return _mock_response(status_code=200, payload={"InvoiceId": "pay-3"})

        session = Mock()
        session.post.side_effect = post_side_effect
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_write_financial",
            {
                "action": "purchase_invoice_payment_create",
                "payload": {
                    "BankId": "bank-guid-1",
                    "VendorName": "Acme Inc",
                    "PaymentDate": "202604170000",
                    "BillNo": "S260214",
                    "Amount": 0.01,
                },
            },
        )

        assert result.structured_content == {"InvoiceId": "pay-3"}
        payment_call = session.post.call_args
        assert payment_call.args[0].endswith("/v1/sendPaymentV")
        sent_body = json.loads(payment_call.kwargs["data"].decode())
        assert sent_body["IBAN"] == "EE382200221020145685"

    asyncio.run(scenario())


def test_connected_mode_write_financial_payment_create_raises_when_iban_not_found():
    async def scenario():
        session = Mock()
        session.post.return_value = _mock_response(
            status_code=200,
            payload=[{"Name": "Acme Inc"}],
        )
        client = MeritAPI("api-id", "api-key", session=session)
        server = build_mcp_server(
            config=MeritMCPConfig(api_id="api-id", api_key="api-key"),
            client_factory=lambda _: client,
        )

        result = await server.call_tool(
            "merit_write_financial",
            {
                "action": "purchase_invoice_payment_create",
                "payload": {
                    "BankId": "bank-guid-1",
                    "VendorName": "Acme Inc",
                    "PaymentDate": "202604170000",
                    "BillNo": "S260214",
                    "Amount": 0.01,
                },
            },
        )

        assert "IBAN" in str(result.structured_content)
        assert "Acme Inc" in str(result.structured_content)

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
        assert [tool["name"] for tool in catalog_payload["tools"]] == [spec.name for spec in get_tool_specs()]
        assert any(action["name"] == "customers_list" for action in catalog_payload["tools"][0]["actions"])
        assert "merit_read_master_data" in invoice_prompt.messages[0].content.text
        assert "merit_write_sales" in invoice_prompt.messages[0].content.text
        assert "merit_write_customers" in customer_prompt.messages[0].content.text

    asyncio.run(scenario())
