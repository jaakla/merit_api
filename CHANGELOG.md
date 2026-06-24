# Changelog

All notable changes to merit_api project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.2] - 2026-06-24

### Fixed

- Purchase invoice creation (MCP `merit_write_purchases` action
  `purchase_invoice_create`) now ships full schema guidance and payload
  validation, matching the sales invoice tool. Previously the action had only a
  one-line description and no validator, so callers guessed the wrong shape
  (`TaxName`/`ArticleCode`/`AccountCode`/`VendorId`/`DocumentDate`) and Merit
  returned cryptic errors such as `VAT with Id 00000000-0000-0000-0000-000000000000
  is missing or nonactive` and `NullReferenceException`. The new validator rejects
  those mistakes up front and points to the correct fields (`Vendor.{Id,Name}`,
  `DocDate`, `Item.{Code,Description,UOMName,TaxId}`, `GLAccountCode`, `TaxId` GUID,
  `TaxAmount`, `TotalAmount`).

### Changed

- Removed the hardcoded company-specific `GOOGOLPLEX_NO_VAT_TAX_ID` tax GUID from
  the MCP tool descriptions. Merit tax GUIDs are per-company, so both the sales and
  purchase invoice descriptions now instruct resolving tax IDs via
  `merit_read_master_data action=taxes_list` (e.g. match `Ei ole käive` /
  `Not included in Turnover` for no-VAT) rather than hardcoding a GUID.

## [0.5.1] - 2026-06-15

### Fixed

- Purchase invoice creation (`purchases.send_invoice` / MCP `merit_write_purchases`)
  no longer fails with Merit's `Periood liiga pikk(max 3 kuud)` error. The internal
  `getpurchorders` duplicate check previously requested a 730-day window, exceeding
  Merit's hard 3-month limit. The check now anchors on the invoice's `DocDate` and
  clamps the window to ~85 days, always staying within the limit while still catching
  recent duplicates.
- `customers.send` (customer_upsert) now targets `/api/v2/sendcustomer` instead of the
  non-existent `/api/v1/sendcustomer`, which was returning 404 and blocking customer
  creation through the MCP `merit_write_customers` tool.

### Added

#### Priority 1: Critical Sales Invoice Delivery Methods
- `sales.send_invoice_by_email(id: str, delivnote: bool = False) -> Dict`
  - Send a sales invoice to customer via email
  - Supports optional delivery note mode (invoice without prices)
  - Returns status message from mail server
  - MCP Tool: `sales_send_invoice_by_email`

- `sales.send_invoice_by_einvoice(id: str) -> Dict`
  - Send invoice as structured e-invoice format
  - Returns status message or error
  - MCP Tool: `sales_send_invoice_by_einvoice`

- `sales.get_invoice_pdf(id: str) -> Dict[str, str]`
  - Retrieve invoice as PDF document
  - Returns base64-encoded PDF content (MCP-compatible format)
  - Can be decoded using standard `base64.b64decode()`
  - MCP Tool: `sales_get_invoice_pdf`

- New client method: `MeritAPI._get_pdf()`
  - Internal method for retrieving PDF and binary responses
  - Handles both binary responses and JSON-wrapped base64 content
  - Implements retry logic consistent with `_post()` method

- New parameter mode in MCP registry: `id_with_delivnote`
  - Used for methods requiring ID and optional boolean flag
  - Automatically generates MCP tool signatures with proper type hints

### Changed

- Updated MCP tool registry to include 3 new invoice delivery tools
- Total MCP tools increased from 29 to 32

### Implementation Details

**Files Modified:**
- `merit_api/src/merit_api/client.py` — Added `_get_pdf()` method
- `merit_api/src/merit_api/namespaces.py` — Added 3 methods to `Sales` namespace
- `mcp/src/merit_api_mcp/registry.py` — Updated tool specs and parameter handling

**Testing:**
- Added comprehensive test suite: `test_priority1_invoice_delivery.py`
- 10 tests covering basic functionality, error cases, and integration workflows
- 100% test coverage for new methods

**API Endpoints Used:**
- `POST /v2/sendinvoicebyemail` — Email delivery
- `POST /v2/sendinvoicebyeinvoice` — E-invoice delivery
- `POST /v2/getinvoicepdf` — PDF retrieval

### Notes

- All Priority 1 methods use Merit Aktiva API v2
- Email delivery requires customer email address to be configured
- E-invoice delivery requires valid e-invoice configuration
- PDF retrieval returns base64-encoded content for MCP compatibility
- Existing retry logic, authentication, and error handling apply to all new methods
