from datetime import datetime, timedelta
from typing import Any, Dict, List
import base64


def _to_yyyymmdd(date_str: str) -> str:
    """Normalize Merit date strings to YYYYMMDD for API fields like PaymentDate.

    Merit invoice lists return DueDate as ISO 8601 (2026-05-02T00:00:00),
    but sendPaymentV expects YYYYMMDD (20260502).
    Already-correct 8-char strings are returned unchanged.
    """
    if len(date_str) == 8 and date_str.isdigit():
        return date_str
    return datetime.fromisoformat(date_str).strftime("%Y%m%d")


class Namespace:
    """Base class for API namespaces."""

    def __init__(self, client):
        self._client = client

    def _apply_default_period(self, kwargs: dict) -> dict:
        if "PeriodStart" not in kwargs or "PeriodEnd" not in kwargs:
            today = datetime.now()
            kwargs.setdefault("PeriodEnd", today.strftime("%Y%m%d"))
            kwargs.setdefault("PeriodStart", (today - timedelta(days=90)).strftime("%Y%m%d"))
        return kwargs


class Customers(Namespace):
    def get_list(self, **kwargs) -> List[Dict]:
        """Get customer list. Optional filters: Name, RegNo."""
        return self._client._post("getcustomers", kwargs)

    def get_groups(self, **kwargs) -> List[Dict]:
        """Get customer groups."""
        return self._client._post("getcustomergroups", kwargs, version="v2")

    def send(self, customer: Dict[str, Any]) -> Dict:
        """Create or update a customer."""
        return self._client._post("sendcustomer", customer)


class Vendors(Namespace):
    def get_list(self, **kwargs) -> List[Dict]:
        """Get vendor list. Optional filters: Name, RegNo."""
        return self._client._post("getvendors", kwargs)

    def get_groups(self, **kwargs) -> List[Dict]:
        """Get vendor groups."""
        return self._client._post("getvendorgroups", kwargs, version="v2")

    def send(self, vendor: Dict[str, Any]) -> Dict:
        """Create or update a vendor."""
        return self._client._post("sendvendor", vendor)

    def update(self, vendor: Dict[str, Any]) -> Dict:
        """Update an existing vendor. Only Id is required; all other fields are optional.

        Use this to keep vendor records current when new invoices arrive — especially
        to sync BankAccount (IBAN) and SWIFT_BIC so future payments can be made without
        manual IBAN lookup.

        v2 fields: Id (guid, required), Name, CountryCode, Address, City, PostalCode,
        PhoneNo, PhoneNo2, Email, RegNo, VatRegNo, SalesInvLang, VatAccountable,
        BankAccount, ReferenceNo, VendGrCode, VendGrId, PayerReceiverName,
        Dimensions ([{DimId, DimValueId, DimCode}]).
        """
        return self._client._post("updatevendor", vendor, version="v2")


class Items(Namespace):
    def get_list(self, **kwargs) -> List[Dict]:
        """Get items list. Optional filters: Code, Name."""
        return self._client._post("getitems", kwargs)

    def get_groups(self, **kwargs) -> List[Dict]:
        """Get item groups."""
        return self._client._post("getitemgroups", kwargs, version="v2")

    def add(self, items: List[Dict[str, Any]]) -> List[Dict]:
        """Add new items."""
        return self._client._post("senditems", items, version="v2")

    def update(self, item: Dict[str, Any]) -> Dict:
        """Update an item."""
        return self._client._post("updateitem", item)


