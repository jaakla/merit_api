#!/usr/bin/env node

const { spawnSync } = require("node:child_process");

const WARNING = `
merit-unofficial-mcp: [DEPRECATION WARNING]
This npm package is deprecated and will be retired in a future release.
The server has migrated to a native, high-performance Python workflow using 'uv' / 'uvx'.

To avoid this warning and get future updates, please update your MCP configuration to use uvx directly:
  Command: "uvx"
  Args: ["--from", "git+https://github.com/jaakla/merit_api.git#subdirectory=mcp", "merit-unofficial-mcp"]
`;

const ERROR_NO_UV = `
merit-unofficial-mcp: [ERROR]
This npm package is deprecated and has migrated to a native Python uv/uvx workflow.
To run this server, you must install 'uv' (https://docs.astral.sh/uv/) and update your config.

Please install 'uv' on your system and run:
  uvx --from git+https://github.com/jaakla/merit_api.git#subdirectory=mcp merit-unofficial-mcp
`;

// Check if 'uv' is available on the system path
const probe = spawnSync("uv", ["--version"], { stdio: "ignore" });

if (probe.status === 0) {
  // Print warning on stderr so it doesn't pollute stdout (which MCP reads as JSON-RPC)
  process.stderr.write(WARNING + "\nForwarding execution to uvx...\n\n");

  // Spawn uvx forwarding all arguments and inheriting stdin, stdout, and stderr
  const result = spawnSync(
    "uvx",
    [
      "--from",
      "git+https://github.com/jaakla/merit_api.git#subdirectory=mcp",
      "merit-unofficial-mcp",
      ...process.argv.slice(2)
    ],
    { stdio: "inherit", env: process.env }
  );

  process.exit(result.status || 0);
} else {
  process.stderr.write(ERROR_NO_UV + "\n");
  process.exit(1);
}
