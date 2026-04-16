"""
Tests for Priority 1 (Critical Sales) invoice delivery methods.

Tests include:
- send_invoice()
- send_invoice_by_email()
- send_invoice_by_einvoice()
- get_invoice_pdf()

Run with: pytest tests/test_priority1_invoice_delivery.py -v
"""

import base64
from unittest.mock import MagicMock, patch

import pytest

from merit_api import MeritAPI


@pytest.fixture
def client():
    """Create a MeritAPI client for testing."""
    return MeritAPI("test_id", "test_key")


@pytest.fixture
def mock_post(client):
    """Mock the _post method."""
    with patch.object(client, "_post") as mock:
        yield mock


@pytest.fixture
def mock_get_pdf(client):
    """Mock the _get_pdf method."""
    with patch.object(client, "_get_pdf") as mock:
        yield mock


# ---------------------------------------------------------------------------
# Realistic TaxId used across tests (matches the structure the real API needs)
# ---------------------------------------------------------------------------
TAX_ID_20 = "b9b25735-6a15-4d4e-8720-25b254ae3d21"  # 20 % VAT (example)


class TestSendInvoice:
    """Tests for sales.send_invoice() — verifies payload structure sent to the API."""

    def test_send_invoice_basic(self, client, mock_post):
        """Minimal valid invoice: existing customer by Id, one row, TaxAmount array."""
        mock_post.return_value = {
            "CustomerId": "cust-guid",
            "InvoiceId": "inv-guid",
            "InvoiceNo": "21200",
            "RefNo": "212001",
        }

        payload = {
            "Customer": {"Id": "cust-guid"},
            "DocDate": "20260415",
            "DueDate": "20260429",
            "InvoiceRow": [
                {
                    "Item": {
                        "Code": "SVC01",
                        "Description": "Consulting services",
                        "UOMName": "tk",
                    },
                    "Quantity": 1.0,
                    "Price": 100.00,
                    "TaxId": TAX_ID_20,
                }
            ],
            "TaxAmount": [{"TaxId": TAX_ID_20, "Amount": 20.00}],
            "TotalAmount": 120.00,
        }

        result = client.sales.send_invoice(payload)

        assert result["InvoiceId"] == "inv-guid"
        mock_post.assert_called_once_with("sendinvoice", payload)

    def test_send_invoice_new_customer_inline(self, client, mock_post):
        """Customer can be created inline by providing Name + RegNo + CountryCode."""
        mock_post.return_value = {
            "CustomerId": "new-cust-guid",
            "InvoiceId": "inv-guid-2",
            "InvoiceNo": "21201",
            "NewCustomer": True,
        }

        payload = {
            "Customer": {
                "Name": "Acme OÜ",
                "RegNo": "12345678",
                "CountryCode": "EE",
            },
            "DocDate": "20260415",
            "DueDate": "20260429",
            "InvoiceRow": [
                {
                    "Item": {"Code": "ITEM1", "Description": "Goods", "UOMName": "tk"},
                    "Quantity": 2.0,
                    "Price": 50.00,
                    "TaxId": TAX_ID_20,
                }
            ],
            "TaxAmount": [{"TaxId": TAX_ID_20, "Amount": 20.00}],
            "TotalAmount": 120.00,
        }

        result = client.sales.send_invoice(payload)

        assert result["NewCustomer"] is True
        mock_post.assert_called_once_with("sendinvoice", payload)

    def test_send_invoice_tax_amount_is_array(self, client, mock_post):
        """TaxAmount must be an array even for a single tax rate — not a scalar."""
        mock_post.return_value = {"InvoiceId": "inv-guid-3", "InvoiceNo": "21202"}

        payload = {
            "Customer": {"Id": "cust-guid"},
            "DocDate": "20260415",
            "DueDate": "20260429",
            "InvoiceRow": [
                {
                    "Item": {"Code": "X", "Description": "Item", "UOMName": "tk"},
                    "Quantity": 1.0,
                    "Price": 100.00,
                    "TaxId": TAX_ID_20,
                }
            ],
            "TaxAmount": [{"TaxId": TAX_ID_20, "Amount": 20.00}],
            "TotalAmount": 120.00,
        }

        client.sales.send_invoice(payload)

        sent = mock_post.call_args[0][1]
        assert isinstance(sent["TaxAmount"], list), "TaxAmount must be a list"
        assert sent["TaxAmount"][0]["TaxId"] == TAX_ID_20

    def test_send_credit_invoice_uses_negative_amounts(self, client, mock_post):
        """Credit invoice: same endpoint (sendinvoice) with negated quantities and amounts."""
        mock_post.return_value = {"InvoiceId": "credit-inv-guid", "InvoiceNo": "21203"}

        payload = {
            "Customer": {"Id": "cust-guid"},
            "DocDate": "20260415",
            "InvoiceRow": [
                {
                    "Item": {"Code": "SVC01", "Description": "Credit: Consulting", "UOMName": "tk"},
                    "Quantity": -1.0,
                    "Price": 100.00,
                    "TaxId": TAX_ID_20,
                }
            ],
            "TaxAmount": [{"TaxId": TAX_ID_20, "Amount": -20.00}],
            "TotalAmount": -120.00,
        }

        client.sales.send_credit_invoice(payload)

        # Both send_invoice and send_credit_invoice hit the same endpoint
        mock_post.assert_called_once_with("sendinvoice", payload)
        sent = mock_post.call_args[0][1]
        assert sent["TotalAmount"] < 0
        assert sent["TaxAmount"][0]["Amount"] < 0