class Sales(Namespace):
    def get_invoices(self, **kwargs) -> List[Dict]:
        """Get list of invoices. PeriodStart/PeriodEnd (YYYYmmdd) default to last 3 months if omitted."""
        return self._client._post("getinvoices", self._apply_default_period(kwargs), version="v2")

    def get_invoice(self, id: str, add_attachment: bool = False) -> Dict:
        """Get single invoice details."""
        return self._client._post("getinvoice", {"Id": id, "AddAttachment": add_attachment})

    def send_invoice(self, invoice: Dict[str, Any]) -> Dict:
        """Create a sales invoice.

        Tricky requirements:
        - Customer: ``{"Id": guid}`` for an existing customer, or provide Name + RegNo + CountryCode
          to create a new one on the fly.
        - InvoiceRow.Item: required nested object — Description and UOMName live here.
        - InvoiceRow.TaxId: required on every row (use ``taxes.get_list()`` to find valid IDs).
        - TaxAmount: required array of ``{TaxId, Amount}`` — one entry per distinct tax rate.
        - Dates (DocDate, DueDate): YYYYmmdd strings.
        - InvoiceNo: optional — Merit auto-assigns the next number if omitted.

        Minimal working example (20 % VAT)::

            result = client.sales.send_invoice({
                "Customer": {"Id": "<customer-guid>"},
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
                        "TaxId": "<tax-guid>",
                    }
                ],
                "TaxAmount": [{"TaxId": "<tax-guid>", "Amount": 20.00}],
                "TotalAmount": 120.00,
            })
            # Returns: {"CustomerId": "...", "InvoiceId": "...", "InvoiceNo": "...", "RefNo": "..."}
        """
        return self._client._post("sendinvoice", invoice)

    def delete_invoice(self, id: str) -> Dict:
        """Delete an invoice."""
        return self._client._post("deleteinvoice", {"Id": id})

    def send_credit_invoice(self, credit_data: Dict[str, Any]) -> Dict:
        """Create a credit invoice.

        Uses the same ``sendinvoice`` endpoint with negative Quantity / Price / TotalAmount.
        Provide the original invoice's customer and rows with negated quantities/prices.

        Example::

            result = client.sales.send_credit_invoice({
                "Customer": {"Id": "<customer-guid>"},
                "DocDate": "20260415",
                "InvoiceRow": [
                    {
                        "Item": {"Code": "SVC01", "Description": "Credit: Consulting", "UOMName": "tk"},
                        "Quantity": -1.0,
                        "Price": 100.00,
                        "TaxId": "<tax-guid>",
                    }
                ],
                "TaxAmount": [{"TaxId": "<tax-guid>", "Amount": -20.00}],
                "TotalAmount": -120.00,
            })
        """
        return self._client._post("sendinvoice", credit_data)

    def send_invoice_by_email(self, id: str, delivnote: bool = False) -> Dict:
        """Send a sales invoice by email to the customer.
        
        Args:
            id: Sales invoice GUID (SIHId)
            delivnote: If True, send invoice without prices (delivery note mode)
        
        Returns:
            Status message or error from mail server
        """
        return self._client._post(
            "sendinvoicebyemail",
            {"Id": id, "DelivNote": delivnote},
            version="v2"
        )

    def send_invoice_by_einvoice(self, id: str, delivnote: bool = False) -> Dict:
        """Send a sales invoice as a structured e-invoice.

        Args:
            id: Sales invoice GUID (SIHId)
            delivnote: If True, send invoice without prices (delivery note mode)

        Returns:
            "OK" on success, or "api-noeinv" if recipient lacks e-invoice capability
        """
        return self._client._post(
            "sendinvoiceaseinv",
            {"Id": id, "DelivNote": delivnote},
            version="v2"
        )

    def get_invoice_pdf(self, id: str) -> Dict[str, Any]:
        """Get a sales invoice as a PDF document (returned as base64-encoded data).
        
        Args:
            id: Sales invoice GUID (SIHId)
        
        Returns:
            Dict with 'pdf' containing base64-encoded PDF content that can be decoded:
            
            ```python
            result = client.sales.get_invoice_pdf(invoice_id)
            pdf_bytes = base64.b64decode(result['pdf'])
            with open('invoice.pdf', 'wb') as f:
                f.write(pdf_bytes)
            ```
        """
        pdf_bytes = self._client._get_pdf("getsalesinvpdf", {"Id": id}, version="v2")
        return {"pdf": base64.b64encode(pdf_bytes).decode("utf-8")}

    def get_offers(self, **kwargs) -> List[Dict]:
        """Get list of sales offers. Required: PeriodStart, PeriodEnd, DateType, UnPaid."""
        return self._client._post("getoffers", kwargs, version="v2")

    def get_offer(self, id: str) -> Dict:
        """Get sales offer details."""
        return self._client._post("getoffer", {"Id": id}, version="v2")

    def get_recurring_invoices(self, **kwargs) -> List[Dict]:
        """Get recurring invoices. Required: PeriodStart, PeriodEnd, DateType."""
        return self._client._post("getperinvoices", kwargs, version="v2")

    def get_recurring_invoice(self, id: str) -> Dict:
        """Get recurring invoice details."""
        return self._client._post("getperinvoice", {"Id": id}, version="v2")

    def get_recurring_invoice_addresses(self, **kwargs) -> List[Dict]:
        """Get recurring invoice client shipping addresses."""
        return self._client._post("getpershaddress", kwargs, version="v2")


