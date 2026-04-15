from unittest.mock import Mock

import pytest

from merit_api import MeritAPI


READ_METHOD_CASES = [
    (
        "customers.get_list",
        lambda client: client.customers.get_list(Name="Acme"),
        ("getcustomers", {"Name": "Acme"}),
        {},
    ),
    (
        "vendors.get_list",
        lambda client: client.vendors.get_list(RegNo="123"),
        ("getvendors", {"RegNo": "123"}),
        {},
    ),
    (
        "items.get_list",
        lambda client: client.items.get_list(Code="ITEM-1"),
        ("getitems", {"Code": "ITEM-1"}),
        {},
    ),
    (
        "sales.get_invoices",
        lambda client: client.sales.get_invoices(PeriodStart="2026-01-01", PeriodEnd="2026-01-31"),
        ("getinvoices", {"PeriodStart": "2026-01-01", "PeriodEnd": "2026-01-31"}),
        {"version": "v2"},
    ),
    (
        "sales.get_invoice",
        lambda client: client.sales.get_invoice("inv-id", add_attachment=True),
        ("getinvoice", {"Id": "inv-id", "AddAttachment": True}),
        {},
    ),
    (
        "sales.get_offers",
        lambda client: client.sales.get_offers(PeriodStart="2026-01-01", PeriodEnd="2026-01-31"),
        ("getoffers", {"PeriodStart": "2026-01-01", "PeriodEnd": "2026-01-31"}),
        {"version": "v2"},
    ),
    (
        "sales.get_recurring_invoices",
        lambda client: client.sales.get_recurring_invoices(PeriodStart="2026-01-01", PeriodEnd="2026-01-31", DateType=0),
        ("getperinvoices", {"PeriodStart": "2026-01-01", "PeriodEnd": "2026-01-31", "DateType": 0}),
        {"version": "v2"},
    ),
    (
        "purchases.get_invoices",
        lambda client: client.purchases.get_invoices(PeriodStart="2026-01-01", PeriodEnd="2026-01-31"),
        ("getpurchorders", {"PeriodStart": "2026-01-01", "PeriodEnd": "2026-01-31"}),
        {},
    ),
    (
        "financial.get_payments",
        lambda client: client.financial.get_payments(PeriodStart="2026-01-01", PeriodEnd="2026-01-31"),
        ("getpayments", {"PeriodStart": "2026-01-01", "PeriodEnd": "2026-01-31"}),
        {},
    ),
    (
        "financial.get_gl_batches",
        lambda client: client.financial.get_gl_batches(PeriodStart="2026-01-01", PeriodEnd="2026-01-31"),
        ("getglbatches", {"PeriodStart": "2026-01-01", "PeriodEnd": "2026-01-31"}),
        {},
    ),
    (
        "financial.get_banks",
        lambda client: client.financial.get_banks(),
        ("getbanks",),
        {},
    ),
    (
        "financial.get_costs",
        lambda client: client.financial.get_costs(),
        ("getcostcenters",),
        {},
    ),
    (
        "financial.get_projects",
        lambda client: client.financial.get_projects(),
        ("getprojects",),
        {},
    ),
    (
        "inventory.get_movements",
        lambda client: client.inventory.get_movements(PeriodStart="2026-01-01", PeriodEnd="2026-01-31"),
        ("getinvmovements", {"PeriodStart": "2026-01-01", "PeriodEnd": "2026-01-31"}),
        {"version": "v2"},
    ),
    (
        "assets.get_fixed_assets",
        lambda client: client.assets.get_fixed_assets(PeriodStart="2026-01-01", PeriodEnd="2026-01-31"),
        ("getfixassets", {"PeriodStart": "2026-01-01", "PeriodEnd": "2026-01-31"}),
        {"version": "v2"},
    ),
    (
        "taxes.get_list",
        lambda client: client.taxes.get_list(),
        ("gettaxes",),
        {},
    ),
    (
        "dimensions.get_list",
        lambda client: client.dimensions.get_list(),
        ("dimensionslist", {"AllValues": False}),
        {"version": "v2"},
    ),
]


@pytest.mark.parametrize("_name,invoke,expected_args,expected_kwargs", READ_METHOD_CASES)
def test_read_methods_delegate_to_expected_endpoints(_name, invoke, expected_args, expected_kwargs):
    client = MeritAPI("test_id", "test_key")
    expected_result = [{"ok": True}]
    client._post = Mock(return_value=expected_result)

    result = invoke(client)

    assert result == expected_result
    client._post.assert_called_once_with(*expected_args, **expected_kwargs)
