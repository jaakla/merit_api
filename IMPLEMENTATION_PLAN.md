# Merit API Implementation Plan

> **Last Updated:** April 15, 2026

## Executive Summary

The merit_api Python SDK currently implements **10 namespaces** with **~40 methods**, providing coverage of core accounting operations. Based on the Merit Aktiva REST API reference manual, there are **50+ additional endpoints** available that should be implemented to provide comprehensive API coverage.

This plan prioritizes implementation in phases, focusing on high-impact, commonly-used endpoints first.

---

## Current Implementation Status

### ✅ Implemented Namespaces (29 MCP Tools)

| Namespace | Methods | Status |
|-----------|---------|--------|
| **Customers** | `get_list()`, `send()` | Complete for basic ops |
| **Vendors** | `get_list()`, `send()` | Complete for basic ops |
| **Items** | `get_list()`, `add()`, `update()` | Complete for basic ops |
| **Sales** | 7 methods (invoices, offers, recurring) | **Partial** - missing email/einvoice |
| **Purchases** | `get_invoices()`, `send_invoice()` | **Partial** - missing details |
| **Financial** | 5 methods (payments, GL, banks) | **Partial** - missing many payment types |
| **Inventory** | `get_movements()` | **Partial** - missing locations, send |
| **Assets** | `get_fixed_assets()` | **Partial** - missing send, other methods |
| **Taxes** | `get_list()`, `send()` | Complete |
| **Dimensions** | `get_list()`, `add()` | Complete |

---

## Phase 1: Critical Sales Invoice Methods (PRIORITY 1)

**Impact:** High - Core invoicing workflow  
**Effort:** Low-Medium  
**Timeline:** 1-2 days  
**Status:** ✅ **COMPLETE** (April 15, 2026)

### Implementation Summary

Implemented all 3 methods on April 15, 2026:
- **Files Modified:** 5 files
- **Tests Added:** 10 comprehensive tests (100% pass rate)
- **MCP Tools Added:** 3 new tools (total: 32)
- **Breaking Changes:** None
- **Documentation:** Complete with examples

### 1.1 Sales Invoice Delivery Methods

#### `sales.send_invoice_by_email(id: str, delivnote: bool = False) -> Dict`
- **Endpoint:** `/sendinvoicebyemail` (v2)
- **Parameters:** `Id` (GUID), `DelivNote` (bool)
- **Returns:** Status message or error
- **Use Case:** Send created invoice to customer email
- **Implementation:** Simple query parameters POST

#### `sales.send_invoice_by_einvoice(id: str) -> Dict`
- **Endpoint:** `/sendinvoicebyeinvoice` (v2)
- **Parameters:** `Id` (GUID)
- **Returns:** Status message or error
- **Use Case:** Send as structured e-invoice
- **Implementation:** Simple parameter POST

#### `sales.get_invoice_pdf(id: str) -> bytes`
- **Endpoint:** `/getinvoicepdf` or similar
- **Parameters:** `Id` (GUID)
- **Returns:** PDF file bytes
- **Use Case:** Get PDF representation for download/storage
- **Implementation:** Binary file handling needed

### 1.2 Credit Invoice Details

#### `sales.get_credit_invoice(id: str) -> Dict`
- **Endpoint:** Similar to `getinvoice` but for credit
- **Parameters:** `Id` (GUID)
- **Returns:** Credit invoice details
- **Use Case:** Retrieve single credit invoice
- **Implementation:** May reuse existing logic

---

## Phase 2: Sales Offers Workflow (PRIORITY 2)

**Impact:** Medium-High - Sales quote management  
**Effort:** Medium  
**Timeline:** 2-3 days

### 2.1 Offers CRUD Operations

#### `sales.create_offer(offer: Dict[str, Any]) -> Dict`
- **Endpoint:** `/sendoffer` or `/createoffer`
- **Payload:** Similar to invoice structure
- **Returns:** Created offer with Id
- **Use Case:** Create sales quotes/offers

#### `sales.get_offer_details(id: str) -> Dict`
- **Endpoint:** `/getoffer`
- **Parameters:** `Id` (GUID)
- **Returns:** Single offer data
- **Use Case:** Retrieve specific offer details

#### `sales.update_offer(offer: Dict[str, Any]) -> Dict`
- **Endpoint:** `/updateoffer`
- **Payload:** Offer object with `Id` field
- **Returns:** Updated offer or status
- **Use Case:** Modify existing offer

