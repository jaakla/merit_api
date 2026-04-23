"""
Integration test for purchase invoice creation with PDF attachment.

Run with:
    MERIT_API_INTEGRATION_TEST=true pytest tests/test_purchase_invoice_integration.py -v

Tests will skip if:
- MERIT_API_INTEGRATION_TEST is not set to "true"
- MERIT_API_ID or MERIT_API_KEY are not set
"""

import base64
import os
from datetime import date, datetime, timedelta

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
RUN_PAYMENT_TEST = os.getenv("MERIT_API_PAYMENT_TEST") == "true"

pytestmark = pytest.mark.skipif(
    not RUN_INTEGRATION or not API_ID or not API_KEY,
    reason="Set MERIT_API_INTEGRATION_TEST=true with credentials to run integration tests.",
)

# Account-specific constants derived from real invoice 5e840c75 (Viru Elektrivõrgud OÜ, Feb 2025)
VENDOR_ID = "64206cd4-e999-41c9-b9e3-43bf1f0a1e07"   # Viru Elektrivõrgud OÜ
TAX_ID_ZERO = "7e170b45-fe96-4048-b824-39733c33e734"  # "Ei ole käive" – 0 % VAT
GL_ACCOUNT = "4017"
# Set MERIT_BANK_ID in env to enable payment creation tests
BANK_ID = os.getenv("MERIT_BANK_ID", "")


def _minimal_pdf_b64() -> str:
    """Return a syntactically valid minimal PDF as a base64 string."""
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type /Catalog /Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type /Pages /Kids[3 0 R] /Count 1>>endobj\n"
        b"3 0 obj<</Type /Page /MediaBox[0 0 612 792] /Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f \n"
        b"trailer<</Size 4 /Root 1 0 R>>\n"
        b"startxref\n9\n%%EOF\n"
    )
    return base64.b64encode(pdf).decode("utf-8")


@pytest.fixture(scope="module")
def client():
    return MeritAPI(API_ID, API_KEY)


class TestSendPurchaseInvoiceWithAttachment:
    """Integration tests for purchase invoice creation with PDF attachment."""

    def test_send_purchase_invoice_with_pdf(self, client):
        """Create a purchase invoice with a PDF attachment, verify response, then delete."""
        today = date.today()
        bill_no = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        doc_date = today.strftime("%Y%m%d")
        due_date = (today + timedelta(days=14)).strftime("%Y%m%d")
        amount = 8.01

        payload = {
            "Vendor": {
                "Id": VENDOR_ID,
                "Name": "Viru Elektrivõrgud OÜ",
                "RegNo": "10855041",
            },
            "DocDate": doc_date,
            "DueDate": due_date,
            "TransactionDate": doc_date,
            "BillNo": bill_no,
            "CurrencyCode": "EUR",
            "CurrencyRate": 1.0,
            "InvoiceRow": [
                {
                    "Item": {
                        "Code": "Komm",
                        "Description": "Test purchase invoice row",
                        "UOMName": "tk",
                        "TaxId": TAX_ID_ZERO,
                    },
                    "Quantity": 1.0,
                    "Price": amount,
                    "TaxId": TAX_ID_ZERO,
                    "GLAccountCode": GL_ACCOUNT,
                }
            ],
            "TaxAmount": [
                {"TaxId": TAX_ID_ZERO, "Amount": 0.0}
            ],
            "TotalAmount": amount,
            "RoundingAmount": 0.0,
            "Attachment": {
                "FileName": "test_invoice.pdf",
                "FileContent": _minimal_pdf_b64(),
            },
        }

        result = client.purchases.send_invoice(payload)

        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "BillId" in result, f"Missing BillId in response: {result}"
        bill_id = result["BillId"]
        assert bill_id, "BillId must not be empty"

        # Verify the attachment was stored by fetching the invoice back
        detail = client._post("getpurchorder", {"Id": bill_id, "SkipAttachment": False})
        attachment = detail.get("Attachment")
        assert attachment is not None, "Attachment should be present in fetched invoice"
        assert attachment.get("FileName") == "test_invoice.pdf"
        file_content = attachment.get("FileContent", "")
        assert len(file_content) > 0, "FileContent should not be empty"
        pdf_bytes = base64.b64decode(file_content)
        assert pdf_bytes.startswith(b"%PDF"), "Stored attachment must be a valid PDF"

        # Cleanup: delete the test invoice so it doesn't pollute the books
        client._post("deletepurchinvoice", {"Id": bill_id})


