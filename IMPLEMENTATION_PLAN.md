# Merit API Python Client — Full Implementation Plan

## Objective
Bring this repository from a partial Merit Aktiva wrapper to a complete, production-ready Python SDK that covers the full method surface documented in the Merit Aktiva reference manual (`https://api.merit.ee/connecting-robots/reference-manual/`).

---

## 1) Current State Review

### What exists today
The client currently exposes a small subset of Merit methods via namespace classes (`Customers`, `Vendors`, `Items`, `Sales`, `Purchases`, `Financial`, `Inventory`, `Assets`, `Taxes`, `Dimensions`) over a shared `_post()` transport and HMAC authentication implementation.

### Main gaps observed
1. **Coverage gap**: many documented API method groups are missing (reports, payment subflows, departments, units of measure, sales prices/discounts, accounts, financial years, customer/vendor groups, etc.).
2. **Naming inconsistency**: some methods are convenience names (`send`, `get_list`) and do not always map one-to-one with reference-manual operation names.
3. **Response handling**: no unified response/error model beyond HTTP status and raw JSON return.
4. **Validation/modeling**: no typed request/response models or schema validation for complex payloads.
5. **Pagination/rate-limit/retry support**: no explicit handling for throttling and transient failures.
6. **Test strategy**: tests are script-like integration checks rather than deterministic unit tests with mocked HTTP transport.
7. **Packaging/docs**: no API surface documentation that enumerates supported endpoints and versioning guarantees.

---

## 2) Complete Method Coverage Target (Reference Manual Aligned)

Below is the implementation target grouped by the same domains used in the reference manual.

### Already implemented (keep + harden)
- Sales Invoices: list, details, delete, create, credit invoice.
- Sales Offers: list only (partial).
- Recurring Invoices: list only (partial).
- Purchase Invoices: list + create (partial).
- Inventory Movements: list only (partial).
- Payments: list + create payment (partial generic coverage).
- General Ledger Transactions: list (partial).
- Fixed Assets: list fixed assets (partial).
- Tax: get/send.
- Customers: list + send.
- Vendors: list + send.
- Cost centers, projects, banks.
- Dimensions: list + add (partial).
- Items: list + add + update (partial).

### Missing or partial — implement fully

#### A) Sales Invoices
- Ensure full support for all documented variants/examples:
  - create with payment,
  - create with multiple payments,
  - e-invoice payload variants,
  - e-mail sending flags/options,
  - PDF retrieval helper.

#### B) Sales Offers
- Create Sales Offer.
- Set Offer status.
- Create Invoice from Sales Offer.
- Get sales offer details.
- Update sales offer.

#### C) Recurring Invoices
- Create Recurring Invoice.
- Get recurring invoice clients address list.
- Send indication values.
- Get recurring invoice details.

#### D) Purchase Invoices
- Get purchase invoice details.
- Delete purchase invoice.
- Create purchase invoice waiting approval.
- Create purchase invoice waiting approval (e-invoice 1.2 variant).
- Get purchase orders list.

#### E) Inventory Movements
- Get locations list.
- Send inventory movements.

#### F) Payments
- List payment types.
- Create payment for sales invoice.
- Create payment for purchase invoice.
- Create payment for sales offer.
- Delete payment.
- Bank statement import.
- Send settlement.
- Get payment imports.
- Expense payments: list/send.
- Income payments: list/send.
- Send prepayments.

#### G) General Ledger Transactions
- Create GL transactions.
- Get GL transaction details.
- Get GL transactions full details.

#### H) Fixed Assets
- Fixed asset locations list.
- Responsible employees list.
- Send fixed assets.

#### I) Customers/Vendors extended
- Customer groups: create/list.
- Vendor groups: create/list.
- Explicit create/update convenience wrappers (even if same backend method).

#### J) Core master data
- Accounts list.
- Departments list.
- Units of Measure list + send.
- Financial years.

#### K) Dimensions extended
- Add dimension values.

#### L) Sales prices and discounts
- Send prices.
- Send discounts.
- Get prices.
- Get discounts.
- Get single price.

#### M) Items extended
- Item groups list.
- Add item groups.

#### N) Reports
- Customer debts report.
- Customer payment report.
- Statement of Profit or Loss.
- Statement of Financial Position.
- Inventory report.
- Sales report.
- Purchase report.

---

## 3) Proposed SDK Structure

Refactor from a single large module into a package:

```
merit_api/
  __init__.py
  client.py               # MeritAPI main entry, auth, transport
  exceptions.py           # typed exception hierarchy
  transport.py            # requests session, retry, timeout, logging hooks
  models/                 # optional pydantic/dataclass models
  namespaces/
    sales.py
    sales_offers.py
    recurring_invoices.py
    purchases.py
    inventory.py
    payments.py
    gl.py
    assets.py
    customers.py
    vendors.py
    items.py
    prices.py
    reports.py
    master_data.py        # banks, accounts, departments, FY, UOM, etc.
```