#### `sales.set_offer_status(id: str, status: str) -> Dict`
- **Endpoint:** `/setofferstatus`
- **Parameters:** `Id` (GUID), `Status` (enum: pending/accepted/expired/etc)
- **Returns:** Status confirmation
- **Use Case:** Change offer lifecycle state

#### `sales.create_invoice_from_offer(offer_id: str, invoice_data: Dict) -> Dict`
- **Endpoint:** `/createinvoicefromoffer`
- **Parameters:** `Id`, additional invoice fields
- **Returns:** Created invoice
- **Use Case:** Convert accepted offer to invoice

---

## Phase 3: Recurring Invoices Management (PRIORITY 2)

**Impact:** Medium - Recurring billing workflows  
**Effort:** Medium  
**Timeline:** 2-3 days

### 3.1 Recurring Invoices

#### `sales.create_recurring_invoice(invoice: Dict[str, Any]) -> Dict`
- **Endpoint:** `/sendperinvoice`
- **Payload:** Recurring invoice structure with schedule
- **Returns:** Created recurring invoice with Id
- **Use Case:** Set up recurring billings

#### `sales.get_recurring_invoice_details(id: str) -> Dict`
- **Endpoint:** `/getperinvoice`
- **Parameters:** `Id` (GUID)
- **Returns:** Single recurring invoice details
- **Use Case:** View recurring invoice setup

#### `sales.get_recurring_invoice_addresses(id: str) -> List[Dict]`
- **Endpoint:** `/getperinvoicesclientsaddress`
- **Parameters:** `Id` (GUID)
- **Returns:** List of client addresses for recurring
- **Use Case:** Multiple delivery addresses for recurring

#### `sales.send_indication_values(indication: Dict[str, Any]) -> Dict`
- **Endpoint:** `/sendindicationvalues`
- **Payload:** `RecurringInvoiceId`, meter readings/usage values
- **Returns:** Confirmation or status
- **Use Case:** Update meter/usage readings for usage-based billing

---

## Phase 4: Payment Management (PRIORITY 3)

**Impact:** High - Core financial operations  
**Effort:** Medium-High  
**Timeline:** 3-4 days

### 4.1 Payment Type Reference

#### `financial.get_payment_types() -> List[Dict]`
- **Endpoint:** `/getpaymenttypes`
- **Parameters:** None
- **Returns:** List of valid payment types
- **Use Case:** Understand available payment methods

### 4.2 Sales Invoice Payments (Already have create_payment)

#### `financial.payment_of_sales_offer(payment: Dict[str, Any]) -> Dict`
- **Endpoint:** `/createpaymentsoffer`
- **Payload:** `OfferId`, amount, date, type, account
- **Returns:** Created payment record
- **Use Case:** Record payment against sales offer

### 4.3 Purchase Invoice Payments

#### `financial.payment_of_purchase_invoice(payment: Dict[str, Any]) -> Dict`
- **Endpoint:** `/createpaymentpurchase`
- **Payload:** `PurchaseId`, amount, date, type, account
- **Returns:** Created payment record
- **Use Case:** Record payment against PO

### 4.4 Payment Record Management

#### `financial.delete_payment(id: str) -> Dict`
- **Endpoint:** `/deletepayment`
- **Parameters:** `Id` (GUID)
- **Returns:** Confirmation or status
- **Use Case:** Remove incorrect payment record

#### `financial.get_payment_imports() -> List[Dict]`
- **Endpoint:** `/getpaymentimports`
- **Parameters:** Optional filters
- **Returns:** List of imported payments
- **Use Case:** View bank statement imports

#### `financial.bank_statement_import(statement: Dict[str, Any]) -> Dict`
- **Endpoint:** `/bankstatementimport`
- **Payload:** Bank statement file/data, format
- **Returns:** Import result with matched payments
- **Use Case:** Import and match bank transactions

#### `financial.send_settlement(settlement: Dict[str, Any]) -> Dict`
- **Endpoint:** `/sendsettlement`
- **Payload:** Settlement details
- **Returns:** Created settlement record
- **Use Case:** Record settlement/reconciliation

### 4.5 Special Payment Types

#### `financial.send_expense_payments(expenses: List[Dict[str, Any]]) -> List[Dict]`
- **Endpoint:** `/sendexpensepayments`
- **Payload:** Array of expense payment records
- **Returns:** Created payment records
- **Use Case:** Record employee expense reimbursements

