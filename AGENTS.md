# AGENTS.md

Codebase guidance for AI coding agents working in this repository.

## What This Project Is

Unofficial MCP server and Python SDK for the [Merit Aktiva](https://aktiva.merit.ee) accounting REST API (Estonian/Polish). The project is a **uv workspace** with two independently publishable packages:

- `merit_api/` — Python SDK (`merit-api` on PyPI)
- `mcp/` — FastMCP server (`merit-unofficial-mcp-server` on PyPI)

## Commands

```bash
# Install all dependencies (both packages)
uv sync --all-extras

# Run SDK tests
uv run --package merit-api pytest

# Run MCP server tests
uv run --package merit-unofficial-mcp-server pytest

# Run a single test file
uv run --package merit-api pytest merit_api/tests/test_read_methods.py

# Run integration tests (requires live Merit credentials)
MERIT_API_INTEGRATION_TEST=true MERIT_API_ID=xxx MERIT_API_KEY=xxx \
  uv run --package merit-api pytest

# Start the MCP server locally
uv run --package merit-unofficial-mcp-server merit-unofficial-mcp
```

There is no separate linting configuration. CI runs pytest for both packages.

## Architecture

### SDK (`merit_api/src/merit_api/`)

`MeritAPI` in `client.py` is the single entry point. It owns the HTTP session and HMAC-SHA256 request signing: every request body is deterministically serialized (`json.dumps` with `sort_keys=True`), then signed with `api_id + timestamp + body`. Auth params (`apiId`, `timestamp`, `signature`) go on the query string.

Thirteen domain namespaces are instantiated as properties on `MeritAPI` (e.g. `client.sales`, `client.customers`). They all inherit from `Namespace` in `namespaces.py` and call `self._client._post()` or `self._client._get()`. The client exposes three HTTP methods: `_post`, `_get`, and `_get_pdf` (for base64-encoded PDF responses).

Key SDK behaviours to know:
- **Date format**: Merit API fields expect `YYYYMMDD` strings. `_to_yyyymmdd()` converts ISO 8601 to this format; use it when passing dates from invoice-list responses (which return ISO 8601) to write endpoints.
- **Default period**: `Namespace._apply_default_period()` injects the last 90 days when `PeriodStart`/`PeriodEnd` are omitted.
- **Business errors**: Merit returns HTTP 200 with `{"Success": false, "Error": "..."}` for errors. `_raise_for_business_error()` detects this and raises `MeritAPIError`.
- **Plain-text responses**: Some endpoints (email/e-invoice delivery) return `"OK"` as a plain string. The client normalises these to `{"Message": "OK", "Success": true}`.

### MCP Server (`mcp/src/merit_api_mcp/`)

Built on **FastMCP**. The server exposes Merit's many endpoints via ~15 consolidated tools instead of one tool per endpoint.

`server.py` — `build_mcp_server()` wires everything together. It reads config from env, creates a `MeritAPI` client (or enters setup mode if credentials are absent), then iterates over `get_tool_specs()` to dynamically register tools.

`registry.py` — All tool and action definitions live here. Key types:
- `ActionSpec`: one Merit API action (e.g. `customers_list`), including its invoker function and required field validation.
- `ToolSpec`: a group of related actions exposed as a single MCP tool (e.g. `merit_read_master_data`).

**Write tools use a preview/confirm pattern**: calling `merit_write_sales` returns a preview and a `confirmation_code`; no data is written. Calling `merit_write_sales_confirm` with that code and `confirmed=true` executes the write. The `confirmation_store` is an in-process dict keyed by a hash of `(action, arguments)`, so codes are tied to specific arguments and cannot be reused for different payloads.

`config.py` — Loads `MERIT_API_ID`, `MERIT_API_KEY`, `MERIT_API_COUNTRY` from environment. Falls back to `~/.env` via python-dotenv in dev. Returns `None` (setup mode) when credentials are absent.

## Adding New API Endpoints

1. Add a method to the relevant namespace class in `merit_api/src/merit_api/namespaces.py`, calling `self._client._post(...)` or `self._client._get(...)`.
2. Add an `ActionSpec` in `mcp/src/merit_api_mcp/registry.py`. Wire the invoker to the new namespace method. Add to the appropriate `ToolSpec`'s `actions` tuple, or create a new `ToolSpec` and add it to `get_tool_specs()`.
3. Write tests in `merit_api/tests/` (mocked) and, if mutating, add coverage in `mcp/tests/test_mcp_server.py`.

## Sales Invoice Creation Gotchas

The `SALES_INVOICE_CREATE_DESCRIPTION` constant in `registry.py:16` documents several non-obvious Merit API requirements:
- Field is `InvoiceRow` (singular), not `InvoiceRows`.
- `InvoiceNo` must be supplied; Merit does not auto-assign it.
- `UOMName` goes inside `Item`, not on the row directly.
- Use `Account`, not `AccountCode`.
- `TaxId` must be a GUID; `TaxAmount` is required even for zero-VAT rows.
- Do not set `DelivNote=true` on creation; leave invoices as undelivered drafts.

## Environment Variables

| Variable | Required | Default |
|---|---|---|
| `MERIT_API_ID` | Yes | — |
| `MERIT_API_KEY` | Yes | — |
| `MERIT_API_COUNTRY` | No | `EE` |

Country options: `EE` (Estonia, `aktiva.merit.ee`) or `PL` (Poland, `360ksiegowosc.pl`).
