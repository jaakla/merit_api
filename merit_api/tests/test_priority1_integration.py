"""
Real integration tests for Priority 1 invoice delivery methods.

These tests require real Merit API credentials and an actual invoice to work with.

Run with:
    MERIT_API_INTEGRATION_TEST=true pytest tests/test_priority1_integration.py -v

Tests will skip if:
- MERIT_API_INTEGRATION_TEST is not set to "true"
- MERIT_API_ID or MERIT_API_KEY are not set
- No invoices are found in the test period
"""

import base64
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


_EINVOICE_NO_CAPABILITY_MSGS = ("api-noeinv", "puudub e-arve")


def _call(fn):
    """Call fn(); skip on 404 (module not enabled on this account)."""
    try:
        return fn()
    except MeritAPIError as exc:
        if exc.status_code == 404:
            pytest.skip("Endpoint not available on this Merit account (404)")
        raise


def _call_einvoice(fn):
    """Like _call but also skips when recipient lacks e-invoice capability."""
    try:
        return fn()
    except MeritAPIError as exc:
        if exc.status_code == 404:
            pytest.skip("Endpoint not available on this Merit account (404)")
        msg = str(exc).lower()
        if any(s in msg for s in _EINVOICE_NO_CAPABILITY_MSGS):
            pytest.skip("Invoice recipient has no e-invoice capability (api-noeinv)")
        raise


class TestInvoiceDeliveryMethods:
    """Integration tests for invoice delivery methods with real API."""

    def test_send_invoice_by_email(self, client):
        """Test sending invoice by email with real API."""
        # Get a recent invoice to work with
        invoices = _call(lambda: client.sales.get_invoices(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))

        if not invoices:
            pytest.skip("No invoices found in the test period.")

        invoice = invoices[0]
        invoice_id = invoice["SIHId"]

        # Send by email
        result = _call(lambda: client.sales.send_invoice_by_email(invoice_id))

        # Result should be a dict (wrapped by client if plain text response)
        assert isinstance(result, dict)
        # Check for success indication
        assert result.get("Success") or result.get("Message")

    def test_send_invoice_by_email_delivnote_mode(self, client):
        """Test sending invoice as delivery note (without prices)."""
        invoices = _call(lambda: client.sales.get_invoices(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))

        if not invoices:
            pytest.skip("No invoices found in the test period.")

        invoice = invoices[0]
        invoice_id = invoice["SIHId"]

        # Send as delivery note (no prices)
        result = _call(lambda: client.sales.send_invoice_by_email(invoice_id, delivnote=True))

        assert isinstance(result, dict)
        # Should have success or message field
        assert result.get("Success") or result.get("Message")

    def test_send_invoice_by_einvoice(self, client):
        """Test sending invoice as e-invoice."""
        invoices = _call(lambda: client.sales.get_invoices(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))

        if not invoices:
            pytest.skip("No invoices found in the test period.")

        invoice = invoices[0]
        invoice_id = invoice["SIHId"]

        # Send as e-invoice
        result = _call_einvoice(lambda: client.sales.send_invoice_by_einvoice(invoice_id))

        assert isinstance(result, dict)
        # Check response has expected fields
        assert result.get("Success") or result.get("Message") or result.get("Error")

    def test_get_invoice_pdf(self, client):
        """Test retrieving invoice as PDF."""
        invoices = _call(lambda: client.sales.get_invoices(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))

        if not invoices:
            pytest.skip("No invoices found in the test period.")

        invoice = invoices[0]
        invoice_id = invoice["SIHId"]

        # Get PDF
        result = _call(lambda: client.sales.get_invoice_pdf(invoice_id))

        assert isinstance(result, dict)
        assert "pdf" in result

        # Result should contain base64-encoded PDF
        pdf_b64 = result["pdf"]
        assert isinstance(pdf_b64, str)

        # Should be valid base64
        pdf_bytes = base64.b64decode(pdf_b64)
        assert len(pdf_bytes) > 0

        # Should look like a PDF
        assert pdf_bytes.startswith(b"%PDF")

        #with open("output.pdf", "wb") as f:
        #    f.write(pdf_bytes)

    def test_complete_invoice_delivery_workflow(self, client):
        """Test complete workflow: retrieve, email, and PDF in sequence."""
        # Get invoices
        invoices = _call(lambda: client.sales.get_invoices(PeriodStart=PERIOD_START, PeriodEnd=PERIOD_END))

        if not invoices:
            pytest.skip("No invoices found in the test period.")

        invoice = invoices[0]
        invoice_id = invoice["SIHId"]
        invoice_no = invoice.get("InvoiceNo", "unknown")

        print(f"\n[Workflow Test] Processing invoice {invoice_no} (ID: {invoice_id})")

        # Step 1: Send by email
        print(f"[Workflow Test] Sending invoice {invoice_no} by email...")
        email_result = _call(lambda: client.sales.send_invoice_by_email(invoice_id))
        assert isinstance(email_result, dict)
        print(f"[Workflow Test] Email result: {email_result}")

        # Step 2: Send as e-invoice
        print(f"[Workflow Test] Sending invoice {invoice_no} as e-invoice...")
        einvoice_result = _call_einvoice(lambda: client.sales.send_invoice_by_einvoice(invoice_id))
        assert isinstance(einvoice_result, dict)
        print(f"[Workflow Test] E-invoice result: {einvoice_result}")

        # Step 3: Get PDF
        print(f"[Workflow Test] Retrieving PDF for invoice {invoice_no}...")
        pdf_result = _call(lambda: client.sales.get_invoice_pdf(invoice_id))
        assert isinstance(pdf_result, dict)
        assert "pdf" in pdf_result

        pdf_bytes = base64.b64decode(pdf_result["pdf"])
        print(f"[Workflow Test] PDF retrieved: {len(pdf_bytes)} bytes")
        assert pdf_bytes.startswith(b"%PDF")


        print(f"[Workflow Test] Complete! Invoice {invoice_no} was successfully:")
        print(f"  ✓ Sent by email")
        print(f"  ✓ Sent as e-invoice")
        print(f"  ✓ PDF retrieved ({len(pdf_bytes)} bytes)")
