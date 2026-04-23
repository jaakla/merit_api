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