class TestSendInvoiceByEmail:
    """Tests for sales.send_invoice_by_email()"""

    def test_send_invoice_by_email_basic(self, client, mock_post):
        """Test sending invoice by email with default parameters."""
        mock_post.return_value = {"Success": True, "Message": "OK"}

        result = client.sales.send_invoice_by_email("invoice-id-123")

        assert result == {"Success": True, "Message": "OK"}
        mock_post.assert_called_once_with(
            "sendinvoicebyemail",
            {"Id": "invoice-id-123", "DelivNote": False},
            version="v2",
        )

    def test_send_invoice_by_email_with_delivnote(self, client, mock_post):
        """Test sending invoice as delivery note (without prices)."""
        mock_post.return_value = {"Success": True, "Message": "OK"}

        result = client.sales.send_invoice_by_email("invoice-id-123", delivnote=True)

        assert result == {"Success": True, "Message": "OK"}
        mock_post.assert_called_once_with(
            "sendinvoicebyemail",
            {"Id": "invoice-id-123", "DelivNote": True},
            version="v2",
        )

    def test_send_invoice_by_email_error(self, client, mock_post):
        """Test error response when email sending fails."""
        mock_post.return_value = {
            "Success": False,
            "Error": "Customer has no email address",
            "ErrorCode": "NO_EMAIL",
        }

        result = client.sales.send_invoice_by_email("invoice-id-123")

        assert result["Success"] is False
        assert "email" in result["Error"].lower()


class TestSendInvoiceByEinvoice:
    """Tests for sales.send_invoice_by_einvoice()"""

    def test_send_invoice_by_einvoice_basic(self, client, mock_post):
        """Test sending invoice as e-invoice."""
        mock_post.return_value = {"Success": True, "Message": "OK"}

        result = client.sales.send_invoice_by_einvoice("invoice-id-456")

        assert result == {"Success": True, "Message": "OK"}
        mock_post.assert_called_once_with(
            "sendinvoiceaseinv",
            {"Id": "invoice-id-456", "DelivNote": False},
            version="v2",
        )

    def test_send_invoice_by_einvoice_with_delivnote(self, client, mock_post):
        """Test sending e-invoice without prices (delivery note mode)."""
        mock_post.return_value = {"Success": True, "Message": "OK"}

        client.sales.send_invoice_by_einvoice("invoice-id-456", delivnote=True)

        mock_post.assert_called_once_with(
            "sendinvoiceaseinv",
            {"Id": "invoice-id-456", "DelivNote": True},
            version="v2",
        )

    def test_send_invoice_by_einvoice_no_capability(self, client, mock_post):
        """api-noeinv means the recipient has no e-invoice operator configured."""
        mock_post.return_value = {"Message": "api-noeinv"}

        result = client.sales.send_invoice_by_einvoice("invoice-id-456")

        assert "api-noeinv" in result.get("Message", "")


