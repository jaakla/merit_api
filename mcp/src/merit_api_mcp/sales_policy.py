"""Restricted MCP sales-invoice profile; the general-purpose SDK is unchanged.

Confirmation creates a real, unsent accounting invoice, NOT an unposted draft.
Merit documents embedded payments and item creation on sendinvoice, so a tool
name allowlist alone is insufficient. Reject unknown fields at every level.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
from uuid import UUID

INVOICE_EFFECT = (
    "Confirmation creates a real, unsent accounting invoice in Merit. It can affect "
    "the ledger and reports before delivery; this is NOT an unposted draft. "
    "Only the preview is non-writing. Review before confirming; send manually in Merit."
)

_TOP = {
    "Customer", "DocDate", "TransactionDate", "DueDate", "InvoiceNo",
    "CurrencyCode", "PriceInclVat", "InvoiceRow", "TaxAmount", "TotalAmount",
    "FComment", "HComment",
}
_ROW = {"Item", "Quantity", "Price", "TaxId", "Account"}
_ITEM = {"Code", "Description", "UOMName"}
_CENT = Decimal("0.01")
_MAX = Decimal("999999999999.99")


def sales_invoice_errors(payload: Any) -> tuple[str, ...]:
    errors: list[str] = []

    def obj(value: Any, allowed: set[str], required: set[str], path: str) -> bool:
        if not isinstance(value, dict):
            errors.append(f"{path} must be an object.")
            return False
        for key in value:
            if key not in allowed:
                errors.append(f"{path}.{key} is not allowed in the restricted invoice profile.")
        for key in sorted(required - value.keys()):
            errors.append(f"{path}.{key} is required.")
        return True

    def text(value: Any, path: str, limit: int) -> None:
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            errors.append(f"{path} must be a non-empty string of at most {limit} characters.")

    def guid(value: Any, path: str) -> None:
        try:
            if not isinstance(value, str) or str(UUID(value)) != value.lower():
                raise ValueError()
        except (ValueError, AttributeError):
            errors.append(f"{path} must be a TaxId GUID or customer GUID in canonical UUID format.")

    def amount(value: Any, path: str, places: int, positive: bool = False) -> Decimal | None:
        try:
            # No booleans, numeric strings, NaN, Infinity, or nested objects.
            if type(value) not in (int, float):
                raise ValueError()
            n = Decimal(str(value))
            if not n.is_finite() or n < 0 or n > _MAX or (positive and n == 0):
                raise ValueError()
            if n != n.quantize(Decimal(1).scaleb(-places)):
                raise ValueError()
            return n
        except (InvalidOperation, ValueError):
            sign = "positive" if positive else "non-negative"
            errors.append(f"{path} must be a finite {sign} JSON number with at most {places} decimal places.")
            return None

    if not obj(payload, _TOP, _TOP - {"FComment", "HComment"}, "payload"):
        return tuple(errors)
    if "InvoiceRows" in payload:
        errors.append("Use InvoiceRow (singular), not InvoiceRows.")
    customer = payload.get("Customer")
    if obj(customer, {"Id"}, {"Id"}, "Customer"):
        guid(customer.get("Id"), "Customer.Id")
    for field in ("DocDate", "TransactionDate", "DueDate"):
        value = payload.get(field)
        try:
            if not isinstance(value, str) or len(value) != 8 or not value.isascii() or not value.isdigit():
                raise ValueError()
            datetime.strptime(value, "%Y%m%d")
        except ValueError:
            errors.append(f"{field} must be a valid calendar date in YYYYMMDD format.")
    text(payload.get("InvoiceNo"), "InvoiceNo", 35)
    # Keep the preparation profile small: no FX, gross-price conversion, discounts,
    # rounding adjustments, or alternative accounting document types.
    if payload.get("CurrencyCode") != "EUR":
        errors.append("CurrencyCode must be EUR in the restricted invoice profile.")
    if payload.get("PriceInclVat") is not False:
        errors.append("PriceInclVat must be false; use VAT-exclusive prices.")
    for field in ("FComment", "HComment"):
        if field in payload:
            text(payload[field], field, 4096)

    rows = payload.get("InvoiceRow")
    row_total = Decimal(0)
    tax_ids: set[str] = set()
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        errors.append("InvoiceRow must be a non-empty list of at most 100 rows.")
    else:
        for index, row in enumerate(rows):
            path = f"InvoiceRow[{index}]"
            if not obj(row, _ROW, _ROW, path):
                continue
            item = row.get("Item")
            if obj(item, _ITEM, _ITEM, path + ".Item"):
                for key, limit in (("Code", 20), ("Description", 150), ("UOMName", 64)):
                    text(item.get(key), path + ".Item." + key, limit)
            quantity = amount(row.get("Quantity"), path + ".Quantity", 3, positive=True)
            price = amount(row.get("Price"), path + ".Price", 7)
            guid(row.get("TaxId"), path + ".TaxId")
            if isinstance(row.get("TaxId"), str):
                tax_ids.add(row["TaxId"].lower())
            text(row.get("Account"), path + ".Account", 10)
            if quantity is not None and price is not None:
                row_total += (quantity * price).quantize(_CENT, rounding=ROUND_HALF_UP)
    total = amount(payload.get("TotalAmount"), "TotalAmount", 2, positive=True)
    if total is not None and total != row_total:
        errors.append("TotalAmount must equal the sum of VAT-exclusive Quantity × Price, rounded per row to cents.")

    taxes = payload.get("TaxAmount")
    seen: set[str] = set()
    if not isinstance(taxes, list) or not 1 <= len(taxes) <= 100:
        errors.append("TaxAmount must be a non-empty list of at most 100 tax entries, including zero VAT.")
    else:
        for index, tax in enumerate(taxes):
            path = f"TaxAmount[{index}]"
            if not obj(tax, {"TaxId", "Amount"}, {"TaxId", "Amount"}, path):
                continue
            guid(tax.get("TaxId"), path + ".TaxId")
            amount(tax.get("Amount"), path + ".Amount", 2)
            if isinstance(tax.get("TaxId"), str):
                key = tax["TaxId"].lower()
                if key in seen:
                    errors.append("TaxAmount must contain each TaxId only once.")
                seen.add(key)
        if seen != tax_ids:
            errors.append("TaxAmount TaxIds must exactly match the invoice row TaxIds.")
    return tuple(errors)


def create_unsent_invoice(client: Any, args: dict[str, Any]) -> Any:
    """Check existing items at execution time, then invoke only sendinvoice.

    getitems has broad matching and can return one object or an array. Require
    one exact code match and a known non-stock type. Missing/ambiguous/malformed
    results fail closed. Type (needed for item creation) is never sent.
    """
    payload = args["payload"]
    errors = sales_invoice_errors(payload)
    if errors:
        raise ValueError(" ".join(errors))
    for code in sorted({row["Item"]["Code"] for row in payload["InvoiceRow"]}):
        result = client.items.get_list(Code=code)
        records = [result] if isinstance(result, dict) else result
        if not isinstance(records, list):
            raise ValueError(f"Cannot verify existing item {code!r}; no invoice was created.")
        matches = [r for r in records if isinstance(r, dict) and r.get("Code") == code]
        if len(matches) != 1:
            raise ValueError(f"Item {code!r} must match exactly one existing Merit item. Create/manage items manually.")
        record = matches[0]
        kind = record.get("Type0", record.get("Type"))
        if type(kind) is not int or kind not in (2, 3):
            raise ValueError(f"Item {code!r} must have a verified non-stock type (2 or 3); stock/unknown items are not allowed.")
    return client.sales.send_invoice(payload)