#### `financial.list_expense_payments(**kwargs) -> List[Dict]`
- **Endpoint:** `/getexpensepayments`
- **Parameters:** Period/filter options
- **Returns:** List of expense payment records
- **Use Case:** View expense reimbursements

#### `financial.send_income_payments(incomes: List[Dict[str, Any]]) -> List[Dict]`
- **Endpoint:** `/sendincomepayments`
- **Payload:** Array of income payment records
- **Returns:** Created payment records
- **Use Case:** Record income-related payments

#### `financial.list_income_payments(**kwargs) -> List[Dict]`
- **Endpoint:** `/getincomepayments`
- **Parameters:** Period/filter options
- **Returns:** List of income payment records
- **Use Case:** View income payments

#### `financial.send_prepayments(prepayments: List[Dict[str, Any]]) -> List[Dict]`
- **Endpoint:** `/sendprepayments`
- **Payload:** Array of prepayment records
- **Returns:** Created prepayment records
- **Use Case:** Record advance payments received

---

## Phase 5: Purchase Invoice Details (PRIORITY 3)

**Impact:** Medium - Purchasing workflow  
**Effort:** Low  
**Timeline:** 1-2 days

### 5.1 Purchase Invoice Operations

#### `purchases.get_invoice_details(id: str) -> Dict`
- **Endpoint:** `/getpurchaseinvoice`
- **Parameters:** `Id` (GUID)
- **Returns:** Single purchase invoice details
- **Use Case:** View full PO details

#### `purchases.delete_invoice(id: str) -> Dict`
- **Endpoint:** `/deletepurchaseinvoice`
- **Parameters:** `Id` (GUID)
- **Returns:** Confirmation
- **Use Case:** Remove PO record

#### `purchases.create_invoice_waiting_approval(invoice: Dict[str, Any]) -> Dict`
- **Endpoint:** `/sendpurchaseorder`
- **Payload:** Invoice structure
- **Returns:** Created PO in draft/pending state
- **Use Case:** Create PO requiring approval before posting

---

## Phase 6: Inventory Management (PRIORITY 4)

**Impact:** Medium - For inventory-tracked businesses  
**Effort:** Medium  
**Timeline:** 2-3 days

### 6.1 Inventory Infrastructure

#### `inventory.get_locations() -> List[Dict]`
- **Endpoint:** `/getinventorylocations`
- **Parameters:** None
- **Returns:** List of warehouse/location records
- **Use Case:** Enumerate locations for movements

#### `inventory.send_movements(movements: List[Dict[str, Any]]) -> List[Dict]`
- **Endpoint:** `/sendinvmovements`
- **Payload:** Array of movement records with location, item, quantity, date
- **Returns:** Created movement records
- **Use Case:** Record inventory adjustments/transfers

---

## Phase 7: Fixed Assets Management (PRIORITY 4)

**Impact:** Low-Medium - For asset tracking  
**Effort:** Medium  
**Timeline:** 2-3 days

### 7.1 Fixed Asset Operations

#### `assets.get_locations() -> List[Dict]`
- **Endpoint:** `/getfixassetlocations`
- **Parameters:** None
- **Returns:** List of asset locations
- **Use Case:** Get available asset storage locations

#### `assets.get_responsible_employees() -> List[Dict]`
- **Endpoint:** `/responsibleemployeelist`
- **Parameters:** None
- **Returns:** List of employee/person records for responsibility
- **Use Case:** Assign asset responsibility

#### `assets.send_fixed_assets(assets: List[Dict[str, Any]]) -> List[Dict]`
- **Endpoint:** `/sendfixassets`
- **Payload:** Array of asset records with code, name, value, location, responsible
- **Returns:** Created asset records
- **Use Case:** Register/update fixed assets

---

## Phase 8: Master Data Extensions (PRIORITY 5)

**Impact:** Medium - Supporting data management  
**Effort:** Low-Medium  
**Timeline:** 2-3 days

### 8.1 Customer & Vendor Groups

#### `customers.create_group(group: Dict[str, Any]) -> Dict`
- **Endpoint:** `/sendcustomergroup`
- **Payload:** Group name, description, settings
- **Returns:** Created group with Id
- **Use Case:** Organize customers into categories

#### `customers.get_groups() -> List[Dict]`
- **Endpoint:** `/getcustomergroups`
- **Parameters:** None
- **Returns:** List of customer groups
- **Use Case:** List available customer categories

