"""
Tests for Priority 1 (Critical Sales) invoice delivery methods.

Tests include:
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


class TestSendInvoiceByEmail:
    """Tests for sales.send_invoice_by_email()"""

    def test_send_invoice_by_email_basic(self, client, mock_post):
        """Test sending invoice by email with default parameters."""
        mock_post.return_value = {"Success": True, "Message": "Email sent successfully"}

        result = client.sales.send_invoice_by_email("invoice-id-123")

        assert result == {"Success": True, "Message": "Email sent successfully"}
        mock_post.assert_called_once_with(
            "sendinvoicebyemail",
            {"Id": "invoice-id-123", "DelivNote": False},
            version="v2",
        )

    def test_send_invoice_by_email_with_delivnote(self, client, mock_post):
        """Test sending invoice as delivery note (without prices)."""
        mock_post.return_value = {"Success": True, "Message": "Delivery note sent"}

        result = client.sales.send_invoice_by_email("invoice-id-123", delivnote=True)

        assert result == {"Success": True, "Message": "Delivery note sent"}
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
        mock_post.return_value = {"Success": True, "Message": "E-invoice sent successfully"}

        result = client.sales.send_invoice_by_einvoice("invoice-id-456")

        assert result == {"Success": True, "Message": "E-invoice sent successfully"}
        mock_post.assert_called_once_with(
            "sendinvoicebyeinvoice",
            {"Id": "invoice-id-456"},
            version="v2",
        )

    def test_send_invoice_by_einvoice_error(self, client, mock_post):
        """Test error response when e-invoice sending fails."""
        mock_post.return_value = {
            "Success": False,
            "Error": "Invalid e-invoice details",
            "ErrorCode": "INVALID_EINVOICE",
        }

        result = client.sales.send_invoice_by_einvoice("invoice-id-456")

        assert result["Success"] is False
        assert "Invalid" in result["Error"]


class TestGetInvoicePdf:
    """Tests for sales.get_invoice_pdf()"""

    def test_get_invoice_pdf_returns_base64(self, client, mock_get_pdf):
        """Test getting invoice PDF returns base64-encoded content."""
        # Create a small PDF-like binary content for testing
        pdf_content = b"%PDF-1.4\ntest pdf content"
        mock_get_pdf.return_value = pdf_content

        result = client.sales.get_invoice_pdf("invoice-id-789")

        assert isinstance(result, dict)
        assert "pdf" in result
        assert isinstance(result["pdf"], str)

        # Verify it's valid base64
        decoded = base64.b64decode(result["pdf"])
        assert decoded == pdf_content

        mock_get_pdf.assert_called_once_with(
            "getinvoicepdf",
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
        # Empty bytes should encode to empty string
        assert base64.b64decode(result["pdf"]) == b""


class TestInvoiceDeliveryIntegration:
    """Integration tests for invoice delivery workflow."""

    def test_complete_invoice_delivery_workflow(self, client, mock_post, mock_get_pdf):
        """Test complete workflow: create invoice, send by email, and retrieve PDF."""
        invoice_id = "workflow-test-id"

        # Mock get_invoices to verify we can find the invoice
        mock_post.return_value = [{"SIHId": invoice_id, "InvoiceNo": "INV-001"}]
        invoices = client.sales.get_invoices(PeriodStart="20260401", PeriodEnd="20260411")
        assert len(invoices) > 0

        # Mock send_invoice_by_email
        mock_post.return_value = {"Success": True, "Message": "Email sent"}
        result = client.sales.send_invoice_by_email(invoice_id)
        assert result["Success"] is True

        # Mock get_invoice_pdf
        pdf_data = b"%PDF-1.4\nInvoice PDF content"
        mock_get_pdf.return_value = pdf_data
        pdf_result = client.sales.get_invoice_pdf(invoice_id)
        assert "pdf" in pdf_result
        assert base64.b64decode(pdf_result["pdf"]) == pdf_data

    def test_send_both_email_and_einvoice(self, client, mock_post):
        """Test sending invoice through multiple channels."""
        invoice_id = "multi-channel-id"

        # Send by email
        mock_post.return_value = {"Success": True, "Message": "Email sent"}
        email_result = client.sales.send_invoice_by_email(invoice_id)
        assert email_result["Success"] is True

        # Send as e-invoice
        mock_post.return_value = {"Success": True, "Message": "E-invoice sent"}
        einvoice_result = client.sales.send_invoice_by_einvoice(invoice_id)
        assert einvoice_result["Success"] is True

        # Both should succeed independently
        assert mock_post.call_count == 2
