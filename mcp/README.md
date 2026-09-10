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

The MCP write surface is intentionally minimal: `merit_write_customers` (action `customer_upsert`) and `merit_write_sales` (action `sales_invoice_create`, draft preparation only). Delivery (email/e-invoice), deletion, credit invoices, purchase invoices, payments, and master-data writes are not exposed to AI agents — the underlying `merit-api` SDK still offers them for programmatic use. Purchase/cost invoices are best handled by a dedicated guarded integration (e.g. Costpocket) or Merit's own UI.