#### `vendors.create_group(group: Dict[str, Any]) -> Dict`
- **Endpoint:** `/sendvendorgroup`
- **Payload:** Group name, description
- **Returns:** Created group
- **Use Case:** Organize vendors

#### `vendors.get_groups() -> List[Dict]`
- **Endpoint:** `/getvendorgroups`
- **Parameters:** None
- **Returns:** List of vendor groups
- **Use Case:** List vendor categories

#### `vendors.update(vendor: Dict[str, Any]) -> Dict`
- **Endpoint:** `/updatevendor` or enhance `sendvendor`
- **Payload:** Vendor object with `Id`
- **Returns:** Updated vendor
- **Use Case:** Modify vendor details

### 8.2 Item Management Extensions

#### `items.get_groups() -> List[Dict]`
- **Endpoint:** `/getitemgroups`
- **Parameters:** None
- **Returns:** List of item groups/categories
- **Use Case:** View item categories

#### `items.create_group(group: Dict[str, Any]) -> Dict`
- **Endpoint:** `/senditemgroup`
- **Payload:** Group name, code
- **Returns:** Created group
- **Use Case:** Create item category

### 8.3 Sales Pricing & Discounts

#### `sales.get_prices(**kwargs) -> List[Dict]`
- **Endpoint:** `/getprices`
- **Parameters:** Filters (customer, item, date range)
- **Returns:** List of price records
- **Use Case:** View custom prices

#### `sales.send_price(price: Dict[str, Any]) -> Dict`
- **Endpoint:** `/sendprice`
- **Payload:** Price record with item, customer, amount, validity
- **Returns:** Created price record
- **Use Case:** Create custom price

#### `sales.get_discounts(**kwargs) -> List[Dict]`
- **Endpoint:** `/getdiscounts`
- **Parameters:** Filters
- **Returns:** List of discount records
- **Use Case:** View discounts

#### `sales.send_discount(discount: Dict[str, Any]) -> Dict`
- **Endpoint:** `/senddiscount`
- **Payload:** Discount record
- **Returns:** Created discount
- **Use Case:** Create discount rule

#### `sales.get_price(item_code: str, customer_id: str = None) -> Dict`
- **Endpoint:** `/getprice`
- **Parameters:** `ItemCode`, optional `CustomerId`
- **Returns:** Applicable price
- **Use Case:** Lookup current price

### 8.4 Reference Data

#### `items.get_units_of_measure() -> List[Dict]`
- **Endpoint:** `/getunitofmeasure`
- **Parameters:** None
- **Returns:** List of UOM records
- **Use Case:** View available units

#### `items.send_unit_of_measure(uom: Dict[str, Any]) -> Dict`
- **Endpoint:** `/sendunitofmeasure`
- **Payload:** UOM record
- **Returns:** Created UOM
- **Use Case:** Create custom unit

#### `financial.get_financial_years() -> List[Dict]`
- **Endpoint:** `/getfinancialyear`
- **Parameters:** None
- **Returns:** List of financial year configurations
- **Use Case:** View accounting periods

#### `financial.get_departments() -> List[Dict]`
- **Endpoint:** `/getdepartments`
- **Parameters:** None
- **Returns:** List of organizational departments
- **Use Case:** View departmental structure

#### `financial.get_accounts(**kwargs) -> List[Dict]`
- **Endpoint:** `/getaccounts`
- **Parameters:** Optional filters
- **Returns:** List of GL accounts
- **Use Case:** Get chart of accounts

---

## Phase 9: General Ledger Transactions (PRIORITY 5)

**Impact:** Low-Medium - Advanced accounting  
**Effort:** Medium-High  
**Timeline:** 3 days

### 9.1 GL Transaction Operations

#### `financial.create_gl_transaction(transaction: Dict[str, Any]) -> Dict`
- **Endpoint:** `/sendglbatch`
- **Payload:** GL batch with header and line items (account, debit/credit, amount)
- **Returns:** Created transaction with Id
- **Use Case:** Post manual journal entries

#### `financial.get_gl_batch_details(batch_id: str) -> Dict`
- **Endpoint:** `/getglbatch`
- **Parameters:** `Id` (GUID)
- **Returns:** Single batch details with lines
- **Use Case:** View specific journal batch