If backward compatibility is required, keep `merit_api.py` as a facade re-exporting the new classes.

---

## 4) Implementation Phases

### Phase 0 — Foundation Hardening
1. Add configurable timeout, retry policy, and optional idempotency helpers.
2. Add centralized API error parsing (HTTP + API-level error payloads).
3. Standardize JSON serialization (stable key ordering for signature-sensitive scenarios if needed).
4. Add request/response logging hooks (redacted secrets).

### Phase 1 — Complete Read Operations
Implement all list/get/detail operations first (low risk):
- sales offers details/list,
- recurring details/list/addresses,
- purchase details/orders,
- inventory locations/movements list,
- payment types/imports/expense/income lists,
- GL details/full details,
- fixed asset locations/responsible employees,
- customer/vendor groups list,
- accounts/departments/financial years/UOM list,
- reports retrieval methods.

### Phase 2 — Complete Write Operations
Implement all create/update/delete/send operations:
- offers create/update/status/invoice-from-offer,
- recurring create/indication,
- purchase delete/waiting-approval variants,
- inventory send,
- payments create/delete/import/settlement/expense/income/prepayment,
- GL create,
- fixed asset send,
- customer/vendor group create,
- dimensions values add,
- prices/discounts send,
- item groups add, UOM send.

### Phase 3 — DX and Contract Quality
1. Add typed payload builders for high-complexity endpoints (invoice/payment/report filters).
2. Add richer docstrings with parameter contracts and examples.
3. Publish endpoint matrix (supported/experimental/deprecated).
4. Ensure compatibility with both EE and PL base URLs where API parity exists.

### Phase 4 — Verification & Release
1. Unit tests with mocked `requests` for each endpoint method and error branch.
2. Contract tests (golden request tests) verifying method→endpoint/version mapping.
3. Optional live integration suite behind env vars (`MERIT_API_ID`, `MERIT_API_KEY`).
4. Semantic versioned release and changelog.

---

## 5) Method-Definition Pattern (for consistency)

For every endpoint, follow one pattern:

1. Namespace method with descriptive pythonic name.
2. Docstring includes:
   - reference manual section name,
   - endpoint name,
   - API version (`v1`/`v2`),
   - required fields.
3. Calls `_post(endpoint, body, version=...)`.
4. Optional thin payload normalization (e.g., alias support for `InvoiceRow`/`InvoiceRows` if Merit accepts both).

Example style:
- `payments.create_sales_invoice_payment(payload)` -> `createpayment` (or exact documented operation if distinct).
- `sales_offers.create_invoice_from_offer(payload)` -> mapped documented operation.

---

## 6) Backward Compatibility Plan

1. Preserve existing public names (`customers.get_list`, `customers.send`, etc.) for at least one minor release.
2. Introduce clearer aliases without breaking old names.
3. Mark old names with deprecation warnings only after complete parity is delivered.

---

## 7) Test Plan

### Unit tests (required)
- Auth signature deterministic tests (frozen timestamp).
- URL/endpoint/version mapping tests for every method.
- Error mapping tests:
  - non-200 responses,
  - malformed JSON,
  - network exceptions,
  - API-declared business errors.

### Integration tests (optional CI job/manual)
- Smoke reads: customers, items, taxes, banks.
- Write/read roundtrip in sandbox or dedicated company:
  - create entity,
  - retrieve,
  - update,
  - cleanup/delete if supported.

### Regression matrix
Maintain `tests/test_endpoint_matrix.py` that asserts every planned endpoint has a corresponding SDK method.

---

## 8) Documentation Deliverables

1. `docs/endpoint_matrix.md` — full manual-to-SDK mapping.
2. `docs/examples/` — focused runnable examples for invoices, offers, recurring, payments, reports.
3. `README.md` update with:
   - install,
   - authentication,
   - namespace overview,
   - quickstart,
   - error handling.

---

## 9) Execution Order Recommendation

1. Foundation hardening (Phase 0).
2. Read endpoints (Phase 1).
3. Write endpoints (Phase 2).
4. Reports and advanced flows.
5. Docs/examples and release.

This order reduces risk because read-only methods validate transport/auth correctness before introducing write-side business complexity.

---

## 10) Definition of Done

The implementation is complete when all are true:
1. Every operation documented in the Merit Aktiva reference manual has an SDK method or an explicit documented rationale for exclusion.
2. Endpoint matrix test passes with 100% planned coverage.
3. Existing API surface remains backward-compatible.
4. Core examples run successfully in a real environment with valid credentials.
5. A release is tagged with changelog entries by domain.