class Purchases(Namespace):
    def get_invoices(self, **kwargs) -> List[Dict]:
        """Get list of purchase invoices. Required filters: PeriodStart, PeriodEnd (YYYYmmdd). Defaults to last 3 months."""
        return self._client._post("getpurchorders", self._apply_default_period(kwargs))

    def get_invoice(self, id: str, skip_attachment: bool = True) -> Dict:
        """Get purchase invoice details."""
        return self._client._post("getpurchorder", {"Id": id, "SkipAttachment": skip_attachment})

    def get_orders(self, **kwargs) -> List[Dict]:
        """Get purchase orders waiting approval."""
        return self._client._post("GetPOrders", kwargs, version="v2")

    def send_invoice(self, invoice: Dict[str, Any]) -> Dict:
        """Create a purchase invoice.

        Tricky requirements:
        - Vendor: must include both ``Id`` AND ``Name`` even for an existing vendor.
        - InvoiceRow.Item: required nested object — Description lives here, not on the row.
        - InvoiceRow.TaxId: required on the row (use ``taxes.get_list()`` to find valid IDs).
        - TaxAmount: required array of ``{TaxId, Amount}`` — one entry per distinct tax rate.
        - Dates (DocDate, DueDate, TransactionDate): YYYYmmdd strings.
        - Attachment (optional): ``{FileName: str, FileContent: base64-encoded PDF}``.

        Minimal working example (0 % VAT, with PDF attachment)::

            result = client.purchases.send_invoice({
                "Vendor": {"Id": "<vendor-guid>", "Name": "Vendor Name OÜ"},
                "DocDate": "20260415",
                "DueDate": "20260429",
                "TransactionDate": "20260415",
                "BillNo": "INV-2026-001",
                "CurrencyCode": "EUR",
                "CurrencyRate": 1.0,
                "InvoiceRow": [
                    {
                        "Item": {
                            "Code": "SVC01",
                            "Description": "Consulting services",
                            "UOMName": "tk",
                            "TaxId": "<tax-guid>",
                        },
                        "Quantity": 1.0,
                        "Price": 100.00,
                        "TaxId": "<tax-guid>",
                        "GLAccountCode": "4017",
                    }
                ],
                "TaxAmount": [{"TaxId": "<tax-guid>", "Amount": 0.0}],
                "TotalAmount": 100.00,
                "RoundingAmount": 0.0,
                "Attachment": {
                    "FileName": "invoice.pdf",
                    "FileContent": "<base64-encoded PDF>",
                },
            })
            # Returns: {"VendorId": "...", "BillId": "...", "BillNo": "...", "BatchInfo": "..."}
        """
        return self._client._post("sendpurchinvoice", invoice)