class TestPurchaseInvoicePaymentWorkflow:
    """Integration tests for the purchase invoice payment workflow.

    Verifies that all data required for a bank payment can be assembled from
    Merit records: DueDate from the invoice and IBAN from the vendor.

    Set MERIT_API_PAYMENT_TEST=true AND MERIT_BANK_ID=<guid> to also execute
    the actual sendPaymentV call (creates a real payment — use with care).
    """

    def _create_test_invoice(self, client) -> tuple[str, str, str]:
        """Create a minimal test purchase invoice; return (bill_id, bill_no, due_date)."""
        today = date.today()
        bill_no = f"PAYTEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        doc_date = today.strftime("%Y%m%d")
        due_date = (today + timedelta(days=14)).strftime("%Y%m%d")
        amount = 0.01

        payload = {
            "Vendor": {"Id": VENDOR_ID, "Name": "Viru Elektrivõrgud OÜ"},
            "DocDate": doc_date,
            "DueDate": due_date,
            "TransactionDate": doc_date,
            "BillNo": bill_no,
            "CurrencyCode": "EUR",
            "CurrencyRate": 1.0,
            "InvoiceRow": [
                {
                    "Item": {
                        "Code": "Komm",
                        "Description": "Payment workflow test",
                        "UOMName": "tk",
                        "TaxId": TAX_ID_ZERO,
                    },
                    "Quantity": 1.0,
                    "Price": amount,
                    "TaxId": TAX_ID_ZERO,
                    "GLAccountCode": GL_ACCOUNT,
                }
            ],
            "TaxAmount": [{"TaxId": TAX_ID_ZERO, "Amount": 0.0}],
            "TotalAmount": amount,
            "RoundingAmount": 0.0,
        }
        result = client.purchases.send_invoice(payload)
        assert "BillId" in result, f"Invoice creation failed: {result}"
        return result["BillId"], bill_no, due_date

    def test_invoice_due_date_and_vendor_iban_are_available_for_payment(self, client):
        """Verify that all fields needed for a bank payment can be read from Merit records."""
        bill_id, bill_no, expected_due_date = self._create_test_invoice(client)
        try:
            # 1. Fetch invoice and verify DueDate is present
            invoices = client.purchases.get_invoices(
                PeriodStart=(date.today() - timedelta(days=1)).strftime("%Y%m%d"),
                PeriodEnd=(date.today() + timedelta(days=30)).strftime("%Y%m%d"),
            )
            invoice = next((i for i in invoices if i.get("BillNo") == bill_no), None)
            assert invoice is not None, f"Invoice {bill_no} not found in list"
            due_date_normalized = datetime.fromisoformat(invoice["DueDate"]).strftime("%Y%m%d")
            assert due_date_normalized == expected_due_date, (
                f"DueDate mismatch: expected {expected_due_date}, got {invoice.get('DueDate')}"
            )
            assert invoice.get("VendorName"), "VendorName must be present in invoice list"

            # 2. Fetch vendor and verify BankAccount (IBAN) is present
            vendors = client.vendors.get_list(Name=invoice["VendorName"])
            vendor = next((v for v in vendors if v.get("Id") == VENDOR_ID), None)
            assert vendor is not None, f"Vendor '{invoice['VendorName']}' not found"
            assert vendor.get("BankAccount"), (
                f"Vendor '{invoice['VendorName']}' has no BankAccount — "
                "update vendor record in Merit with IBAN before running payment tests."
            )

            # 3. Verify all payment fields are present
            payment_data = {
                "VendorName": invoice["VendorName"],
                "BillNo": bill_no,
                "Amount": invoice.get("TotalAmount", invoice.get("Amount")),
                "PaymentDate": invoice["DueDate"],
                "IBAN": vendor["BankAccount"],
            }
            for field in ("VendorName", "BillNo", "Amount", "PaymentDate", "IBAN"):
                assert payment_data[field], f"Required payment field '{field}' is empty"

            print(f"\n[Payment Workflow] Invoice {bill_no} ready for payment:")
            print(f"  VendorName:  {payment_data['VendorName']}")
            print(f"  IBAN:        {payment_data['IBAN']}")
            print(f"  Amount:      {payment_data['Amount']}")
            print(f"  PaymentDate: {payment_data['PaymentDate']} (from DueDate)")

        finally:
            client._post("deletepurchinvoice", {"Id": bill_id})

    @pytest.mark.skipif(
        not RUN_PAYMENT_TEST or not BANK_ID,
        reason="Set MERIT_API_PAYMENT_TEST=true and MERIT_BANK_ID=<guid> to run actual payment creation.",
    )
    def test_create_payment_auto_resolves_iban_and_payment_date(self, client):
        """Full payment creation test: auto-resolves IBAN and PaymentDate; raw response is verified."""
        bill_id, bill_no, _ = self._create_test_invoice(client)
        try:
            # Only BankId, VendorName, BillNo, Amount are provided.
            # IBAN and PaymentDate are resolved automatically by create_payment.
            result = client.financial.create_payment({
                "BankId": BANK_ID,
                "VendorName": "Viru Elektrivõrgud OÜ",
                "BillNo": bill_no,
                "Amount": 0.01,
            })

            print(f"\n[Payment Workflow] Raw Merit API response: {result}")

            # Raw response must be returned as-is — all fields Merit sends back
            assert isinstance(result, dict), f"Expected dict response, got {type(result)}: {result}"
            # Merit returns InvoiceId (payment record id) on success
            assert "InvoiceId" in result, f"Missing InvoiceId in payment response: {result}"
            assert result["InvoiceId"], "InvoiceId must not be empty"

        finally:
            client._post("deletepurchinvoice", {"Id": bill_id})