#### `financial.get_gl_transaction_full_details(transaction_id: str) -> Dict`
- **Endpoint:** `/getgltransactionfulldetails`
- **Parameters:** `Id` (GUID)
- **Returns:** Complete transaction audit trail
- **Use Case:** Get full GL transaction details including dim values

---

## Implementation Guidelines

### Code Organization

1. **Namespace methods** (`namespaces.py`):
   - Add methods to appropriate namespace classes
   - Follow existing naming conventions (verb-noun, e.g., `get_list`, `send_invoice`)
   - Document with docstrings including required parameters and return types

2. **Method signature pattern**:
   ```python
   def method_name(self, param1: str, **kwargs) -> Dict[str, Any]:
       """Description of operation."""
       return self._client._post("endpoint_name", {"Param1": param1, **kwargs})
   ```

3. **Version handling**:
   - Most sales invoice methods use `v2`
   - Legacy endpoints default to `v1`
   - Pass `version="v2"` when needed

### Testing Approach

1. **Unit tests** - Mock API responses using conftest fixtures
2. **Integration tests** - Test with real sandbox account (if available)
3. **Parameter validation** - Test required vs optional fields
4. **Response parsing** - Verify returned data structures

### MCP Server Integration

1. **Registry update** (`registry.py`):
   - Add `ToolSpec` entry for each new method
   - Categorize by param_mode (filters, payload, id, items, none)
   - Mark as mutating if creating/updating/deleting

2. **Tool naming convention**:
   - `{namespace}_{action}_{object}` (e.g., `sales_send_invoice_by_email`)
   - Keep MCP tool descriptions concise

### Documentation Requirements

1. **Docstrings** in Python code
2. **Tests** as integration examples
3. **CHANGELOG** entry for new endpoints
4. **MCP tool catalog** automatically generated from registry

---

## Implementation Sequencing

### Week 1 (4 days)
- **Phase 1:** Sales invoice delivery methods (send_email, send_einvoice, get_pdf)
- **Phase 2 (first half):** Offers create/get/update
- **Tests:** Unit tests for each new method

### Week 2 (4 days)  
- **Phase 2 (second half):** Complete offers (set_status, create_invoice_from_offer)
- **Phase 3:** Recurring invoices (create, get_details, addresses, indication values)
- **Tests:** Integration tests

### Week 3 (4 days)
- **Phase 4:** Payment methods (types, delete, imports, settlement, special payments)
- **Phase 5:** Purchase invoice (get_details, delete, waiting_approval)
- **Tests:** Payment flow tests

### Week 4 (4 days)
- **Phase 6:** Inventory (locations, send_movements)
- **Phase 7:** Fixed Assets (locations, responsible, send_assets)
- **Phase 8 (first half):** Master data (groups, pricing, units)
- **Tests:** Inventory/asset tests

### Week 5 (4 days)
- **Phase 8 (second half):** Complete master data
- **Phase 9:** GL Transactions (create, get_details, full_details)
- **Tests:** GL transaction tests
- **Final:** Documentation, CHANGELOG, examples

---

## Risk Mitigation

### API Documentation Gaps
- **Risk:** Merit API docs may lack some endpoint details
- **Mitigation:** Use reverse engineering from actual responses, examine existing successful calls in tests

### Field Name Inconsistencies
- **Risk:** Merit may use different field names for similar concepts in different endpoints
- **Mitigation:** Create detailed field mapping documentation, use consistent Python naming

### Version Compatibility
- **Risk:** Some endpoints may behave differently in EE vs PL
- **Mitigation:** Test both country variants (if access available), document country-specific behaviors

### Breaking Changes
- **Risk:** Modifications to sandbox data by new endpoints
- **Mitigation:** Encourage read-only testing first, provide clear warnings in docstrings for mutating operations

---

## Success Criteria

- ✅ All 50+ endpoints have corresponding Python methods
- ✅ All methods exposed as MCP tools
- ✅ Unit tests with mocked responses for each endpoint
- ✅ Integration tests for critical workflows (invoice→email, offer→invoice, etc.)
- ✅ Comprehensive docstrings and type hints
- ✅ Clear examples in README
- ✅ No breaking changes to existing API

---

## References

- Merit Aktiva API Reference: https://api.merit.ee/connecting-robots/reference-manual/
- Current Implementation: `merit_api/src/merit_api/namespaces.py`
- MCP Tool Registry: `mcp/src/merit_api_mcp/registry.py`
- Test Suite: `merit_api/tests/`