class TestGetInvoicePdf:
    """Tests for sales.get_invoice_pdf()"""

    def test_get_invoice_pdf_returns_base64(self, client, mock_get_pdf):
        """Test getting invoice PDF returns base64-encoded content."""
        pdf_content = b"%PDF-1.4\ntest pdf content"
        mock_get_pdf.return_value = pdf_content

        result = client.sales.get_invoice_pdf("invoice-id-789")

        assert isinstance(result, dict)
        assert "pdf" in result
        assert isinstance(result["pdf"], str)
        decoded = base64.b64decode(result["pdf"])
        assert decoded == pdf_content
        mock_get_pdf.assert_called_once_with(
            "getsalesinvpdf",
            {"Id": "invoice-id-789"},
            version="v2",
        )

    def test_get_invoice_pdf_roundtrip(self, client, mock_get_pdf):
        """Test PDF encoding/decoding roundtrip."""
        original_pdf = b"%PDF-1.4\nThis is a test PDF document with some binary content\x00\xFF"
        mock_get_pdf.return_value = original_pdf

        result = client.sales.get_invoice_pdf("invoice-id-789")
        decoded_pdf = base64.b64decode(result["pdf"])

        assert decoded_pdf == original_pdf

    def test_get_invoice_pdf_empty(self, client, mock_get_pdf):
        """Test getting empty PDF (edge case)."""
        mock_get_pdf.return_value = b""

        result = client.sales.get_invoice_pdf("invoice-id-789")

        assert isinstance(result, dict)
        assert "pdf" in result
        assert base64.b64decode(result["pdf"]) == b""


class TestInvoiceDeliveryIntegration:
    """Integration tests for invoice delivery workflow."""

    def test_complete_invoice_delivery_workflow(self, client, mock_post, mock_get_pdf):
        """Test complete workflow: create invoice, send by email, and retrieve PDF."""
        invoice_id = "workflow-test-id"

        # Create invoice
        mock_post.return_value = {"InvoiceId": invoice_id, "InvoiceNo": "INV-001"}
        result = client.sales.send_invoice({
            "Customer": {"Id": "cust-guid"},
            "DocDate": "20260401",
            "DueDate": "20260415",
            "InvoiceRow": [
                {
                    "Item": {"Code": "SVC01", "Description": "Service", "UOMName": "tk"},
                    "Quantity": 1.0,
                    "Price": 100.00,
                    "TaxId": TAX_ID_20,
                }
            ],
            "TaxAmount": [{"TaxId": TAX_ID_20, "Amount": 20.00}],
            "TotalAmount": 120.00,
        })
        assert result["InvoiceId"] == invoice_id

        # Send by email
        mock_post.return_value = {"Success": True, "Message": "OK"}
        result = client.sales.send_invoice_by_email(invoice_id)
        assert result["Success"] is True

        # Get PDF
        pdf_data = b"%PDF-1.4\nInvoice PDF content"
        mock_get_pdf.return_value = pdf_data
        pdf_result = client.sales.get_invoice_pdf(invoice_id)
        assert "pdf" in pdf_result
        assert base64.b64decode(pdf_result["pdf"]) == pdf_data

    def test_send_both_email_and_einvoice(self, client, mock_post):
        """Test sending invoice through multiple channels."""
        invoice_id = "multi-channel-id"

        mock_post.return_value = {"Success": True, "Message": "OK"}
        email_result = client.sales.send_invoice_by_email(invoice_id)
        assert email_result["Success"] is True

        mock_post.return_value = {"Success": True, "Message": "OK"}
        einvoice_result = client.sales.send_invoice_by_einvoice(invoice_id)
        assert einvoice_result["Success"] is True

        assert mock_post.call_count == 2
