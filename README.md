# merit_api Monorepo

This repository is now split into two separate projects by content:

- [merit_api/](./merit_api) - the Python SDK package `merit-api`
- [mcp/](./mcp) - the Python MCP server package `merit-api-mcp-server`

The repository root also contains the npm wrapper package `merit-api-mcp`, which exists so end users can run the MCP server with:

```bash
npx -y merit-api-mcp
```

## Layout

### SDK project

Path: [merit_api/](./merit_api)

- Python package: `merit_api`
- Distribution name: `merit-api`
- Source: [merit_api/src/merit_api](./merit_api/src/merit_api)
- Tests: [merit_api/tests](./merit_api/tests)

### MCP project

Path: [mcp/](./mcp)

- Python package: `merit_api_mcp`
- Distribution name: `merit-api-mcp-server`
- Source: [mcp/src/merit_api_mcp](./mcp/src/merit_api_mcp)
- Tests: [mcp/tests](./mcp/tests)

### npm wrapper

At the repo root:

- npm package: `merit-api-mcp`
- Launcher: [bin/merit-api-mcp.js](./bin/merit-api-mcp.js)

The wrapper bootstraps a private virtualenv, installs both local Python subprojects into it, and runs `python -m merit_api_mcp`.

## Development

SDK tests:

```bash
cd merit_api
python3 -m pytest -q
```

MCP tests:

```bash
cd mcp
python3 -m pytest -q
```

npm wrapper dry run:

```bash
npm pack --dry-run
```
