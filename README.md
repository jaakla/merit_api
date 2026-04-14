# Merit API MCP Server

MCP server and Python SDK for the Merit Aktiva REST API. The MCP server is built with FastMCP and currently exposes 29 tools, 3 workflow prompts, and 2 resources. It works with MCP clients such as Claude Code, Codex CLI, Cursor, Windsurf, Cline, Gemini CLI, and others.

> **Active development.** This package is still evolving and the MCP layer is an early version. If you find incorrect behavior, treat it as experimental and verify the resulting accounting data manually.

## Disclaimer

**This is an experimental, unofficial project.** It is not affiliated with, endorsed by, or officially connected to Merit Aktiva.

**Use entirely at your own risk.** This software can read and mutate live accounting data, including customers, invoices, payments, items, taxes, and dimensions. The authors accept no responsibility for incorrect bookings, deleted records, or other downstream damage.

By using this software you acknowledge that:

- You are responsible for verifying all created or modified accounting data
- You should test thoroughly before using it against important live data
- This is experimental software with no warranty of any kind

## Requirements

- Python 3.10+

## Installation

Install from PyPI:

```bash
pip install merit-api
```

For local development:

```bash
pip install -e ".[dev]"
```

## Setup

### 1. Add the MCP server

Most AI assistants can set this up for you if you tell them to add the npm package via `npx`:

```bash
npx -y merit-api-mcp
```

If you prefer to do it manually:

**Claude Code:**

```bash
claude mcp add merit-api -- npx -y merit-api-mcp
```

**Other MCP clients** using JSON config:

```json
{
  "mcpServers": {
    "merit-api": {
      "command": "npx",
      "args": ["-y", "merit-api-mcp"]
    }
  }
}
```

**Codex CLI** using TOML config:

```toml
[mcp_servers.merit-api]
command = "npx"
args = ["-y", "merit-api-mcp"]
```

The npm wrapper bootstraps a private Python virtualenv automatically and installs the bundled Python package into it, so users do not need to run `pip install` manually.

### 2. Python requirement

The `npx` package removes the need to install Python dependencies manually, but it still requires a local Python 3.10+ interpreter because the server itself is implemented in Python.

If you already have the Python package installed into a known environment, these manual launch forms also work:

```bash
merit-api-mcp
```

```bash
python3 -m merit_api.mcp
```

### 3. Add your API credentials

The server uses environment variables:

- `MERIT_API_ID`
- `MERIT_API_KEY`
- `MERIT_API_COUNTRY` optional, `EE` or `PL`, defaults to `EE`

Example:

```bash
export MERIT_API_ID=your-api-id
export MERIT_API_KEY=your-api-key
export MERIT_API_COUNTRY=EE
```

If `MERIT_API_ID` or `MERIT_API_KEY` is missing, the server starts in setup mode. In setup mode:

- `get_setup_instructions` remains available
- discovery resources remain available
- prompts remain available
- API-backed tools return setup guidance instead of calling Merit

### 4. Running from source

```bash
git clone https://github.com/jaak/merit_api.git
cd merit_api
pip install -e ".[dev]"
python3 -m merit_api.mcp
```

## SDK Usage

The package also works as a normal Python client:

```python
from merit_api import MeritAPI

client = MeritAPI(api_id="YOUR_API_ID", api_key="YOUR_API_KEY")

customers = client.customers.get_list()
invoices = client.sales.get_invoices(
    PeriodStart="2024-01-01",
    PeriodEnd="2024-01-31",
)
```

The client currently includes:

- deterministic request-body serialization for request signing
- configurable timeout and retry handling
- request and response logging hooks with secret redaction
- optional idempotency header generation
- API-level business error parsing from HTTP 200 responses

## Workflows (MCP Prompts)

The server currently includes 3 built-in prompts:

| Prompt | Description |
|---|---|
| `setup-merit-api` | Explain how to configure the required environment variables and start the server |
| `create-sales-invoice` | Guide an assistant through finding a customer and creating a sales invoice |
| `find-or-create-customer` | Guide an assistant through customer lookup and creation |

## Resources

| Resource | Description |
|---|---|
| `merit://server/info` | Server metadata, setup mode status, supported env vars, and warning text |
| `merit://tools/catalog` | Tool catalog including namespace, method, read-only vs mutating, and parameter mode |

## Tool Surface

The MCP server currently exposes the existing SDK surface directly.

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

Mutating tools are clearly labeled as mutating in their descriptions and in the tool catalog resource.

## Usage Examples

Once the MCP server is connected, you can talk to your AI assistant in natural language.

### Explore master data

> "List my customers matching Acme"

The assistant should use `customers_get_list` with a `Name` filter.

### Create a customer

> "Create a new customer for Example OÜ"

The assistant should build a customer payload and call `customers_send`.

### Create a sales invoice

> "Create a sales invoice for customer Acme for April consulting work"

The assistant can use `customers_get_list`, optionally `find-or-create-customer`, and then `sales_send_invoice`.

### Inspect financial reference data

> "What banks, cost centers, and projects exist in Merit?"

The assistant can use `financial_get_banks`, `financial_get_costs`, and `financial_get_projects`.

## Updating

If installed from PyPI:

```bash
pip install -U merit-api
```

Then restart or reload the MCP server in your client.

If installed via `npx`:

```bash
npx -y merit-api-mcp
```

The wrapper keeps a versioned private virtualenv cache and refreshes it when the npm package version changes.

If running from a local checkout:

```bash
git pull
pip install -e ".[dev]"
```

Then restart the MCP server in your client.

## Development

Run the test suite:

```bash
pytest
```

The test suite includes:

- transport and error-handling unit tests
- in-process FastMCP tool registration tests
- setup mode tests
- prompt and resource smoke tests

Live integration tests are opt-in:

```bash
MERIT_API_INTEGRATION_TEST=true pytest
```

## Good to know

- The current MCP server is single-connection only
- There is no audit-log persistence yet
- There are no dry-run write flows yet
- There is no document ingestion or file-processing workflow layer yet
- The MCP schemas stay generic where the underlying SDK is generic

## License

[MIT](LICENSE)
