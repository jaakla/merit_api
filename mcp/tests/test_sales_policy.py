"""Regression tests for the MCP boundary (HTTP is always mocked)."""
import asyncio
import copy
import json
from unittest.mock import Mock

import pytest

from merit_api import MeritAPI
from merit_api_mcp.config import MeritMCPConfig
from merit_api_mcp.sales_policy import sales_invoice_errors
from merit_api_mcp.server import build_mcp_server
from test_mcp_server import _valid_sales_invoice_payload, _mock_response


def configured():
    session = Mock()
    client = MeritAPI("dummy", "dummy", session=session)
    server = build_mcp_server(
        config=MeritMCPConfig("dummy", "dummy"), client_factory=lambda _: client,
    )
    return server, session


def replace_at(payload, path, value):
    target = payload
    for component in path[:-1]:
        target = target[component]
    target[path[-1]] = value


BAD_FIELDS = [
    (("Payment",), {"PaymentMethod": "Cash", "PaidAmount": 100, "PaymDate": "202609100900"}),
    (("payment",), {}), (("PAYMENT",), {}), (("Payments",), []),
    (("AccountingDoc",), 5), (("AccountingDoc",), 1),
    (("DelivNote",), True), (("DelivNote",), 1), (("DelivNote",), "true"),
    (("delivnote",), False), (("DeliveryType",), True),
    (("DiscountPct",), 200), (("RoundingAmount",), -200),
    (("Customer", "Name"), "Unintended new customer"),
    (("Customer", "Payment"), {}), (("Customer", "Id"), "fake-guid"),
    (("InvoiceRow", 0, "Item", "Type"), 2),
    (("InvoiceRow", 0, "Item", "type"), 2),
    (("InvoiceRow", 0, "Item", "DefLocationCode"), "new-stock"),
    (("InvoiceRow", 0, "Item", "Description"), {"Payment": {}}),
    (("InvoiceRow", 0, "DiscountPct"), 200),
    (("InvoiceRow", 0, "ItemCostAmount"), -100),
    (("InvoiceRow", 0, "LocationCode"), "stock"),
    (("InvoiceRow", 0, "Quantity"), -1), (("InvoiceRow", 0, "Quantity"), 0),
    (("InvoiceRow", 0, "Quantity"), True), (("InvoiceRow", 0, "Price"), -1),
    (("InvoiceRow", 0, "Price"), "100"), (("InvoiceRow", 0, "Price"), float("inf")),
    (("InvoiceRow", 0, "Price"), float("nan")),
    (("InvoiceRow", 0, "TaxId"), "not-a-guid"),
    (("TotalAmount",), -100), (("TotalAmount",), 99999), (("TotalAmount",), "100"),
    (("TaxAmount", 0, "Amount"), -1), (("TaxAmount", 0, "Payment"), {}),
    (("TaxAmount", 0, "TaxId"), "33333333-3333-4333-8333-333333333333"),
    (("DocDate",), "20269999"), (("DueDate",), "20260229"),
    (("TransactionDate",), "20260431"),
    (("CurrencyCode",), "USD"), (("PriceInclVat",), True), (("PriceInclVat",), 0),
    (("FComment",), {"payload": {}}), (("InvoiceRow",), []),
]


@pytest.mark.parametrize("path,value", BAD_FIELDS)
@pytest.mark.parametrize("json_string", [False, True])
def test_unsafe_payloads_are_blocked_on_preview_and_confirm(path, value, json_string):
    async def scenario():
        server, session = configured()
        payload = _valid_sales_invoice_payload()
        replace_at(payload, path, value)
        args = {"action": "sales_invoice_create", "payload": json.dumps(payload) if json_string else payload}
        for suffix in ("", "_confirm"):
            result = await server.call_tool("merit_write_sales" + suffix, {
                **args, "confirmed": True, "confirmation_code": "irrelevant",
            })
            assert result.structured_content["error"] == "ValidationError"
        session.post.assert_not_called()
    asyncio.run(scenario())


def test_credit_invoice_payload_is_rejected_even_after_legitimate_preview():
    async def scenario():
        server, session = configured()
        payload = _valid_sales_invoice_payload()
        preview = await server.call_tool("merit_write_sales", {"action": "sales_invoice_create", "payload": payload})
        payload["InvoiceRow"][0]["Quantity"] = -1
        payload["TotalAmount"] = -100
        result = await server.call_tool("merit_write_sales_confirm", {
            "action": "sales_invoice_create", "payload": payload, "confirmed": True,
            "confirmation_code": preview.structured_content["confirmation_code"],
        })
        assert result.structured_content["error"] == "ValidationError"
        session.post.assert_not_called()
    asyncio.run(scenario())


