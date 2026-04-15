from datetime import datetime, timedelta
from typing import Any, Dict, List
import base64


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

    def send(self, customer: Dict[str, Any]) -> Dict:
        """Create or update a customer."""
        return self._client._post("sendcustomer", customer)


class Vendors(Namespace):
    def get_list(self, **kwargs) -> List[Dict]:
        """Get vendor list. Optional filters: Name, RegNo."""
        return self._client._post("getvendors", kwargs)

    def send(self, vendor: Dict[str, Any]) -> Dict:
        """Create or update a vendor."""
        return self._client._post("sendvendor", vendor)


class Items(Namespace):
    def get_list(self, **kwargs) -> List[Dict]:
        """Get items list. Optional filters: Code, Name."""
        return self._client._post("getitems", kwargs)

    def add(self, items: List[Dict[str, Any]]) -> List[Dict]:
        """Add new items."""
        return self._client._post("additems", items)

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
        """Create a sales invoice."""
        return self._client._post("sendinvoice", invoice)

    def delete_invoice(self, id: str) -> Dict:
        """Delete an invoice."""
        return self._client._post("deleteinvoice", {"Id": id})

    def send_credit_invoice(self, credit_data: Dict[str, Any]) -> Dict:
        """Create a credit invoice."""
        return self._client._post("sendcreditinvoice", credit_data)

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

    def send_invoice_by_einvoice(self, id: str) -> Dict:
        """Send a sales invoice as a structured e-invoice.
        
        Args:
            id: Sales invoice GUID (SIHId)
        
        Returns:
            Status message or error
        """
        return self._client._post(
            "sendinvoicebyeinvoice",
            {"Id": id},
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
        pdf_bytes = self._client._get_pdf("getinvoicepdf", {"Id": id}, version="v2")
        return {"pdf": base64.b64encode(pdf_bytes).decode("utf-8")}

    def get_offers(self, **kwargs) -> List[Dict]:
        """Get list of sales offers. Required: PeriodStart, PeriodEnd, DateType, UnPaid."""
        return self._client._post("getoffers", kwargs, version="v2")

    def get_recurring_invoices(self, **kwargs) -> List[Dict]:
        """Get recurring invoices. Required: PeriodStart, PeriodEnd, DateType."""
        return self._client._post("getperinvoices", kwargs, version="v2")


class Purchases(Namespace):
    def get_invoices(self, **kwargs) -> List[Dict]:
        """Get list of purchase invoices. Required filters: PeriodStart, PeriodEnd (YYYYmmdd). Defaults to last 3 months."""
        return self._client._post("getpurchorders", self._apply_default_period(kwargs))

    def send_invoice(self, invoice: Dict[str, Any]) -> Dict:
        """Create a purchase invoice."""
        return self._client._post("sendpurchaseinvoice", invoice)


class Financial(Namespace):
    def get_payments(self, **kwargs) -> List[Dict]:
        """Get payments. PeriodStart/PeriodEnd (YYYYmmdd) default to last 3 months if omitted."""
        return self._client._post("getpayments", self._apply_default_period(kwargs))

    def create_payment(self, payment: Dict[str, Any]) -> Dict:
        """Create a payment."""
        return self._client._post("createpayment", payment)

    def get_gl_batches(self, **kwargs) -> List[Dict]:
        """Get GL transactions. PeriodStart/PeriodEnd (YYYYmmdd) default to last 3 months if omitted."""
        return self._client._post("getglbatches", self._apply_default_period(kwargs))

    def get_banks(self) -> List[Dict]:
        """Get list of banks."""
        return self._client._post("getbanks")

    def get_costs(self) -> List[Dict]:
        """Get cost centers."""
        return self._client._post("getcostcenters")

    def get_projects(self) -> List[Dict]:
        """Get projects."""
        return self._client._post("getprojects")


class Inventory(Namespace):
    def get_movements(self, **kwargs) -> List[Dict]:
        """Get inventory movements."""
        return self._client._post("getinvmovements", kwargs, version="v2")


class Assets(Namespace):
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
        return self._client._post("dimensionslist", {"AllValues": all_values}, version="v2")

    def add(self, dimensions: List[Dict[str, Any]]) -> List[Dict]:
        """Add dimensions."""
        return self._client._post("adddimensions", dimensions, version="v2")
