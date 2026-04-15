"""
Integration tests for all Merit API read methods.

Requires real credentials. Run with:
    MERIT_API_INTEGRATION_TEST=true pytest tests/test_integration_read.py -v

404 responses are skipped — they indicate a module not enabled on this account.
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

# Rolling 3-month window; Merit API requires YYYYMMDD format.
PERIOD_START = (date.today() - timedelta(days=90)).strftime("%Y%m%d")
PERIOD_END = date.today().strftime("%Y%m%d")


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


def test_customers_get_list(client):
    result = _call(lambda: client.customers.get_list())
    assert isinstance(result, list)


def test_vendors_get_list(client):
    result = _call(lambda: client.vendors.get_list())
    assert isinstance(result, list)


def test_items_get_list(client):
    result = _call(lambda: client.items.get_list())
    assert isinstance(result, list)


def test_taxes_get_list(client):
    result = _call(lambda: client.taxes.get_list())
    assert isinstance(result, list)


def test_dimensions_get_list(client):
    result = _call(lambda: client.dimensions.get_list(all_values=False))
    assert isinstance(result, list)


def test_financial_get_banks(client):
    result = _call(lambda: client.financial.get_banks())
    assert isinstance(result, list)


def test_financial_get_costs(client):
    result = _call(lambda: client.financial.get_costs())
    assert isinstance(result, list)


def test_financial_get_projects(client):
    result = _call(lambda: client.financial.get_projects())
    assert isinstance(result, list)


def test_sales_get_invoices(client):
    result = _call(lambda: client.sales.get_invoices(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))
    assert isinstance(result, list)


def test_sales_get_invoice(client):
    invoices = _call(lambda: client.sales.get_invoices(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))
    if not invoices:
        pytest.skip("No invoices found in the test period.")
    invoice_id = invoices[0].get("SIHId") or invoices[0].get("Id") or invoices[0].get("InvoiceId")
    if not invoice_id:
        pytest.skip("Could not determine invoice id from list response.")
    result = _call(lambda: client.sales.get_invoice(invoice_id))
    assert isinstance(result, dict)


def test_sales_get_offers(client):
    result = _call(lambda: client.sales.get_offers(
        PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END, DateType=0, UnPaid=False,
    ))
    assert isinstance(result, list)


def test_sales_get_recurring_invoices(client):
    result = _call(lambda: client.sales.get_recurring_invoices(
        PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END, DateType=0,
    ))
    assert isinstance(result, list)


def test_purchases_get_invoices(client):
    result = _call(lambda: client.purchases.get_invoices(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))
    assert isinstance(result, list)


def test_financial_get_payments(client):
    result = _call(lambda: client.financial.get_payments(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))
    assert isinstance(result, list)


def test_financial_get_gl_batches(client):
    result = _call(lambda: client.financial.get_gl_batches(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))
    assert isinstance(result, list)


def test_inventory_get_movements(client):
    result = _call(lambda: client.inventory.get_movements(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))
    assert isinstance(result, list)


def test_assets_get_fixed_assets(client):
    result = _call(lambda: client.assets.get_fixed_assets(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))
    assert isinstance(result, list)
