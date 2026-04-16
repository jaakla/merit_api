"""
Integration tests for Merit API read methods.

Requires real credentials. Run with:
    MERIT_API_INTEGRATION_TEST=true pytest tests/test_integration_read.py -v

404 responses are skipped — they indicate a module not enabled on this account.
Tests that need a concrete entity id also skip when no suitable source data exists.
"""

import os
from datetime import date, timedelta

import pytest

from merit_api import MeritAPI, MeritAPIError

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

API_ID = os.getenv("MERIT_API_ID")
API_KEY = os.getenv("MERIT_API_KEY")
RUN_INTEGRATION = os.getenv("MERIT_API_INTEGRATION_TEST") == "true"

pytestmark = pytest.mark.skipif(
    not RUN_INTEGRATION or not API_ID or not API_KEY,
    reason="Set MERIT_API_INTEGRATION_TEST=true with credentials to run integration tests.",
)

PERIOD_START = (date.today() - timedelta(days=90)).strftime("%Y%m%d")
PERIOD_END = date.today().strftime("%Y%m%d")
PERIOD_START_DASHED = (date.today() - timedelta(days=90)).strftime("%Y-%m-%d")
PERIOD_END_DASHED = date.today().strftime("%Y-%m-%d")


@pytest.fixture(scope="module")
def client():
    return MeritAPI(API_ID, API_KEY)


def _call(fn):
    """Call fn(); skip on 404 (module not enabled on this account)."""
    try:
        return fn()
    except MeritAPIError as exc:
        if exc.status_code == 404:
            pytest.skip("Endpoint not available on this Merit account (404)")
        raise


def _first_id(items, *keys):
    for item in items:
        for key in keys:
            value = item.get(key)
            if value:
                return value
    return None


def _require_sales_invoice_id(client):
    invoices = _call(lambda: client.sales.get_invoices(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))
    if not invoices:
        pytest.skip("No sales invoices found in the test period.")
    invoice_id = _first_id(invoices, "SIHId", "Id", "InvoiceId")
    if not invoice_id:
        pytest.skip("Could not determine sales invoice id from list response.")
    return invoice_id


def _require_sales_offer_id(client):
    offers = _call(
        lambda: client.sales.get_offers(
            PeriodStart=PERIOD_START,
            PeriodEnd=PERIOD_END,
            DateType=0,
            UnPaid=False,
        )
    )
    if not offers:
        pytest.skip("No sales offers found in the test period.")
    offer_id = _first_id(offers, "Id", "OfferId")
    if not offer_id:
        pytest.skip("Could not determine sales offer id from list response.")
    return offer_id


def _require_recurring_invoice_id(client):
    invoices = _call(
        lambda: client.sales.get_recurring_invoices(
            PeriodStart=PERIOD_START,
            PeriodEnd=PERIOD_END,
            DateType=0,
        )
    )
    if not invoices:
        pytest.skip("No recurring invoices found in the test period.")
    recurring_id = _first_id(invoices, "Id", "InvoiceId")
    if not recurring_id:
        pytest.skip("Could not determine recurring invoice id from list response.")
    return recurring_id


def _require_purchase_invoice_id(client):
    invoices = _call(lambda: client.purchases.get_invoices(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))
    if not invoices:
        pytest.skip("No purchase invoices found in the test period.")
    invoice_id = _first_id(invoices, "BillId", "Id", "InvoiceId")
    if not invoice_id:
        pytest.skip("Could not determine purchase invoice id from list response.")
    return invoice_id


def _require_gl_batch_id(client):
    batches = _call(lambda: client.financial.get_gl_batches(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))
    if not batches:
        pytest.skip("No GL batches found in the test period.")
    batch_id = _first_id(batches, "BatchId", "Id")
    if not batch_id:
        pytest.skip("Could not determine GL batch id from list response.")
    return batch_id


def _require_bank_id(client):
    banks = _call(lambda: client.financial.get_banks())
    if not banks:
        pytest.skip("No banks found for this account.")
    bank_id = _first_id(banks, "BankId", "Id")
    if not bank_id:
        pytest.skip("Could not determine bank id from list response.")
    return bank_id


