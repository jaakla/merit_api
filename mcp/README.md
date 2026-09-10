# merit-unofficial-mcp-server

FastMCP server for the Merit Aktiva API.

This package is the Python MCP layer only. The repository also includes an npm wrapper at the root so end users can launch it with:

```bash
npx -y merit-unofficial-mcp
```

For direct Python usage:

```bash
python3 -m merit_api_mcp
```

Mutating tools use a preview/confirm flow. Calls to `merit_write_*` return a preview plus `confirmation_code` and do not change Merit data. To execute the change, call the matching `merit_write_*_confirm` tool with the same arguments, the returned `confirmation_code`, and `confirmed=true`.

The MCP write surface is intentionally minimal: `merit_write_customers` (`customer_upsert`) and `merit_write_sales` (`sales_invoice_create`). **Confirmation creates a real, unsent accounting invoice, not an unposted draft.** It can affect the ledger and reports before delivery. Only preview is non-writing; an agent can call both steps, so this flow is not proof of human approval.

The invoice profile accepts EUR, VAT-exclusive prices, positive quantities and net totals, non-negative prices/taxes, valid dates, and matched cent-rounded row totals. Items must already exist as non-stock items and are checked at confirmation. Unknown fields are rejected recursively, including payment, credit-document, delivery, and item-creation fields. Customer references contain only `Id`.

Delivery, deletion, credit invoices, purchase invoices, payments, and other master-data writes are not exposed. The underlying SDK remains unrestricted. Use Merit's UI or a dedicated integration for other workflows (e.g. Costpocket for cost invoices).

See [Merit's invoice schema](https://api.merit.ee/connecting-robots/reference-manual/sales-invoices/create-sales-invoice/) for the documented accounting semantics. This server does not claim an unposted-draft state or independently verify VAT/accounting correctness.
