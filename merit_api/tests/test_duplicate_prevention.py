"""Unit tests for the duplicate-write guards on purchase invoices and payments."""

from unittest.mock import Mock

import pytest

from merit_api import MeritAPI, MeritAPIError


def _mock_response(status_code=200, payload=None, text=""):
    response = Mock()
    response.status_code = status_code
    response.text = text
    if payload is None:
        response.json.side_effect = ValueError("no json")
    else:
        response.json.return_value = payload
    return response


def _purchase_payload(bill_no="INV-1"):
    return {
        "Vendor": {"Id": "ven-1", "Name": "Acme OÜ"},
        "DocDate": "20260415",
        "DueDate": "20260429",
        "TransactionDate": "20260415",
        "BillNo": bill_no,
        "CurrencyCode": "EUR",
        "CurrencyRate": 1.0,
        "InvoiceRow": [
            {
                "Item": {"Code": "X", "Description": "Row", "UOMName": "tk", "TaxId": "t1"},
                "Quantity": 1.0,
                "Price": 10.0,
                "TaxId": "t1",
                "GLAccountCode": "4017",
            }
        ],
        "TaxAmount": [{"TaxId": "t1", "Amount": 0.0}],
        "TotalAmount": 10.0,
    }


def test_purchase_invoice_create_rejects_duplicate_bill_no_for_same_vendor():
    session = Mock()

    def post(url, **_):
        if "getpurchorders" in url:
            return _mock_response(payload=[{"BillId": "old-1", "BillNo": "INV-1", "VendorId": "ven-1"}])
        return _mock_response(payload={"BillId": "new-1"})

    session.post.side_effect = post
    client = MeritAPI("id", "key", session=session)

    with pytest.raises(MeritAPIError) as exc:
        client.purchases.send_invoice(_purchase_payload("INV-1"))

    assert "already exists" in str(exc.value)
    assert exc.value.response_body["BillId"] == "old-1"
    # The create endpoint must never have been called.
    assert all("sendpurchinvoice" not in c.args[0] for c in session.post.call_args_list)


def test_purchase_invoice_create_allows_duplicate_when_overridden():
    session = Mock()

    def post(url, **_):
        if "getpurchorders" in url:
            return _mock_response(payload=[{"BillId": "old-1", "BillNo": "INV-1", "VendorId": "ven-1"}])
        return _mock_response(payload={"BillId": "new-1"})

    session.post.side_effect = post
    client = MeritAPI("id", "key", session=session)

    result = client.purchases.send_invoice(_purchase_payload("INV-1"), allow_duplicate=True)

    assert result == {"BillId": "new-1"}
    assert session.post.call_args.args[0].endswith("/v1/sendpurchinvoice")


def test_purchase_invoice_create_proceeds_when_bill_no_is_new():
    session = Mock()

    def post(url, **_):
        if "getpurchorders" in url:
            return _mock_response(payload=[{"BillId": "old-1", "BillNo": "OTHER", "VendorId": "ven-1"}])
        return _mock_response(payload={"BillId": "new-1"})

    session.post.side_effect = post
    client = MeritAPI("id", "key", session=session)

    result = client.purchases.send_invoice(_purchase_payload("INV-1"))

    assert result == {"BillId": "new-1"}


def test_purchase_invoice_create_proceeds_for_same_bill_no_but_different_vendor():
    session = Mock()

    def post(url, **_):
        if "getpurchorders" in url:
            return _mock_response(payload=[{"BillId": "old-1", "BillNo": "INV-1", "VendorId": "ven-OTHER"}])
        return _mock_response(payload={"BillId": "new-1"})

    session.post.side_effect = post
    client = MeritAPI("id", "key", session=session)

    result = client.purchases.send_invoice(_purchase_payload("INV-1"))

    assert result == {"BillId": "new-1"}


def test_payment_create_rejects_duplicate_for_same_bill_and_amount():
    session = Mock()

    def post(url, **_):
        if "getpayments" in url:
            return _mock_response(payload=[{"BillNo": "S1", "Amount": 0.01}])
        return _mock_response(payload={"InvoiceId": "pay-1"})

    session.post.side_effect = post
    client = MeritAPI("id", "key", session=session)

    with pytest.raises(MeritAPIError) as exc:
        client.financial.create_payment(
            {
                "BankId": "b1",
                "VendorName": "Acme",
                "BillNo": "S1",
                "Amount": 0.01,
                "IBAN": "EE001",
                "PaymentDate": "20260417",
            }
        )

    assert "already exists" in str(exc.value)
    assert all("sendPaymentV" not in c.args[0] for c in session.post.call_args_list)


def test_payment_create_allows_duplicate_when_overridden():
    session = Mock()

    def post(url, **_):
        if "getpayments" in url:
            return _mock_response(payload=[{"BillNo": "S1", "Amount": 0.01}])
        return _mock_response(payload={"InvoiceId": "pay-1"})

    session.post.side_effect = post
    client = MeritAPI("id", "key", session=session)

    result = client.financial.create_payment(
        {
            "BankId": "b1",
            "VendorName": "Acme",
            "BillNo": "S1",
            "Amount": 0.01,
            "IBAN": "EE001",
            "PaymentDate": "20260417",
        },
        allow_duplicate=True,
    )

    assert result == {"InvoiceId": "pay-1"}
    assert session.post.call_args.args[0].endswith("/v1/sendPaymentV")


def test_payment_create_proceeds_when_amount_differs():
    session = Mock()

    def post(url, **_):
        if "getpayments" in url:
            # Same bill referenced, but a different amount — not the same payment.
            return _mock_response(payload=[{"BillNo": "S1", "Amount": 999.0}])
        return _mock_response(payload={"InvoiceId": "pay-1"})

    session.post.side_effect = post
    client = MeritAPI("id", "key", session=session)

    result = client.financial.create_payment(
        {
            "BankId": "b1",
            "VendorName": "Acme",
            "BillNo": "S1",
            "Amount": 0.01,
            "IBAN": "EE001",
            "PaymentDate": "20260417",
        }
    )

    assert result == {"InvoiceId": "pay-1"}