def _require_customer_and_item(client):
    customers = _call(lambda: client.customers.get_list())
    items = _call(lambda: client.items.get_list())
    if not customers:
        pytest.skip("No customers available for pricing tests.")
    if not items:
        pytest.skip("No items available for pricing tests.")

    customer = customers[0]
    item = items[0]

    customer_id = customer.get("Id") or customer.get("CustomerId")
    item_code = item.get("Code")
    item_id = item.get("Id") or item.get("ItemId")

    if not customer_id or not (item_code or item_id):
        pytest.skip("Could not determine customer/item identifiers for pricing tests.")

    payload = {"CustomerId": customer_id}
    if item_code:
        payload["ItemCode"] = item_code
    else:
        payload["ItemId"] = item_id
    return payload


def _extract_more_data_token(payload):
    candidate_keys = ("Id4More", "id4More", "Token", "token", "NextToken", "nextToken", "RequestId", "requestId", "MoreDataKey")
    stack = [payload]

    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key in candidate_keys:
                value = current.get(key)
                if value:
                    return value
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)

    return None


LIST_CASES = [
    ("customers.get_list", lambda client: client.customers.get_list(), list),
    ("customers.get_groups", lambda client: client.customers.get_groups(), list),
    ("vendors.get_list", lambda client: client.vendors.get_list(), list),
    ("vendors.get_groups", lambda client: client.vendors.get_groups(), list),
    ("items.get_list", lambda client: client.items.get_list(), list),
    ("items.get_groups", lambda client: client.items.get_groups(), list),
    (
        "sales.get_invoices",
        lambda client: client.sales.get_invoices(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END),
        list,
    ),
    (
        "sales.get_offers",
        lambda client: client.sales.get_offers(
            PeriodStart=PERIOD_START,
            PeriodEnd=PERIOD_END,
            DateType=0,
            UnPaid=False,
        ),
        list,
    ),
    (
        "sales.get_recurring_invoices",
        lambda client: client.sales.get_recurring_invoices(
            PeriodStart=PERIOD_START,
            PeriodEnd=PERIOD_END,
            DateType=0,
        ),
        list,
    ),
    ("sales.get_recurring_invoice_addresses", lambda client: client.sales.get_recurring_invoice_addresses(), list),
    (
        "purchases.get_invoices",
        lambda client: client.purchases.get_invoices(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END),
        list,
    ),
    (
        "purchases.get_orders",
        lambda client: client.purchases.get_orders(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END),
        list,
    ),
    (
        "financial.get_payments",
        lambda client: client.financial.get_payments(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END),
        list,
    ),
    ("financial.get_payment_types", lambda client: client.financial.get_payment_types(), list),
    (
        "financial.get_payment_imports",
        lambda client: client.financial.get_payment_imports(
            bankId=_require_bank_id(client),
            bookingDateFrom=PERIOD_START_DASHED,
            bookingDateTo=PERIOD_END_DASHED,
            withLines=False,
        ),
        list,
    ),
    (
        "financial.get_gl_batches",
        lambda client: client.financial.get_gl_batches(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END),
        list,
    ),
    (
        "financial.get_gl_batches_full",
        lambda client: client.financial.get_gl_batches_full(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END),
        list,
    ),
    ("financial.get_banks", lambda client: client.financial.get_banks(), list),
    ("financial.get_accounts", lambda client: client.financial.get_accounts(), list),
    ("financial.get_costs", lambda client: client.financial.get_costs(), list),
    ("financial.get_projects", lambda client: client.financial.get_projects(), list),
    ("financial.get_departments", lambda client: client.financial.get_departments(), list),
    ("financial.get_financial_years", lambda client: client.financial.get_financial_years(), dict),
    ("inventory.get_locations", lambda client: client.inventory.get_locations(), list),
    (
        "inventory.get_movements",
        lambda client: client.inventory.get_movements(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END),
        list,
    ),
    ("assets.get_locations", lambda client: client.assets.get_locations(), list),
    ("assets.get_responsible_persons", lambda client: client.assets.get_responsible_persons(), list),
    (
        "assets.get_fixed_assets",
        lambda client: client.assets.get_fixed_assets(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END),
        list,
    ),
    ("taxes.get_list", lambda client: client.taxes.get_list(), list),
    ("dimensions.get_list", lambda client: client.dimensions.get_list(all_values=False), list),
    ("pricing.get_prices", lambda client: client.pricing.get_prices(), list),
    ("pricing.get_discounts", lambda client: client.pricing.get_discounts(), list),
    (
        "reports.get_customer_debts",
        lambda client: client.reports.get_customer_debts(CustName="", OverDueDays=0, DebtDate=PERIOD_END),
        list,
    ),
    (
        "reports.get_customer_payments",
        lambda client: client.reports.get_customer_payments(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END),
        (list, dict),
    ),
    (
        "reports.get_profit",
        lambda client: client.reports.get_profit(EndDate=PERIOD_END, PerCount=3, DepFilter=""),
        dict,
    ),
    (
        "reports.get_balance",
        lambda client: client.reports.get_balance(EndDate=PERIOD_END, PerCount=3),
        dict,
    ),
    (
        "reports.get_inventory",
        lambda client: client.reports.get_inventory(RepDate=PERIOD_END, ShowZero=True, WithReservations=False),
        list,
    ),
    (
        "reports.get_sales",
        lambda client: client.reports.get_sales(StartDate=PERIOD_START, EndDate=PERIOD_END, ReportType=1),
        list,
    ),
    (
        "reports.get_purchases",
        lambda client: client.reports.get_purchases(
            StartDate=PERIOD_START,
            EndDate=PERIOD_END,
            ReportType=1,
            VendChoice=1,
            ByEntryNo=False,
        ),
        list,
    ),
    ("reference.get_units", lambda client: client.reference.get_units(), list),
]