class Financial(Namespace):
    def get_payments(self, **kwargs) -> List[Dict]:
        """Get payments. PeriodStart/PeriodEnd (YYYYmmdd) default to last 3 months if omitted."""
        return self._client._post("getpayments", self._apply_default_period(kwargs))

    def get_payment_types(self, **kwargs) -> List[Dict]:
        """Get payment types."""
        return self._client._post("getpaymenttypes", kwargs, version="v2")

    def get_payment_imports(self, **kwargs) -> List[Dict]:
        """Get payment imports."""
        return self._client._get("PaymentImports", kwargs, version="v2")

    def get_expense_payments(self, bank_id: str, **kwargs) -> List[Dict]:
        """Get expense payments for a bank."""
        return self._client._get(f"Banks/{bank_id}/ExpensePayments", kwargs, version="v2")

    def get_income_payments(self, bank_id: str, **kwargs) -> List[Dict]:
        """Get income payments for a bank."""
        return self._client._get(f"Banks/{bank_id}/IncomePayments", kwargs, version="v2")

    def create_payment(self, payment: Dict[str, Any]) -> Dict:
        """Create a payment for a purchase invoice (sendPaymentV).

        Auto-resolves missing fields before sending:
        - IBAN: looked up from the vendor's BankAccount by VendorName.
        - PaymentDate: looked up from the invoice's DueDate by BillNo.

        Raises ValueError if either field cannot be resolved, preventing a silent
        internal payment without bank transfer details.

        Returns the raw Merit API response (all fields as-is).
        """
        if not payment.get("IBAN"):
            vendor_name = payment.get("VendorName", "")
            if vendor_name:
                vendors = self._client.vendors.get_list(Name=vendor_name)
                vendor = next((v for v in vendors if v.get("Name") == vendor_name), None)
                if vendor and vendor.get("BankAccount"):
                    payment = {**payment, "IBAN": vendor["BankAccount"]}

        if not payment.get("IBAN"):
            vendor_name = payment.get("VendorName", "unknown")
            raise ValueError(
                f"IBAN is missing for vendor '{vendor_name}'. "
                "Add IBAN to the payload or update the vendor's bank account in Merit."
            )

        if not payment.get("PaymentDate"):
            bill_no = payment.get("BillNo", "")
            if bill_no:
                today = datetime.now()
                invoices = self._client.purchases.get_invoices(
                    PeriodStart=(today - timedelta(days=365)).strftime("%Y%m%d"),
                    PeriodEnd=(today + timedelta(days=730)).strftime("%Y%m%d"),
                )
                invoice = next((i for i in invoices if i.get("BillNo") == bill_no), None)
                if invoice and invoice.get("DueDate"):
                    payment = {**payment, "PaymentDate": _to_yyyymmdd(invoice["DueDate"])}

        if not payment.get("PaymentDate"):
            bill_no = payment.get("BillNo", "unknown")
            raise ValueError(
                f"PaymentDate is missing for invoice '{bill_no}' and could not be resolved "
                "from the invoice's DueDate. Provide PaymentDate explicitly (YYYYMMDD)."
            )

        version = "v2" if payment.get("CurrencyCode") else "v1"
        return self._client._post("sendPaymentV", payment, version=version)

    def get_gl_batches(self, **kwargs) -> List[Dict]:
        """Get GL transactions. PeriodStart/PeriodEnd (YYYYmmdd) default to last 3 months if omitted."""
        return self._client._post("getglbatches", self._apply_default_period(kwargs))

    def get_gl_batch(self, id: str) -> Dict:
        """Get GL transaction details."""
        return self._client._post("getglbatch", {"Id": id})

    def get_gl_batches_full(self, **kwargs) -> List[Dict]:
        """Get GL transactions with full details."""
        return self._client._post("GetGLBatchesFull", self._apply_default_period(kwargs))

    def get_banks(self) -> List[Dict]:
        """Get list of banks."""
        return self._client._post("getbanks")

    def get_accounts(self, **kwargs) -> List[Dict]:
        """Get chart of accounts."""
        return self._client._post("getaccounts", kwargs)

    def get_costs(self) -> List[Dict]:
        """Get cost centers."""
        return self._client._post("getcostcenters")

    def get_projects(self) -> List[Dict]:
        """Get projects."""
        return self._client._post("getprojects")

    def get_departments(self, **kwargs) -> List[Dict]:
        """Get departments."""
        return self._client._post("getdepartments", kwargs)

    def get_financial_years(self, **kwargs) -> Dict:
        """Get financial years."""
        return self._client._post("getaccperiods", kwargs, version="v2")