@pytest.mark.parametrize("item_response", [
    [], {}, None, "OK", {"Success": True},
    [{"Code": "SVC01-other", "Type0": 2}],
    [{"Code": "SVC01", "Type0": 2}, {"Code": "SVC01", "Type0": 2}],
    [{"Code": "SVC01", "Type0": 1}], [{"Code": "SVC01"}],
    [{"Code": "SVC01", "Type0": True}], [{"Code": "SVC01", "Type0": "2"}],
    [{"Code": "SVC01", "Type0": 1, "Type": 2}],
])
def test_unknown_ambiguous_stock_or_malformed_items_never_reach_sendinvoice(item_response):
    async def scenario():
        server, session = configured()
        session.post.return_value = _mock_response(payload=item_response, text="OK")
        args = {"action": "sales_invoice_create", "payload": _valid_sales_invoice_payload()}
        preview = await server.call_tool("merit_write_sales", args)
        session.post.assert_not_called()
        result = await server.call_tool("merit_write_sales_confirm", {
            **args, "confirmed": True, "confirmation_code": preview.structured_content["confirmation_code"],
        })
        assert result.structured_content["error"] == "ValueError"
        assert session.post.call_count == 1
        assert session.post.call_args.args[0].endswith("/getitems")
    asyncio.run(scenario())


@pytest.mark.parametrize("item_response", [
    {"Code": "SVC01", "Type0": 2}, [{"Code": "SVC01", "Type0": 3}],
    [{"Code": "SVC01", "Type": 2}],
    [{"Code": "SVC01-other", "Type0": 1}, {"Code": "SVC01", "Type0": 2}],
])
def test_existing_non_stock_invoice_is_sent_without_other_operations(item_response):
    async def scenario():
        server, session = configured()
        session.post.side_effect = [_mock_response(payload=item_response), _mock_response(payload={"InvoiceId": "mock"})]
        payload = _valid_sales_invoice_payload()
        args = {"action": "sales_invoice_create", "payload": payload}
        preview = await server.call_tool("merit_write_sales", args)
        session.post.assert_not_called()
        description = preview.structured_content["intended_operation"]["description"]
        assert "NOT an unposted draft" in description
        assert "ledger" in description
        result = await server.call_tool("merit_write_sales_confirm", {
            **args, "confirmed": True, "confirmation_code": preview.structured_content["confirmation_code"],
        })
        assert result.structured_content == {"InvoiceId": "mock"}
        assert [c.args[0].rsplit("/", 1)[-1] for c in session.post.call_args_list] == ["getitems", "sendinvoice"]
        assert json.loads(session.post.call_args_list[0].kwargs["data"]) == {"Code": "SVC01"}
        assert json.loads(session.post.call_args_list[1].kwargs["data"]) == payload
    asyncio.run(scenario())


def test_calendar_and_decimal_rounding_and_tax_groups():
    payload = _valid_sales_invoice_payload()
    payload["DocDate"] = "20240229"
    payload["InvoiceRow"][0]["Price"] = 1.005
    payload["InvoiceRow"].append(copy.deepcopy(payload["InvoiceRow"][0]))
    payload["TotalAmount"] = 2.02
    assert sales_invoice_errors(payload) == ()
    payload["TaxAmount"].append(copy.deepcopy(payload["TaxAmount"][0]))
    assert any("only once" in error for error in sales_invoice_errors(payload))


def test_confirmation_rechecks_item_existence_instead_of_caching_preview():
    async def scenario():
        server, session = configured()
        args = {"action": "sales_invoice_create", "payload": _valid_sales_invoice_payload()}
        preview = await server.call_tool("merit_write_sales", args)
        # Even if an item existed earlier, an empty current lookup must stop execution.
        session.post.return_value = _mock_response(payload=[])
        result = await server.call_tool("merit_write_sales_confirm", {
            **args, "confirmed": True, "confirmation_code": preview.structured_content["confirmation_code"],
        })
        assert result.structured_content["error"] == "ValueError"
        assert all(c.args[0].endswith("/getitems") for c in session.post.call_args_list)
    asyncio.run(scenario())
