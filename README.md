# Merit API Python Client

`merit-api` is a Python SDK for the Merit Aktiva API, with a first-party FastMCP server that exposes the current SDK surface as MCP tools.

## Requirements

- Python 3.10+

## Installation

```bash
pip install merit-api
```

For local development:

```bash
pip install -e ".[dev]"
```

## SDK Usage

```python
from merit_api import MeritAPI

client = MeritAPI(api_id="YOUR_API_ID", api_key="YOUR_API_KEY")

customers = client.customers.get_list()
invoices = client.sales.get_invoices(
    PeriodStart="2024-01-01",
    PeriodEnd="2024-01-31",
)
```

The client now supports:

- deterministic request-body serialization for signing
- configurable timeout and retry handling
- request/response logging hooks with secret redaction
- automatic idempotency headers via `idempotency_key_factory`
- API-level business error parsing from successful HTTP responses

## MCP Server

The package includes a stdio MCP server built with FastMCP.

### Start the server

```bash
merit-api-mcp
```

### Environment variables

- `MERIT_API_ID`: required
- `MERIT_API_KEY`: required
- `MERIT_API_COUNTRY`: optional, `EE` or `PL`, defaults to `EE`

If the required credentials are missing, the server starts in setup mode. Setup mode still exposes discovery resources, prompts, and `get_setup_instructions`; API-backed tools return a setup guidance payload instead of calling Merit.

### MCP client config examples

Codex CLI:

```toml
[mcp_servers.merit_api]
command = "merit-api-mcp"
```

Generic JSON-based MCP clients:

```json
{
  "mcpServers": {
    "merit_api": {
      "command": "merit-api-mcp"
    }
  }
}
```

### Warning

Mutating MCP tools operate on live accounting data. Tools that create, update, or delete Merit records are marked as mutating in both tool descriptions and the `merit://tools/catalog` resource.

## MCP Features

### Setup and discovery

- Tool: `get_setup_instructions`
- Resource: `merit://server/info`
- Resource: `merit://tools/catalog`
- Prompt: `setup-merit-api`
- Prompt: `create-sales-invoice`
- Prompt: `find-or-create-customer`

### Exposed MCP tools

Customers:
- `customers_get_list`
- `customers_send`

Vendors:
- `vendors_get_list`
- `vendors_send`

Items:
- `items_get_list`
- `items_add`
- `items_update`

Sales:
- `sales_get_invoices`
- `sales_get_invoice`
- `sales_send_invoice`
- `sales_delete_invoice`
- `sales_send_credit_invoice`
- `sales_get_offers`
- `sales_get_recurring_invoices`

Purchases:
- `purchases_get_invoices`
- `purchases_send_invoice`

Financial:
- `financial_get_payments`
- `financial_create_payment`
- `financial_get_gl_batches`
- `financial_get_banks`
- `financial_get_costs`
- `financial_get_projects`

Inventory:
- `inventory_get_movements`

Assets:
- `assets_get_fixed_assets`

Taxes:
- `taxes_get_list`
- `taxes_send`

Dimensions:
- `dimensions_get_list`
- `dimensions_add`

## Development

Run the test suite:

```bash
pytest
```

The MCP server is also testable in-process through FastMCP's async API, so the repo includes direct tests for tool registration, setup mode, prompts, and resources.