@pytest.mark.parametrize("name,invoke,expected_type", LIST_CASES)
def test_read_list_methods(client, name, invoke, expected_type):
    result = _call(lambda: invoke(client))
    assert isinstance(result, expected_type), f"{name} returned {type(result)}"


def test_sales_get_invoice(client):
    invoice_id = _require_sales_invoice_id(client)
    result = _call(lambda: client.sales.get_invoice(invoice_id))
    assert isinstance(result, dict)


def test_sales_get_offer(client):
    offer_id = _require_sales_offer_id(client)
    result = _call(lambda: client.sales.get_offer(offer_id))
    assert isinstance(result, dict)


def test_sales_get_recurring_invoice(client):
    recurring_id = _require_recurring_invoice_id(client)
    result = _call(lambda: client.sales.get_recurring_invoice(recurring_id))
    assert isinstance(result, dict)


def test_purchases_get_invoice(client):
    invoice_id = _require_purchase_invoice_id(client)
    result = _call(lambda: client.purchases.get_invoice(invoice_id))
    assert isinstance(result, dict)


def test_financial_get_gl_batch(client):
    batch_id = _require_gl_batch_id(client)
    result = _call(lambda: client.financial.get_gl_batch(batch_id))
    assert isinstance(result, dict)


def test_financial_get_expense_payments(client):
    bank_id = _require_bank_id(client)
    result = _call(
        lambda: client.financial.get_expense_payments(
            bank_id,
            docDateFrom=PERIOD_START_DASHED,
            docDateTo=PERIOD_END_DASHED,
        )
    )
    assert isinstance(result, list)


def test_financial_get_income_payments(client):
    bank_id = _require_bank_id(client)
    result = _call(
        lambda: client.financial.get_income_payments(
            bank_id,
            docDateFrom=PERIOD_START_DASHED,
            docDateTo=PERIOD_END_DASHED,
        )
    )
    assert isinstance(result, list)


def test_pricing_get_price(client):
    payload = _require_customer_and_item(client)
    payload["DocDate"] = PERIOD_END
    result = _call(lambda: client.pricing.get_price(**payload))
    assert isinstance(result, (dict, list))


def test_reports_get_more_data(client):
    report = _call(lambda: client.reports.get_customer_payments(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))
    if isinstance(report, dict) and not report.get("HasMore"):
        pytest.skip("Customer payment report has no continuation page for get_more_data.")
    token = _extract_more_data_token(report)
    if not token or token == "00000000-0000-0000-0000-000000000000":
        pytest.skip("Customer payment report did not expose a follow-up token for get_more_data.")
    result = _call(lambda: client.reports.get_more_data(Id4More=token))
    assert isinstance(result, (dict, list))