class Inventory(Namespace):
    def get_locations(self, **kwargs) -> List[Dict]:
        """Get inventory locations."""
        return self._client._post("getlocations", kwargs, version="v2")

    def get_movements(self, **kwargs) -> List[Dict]:
        """Get inventory movements."""
        return self._client._post("getinvmovements", kwargs, version="v2")


class Assets(Namespace):
    def get_locations(self, **kwargs) -> List[Dict]:
        """Get fixed asset locations."""
        return self._client._post("getfalocations", kwargs, version="v2")

    def get_responsible_persons(self, **kwargs) -> List[Dict]:
        """Get fixed asset responsible persons."""
        return self._client._post("getfaresppersons", kwargs, version="v2")

    def get_fixed_assets(self, **kwargs) -> List[Dict]:
        """Get fixed assets."""
        return self._client._post("getfixassets", kwargs, version="v2")


class Taxes(Namespace):
    def get_list(self) -> List[Dict]:
        """Get tax rates list."""
        return self._client._post("gettaxes")

    def send(self, tax: Dict[str, Any]) -> Dict:
        """Create or update a tax rate."""
        return self._client._post("sendtax", tax, version="v2")


class Dimensions(Namespace):
    def get_list(self, all_values: bool = False) -> List[Dict]:
        """Get dimensions list. all_values=True includes expired dimension values."""
        return self._client._post("getdimensions", {"AllValues": all_values}, version="v2")

    def add(self, dimensions: List[Dict[str, Any]]) -> List[Dict]:
        """Add dimensions."""
        return self._client._post("senddimensions", dimensions, version="v2")


class Pricing(Namespace):
    def get_prices(self, **kwargs) -> List[Dict]:
        """Get sales prices."""
        return self._client._post("getprices", kwargs, version="v2")

    def get_discounts(self, **kwargs) -> List[Dict]:
        """Get sales discounts."""
        return self._client._post("getdiscounts", kwargs, version="v2")

    def get_price(self, **kwargs) -> Dict:
        """Get a single effective sales price."""
        return self._client._post("getprice", kwargs, version="v2")


class Reports(Namespace):
    def get_customer_debts(self, **kwargs) -> List[Dict]:
        """Get customer debts report."""
        return self._client._post("getcustdebtrep", kwargs)

    def get_customer_payments(self, **kwargs) -> Dict:
        """Get customer payment report."""
        return self._client._post("getcustpaymrep", kwargs, version="v2")

    def get_more_data(self, **kwargs) -> Dict:
        """Get next page / additional report data for paged report APIs."""
        return self._client._post("getmoredata", kwargs, version="v2")

    def get_profit(self, **kwargs) -> Dict:
        """Get statement of profit or loss."""
        return self._client._post("getprofitrep", kwargs)

    def get_balance(self, **kwargs) -> Dict:
        """Get statement of financial position."""
        return self._client._post("getbalancerep", kwargs)

    def get_inventory(self, **kwargs) -> List[Dict]:
        """Get inventory report."""
        return self._client._post("getinventoryreport", kwargs, version="v2")

    def get_sales(self, **kwargs) -> List[Dict]:
        """Get sales report."""
        return self._client._post("getsalesrep", kwargs, version="v2")

    def get_purchases(self, **kwargs) -> List[Dict]:
        """Get purchase report."""
        return self._client._post("getpurchrep", kwargs, version="v2")


class ReferenceData(Namespace):
    def get_units(self, **kwargs) -> List[Dict]:
        """Get units of measure."""
        return self._client._post("getunits", kwargs)
