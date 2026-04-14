#!/usr/bin/env node

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const PACKAGE_ROOT = path.resolve(__dirname, "..");
const PACKAGE_JSON = JSON.parse(
  fs.readFileSync(path.join(PACKAGE_ROOT, "package.json"), "utf8"),
);
const VERSION = PACKAGE_JSON.version;

function fail(message) {
  process.stderr.write(`merit-api-mcp: ${message}\n`);
  process.exit(1);
}

function defaultCacheDir() {
  if (process.env.MERIT_API_MCP_VENV_DIR) {
    return process.env.MERIT_API_MCP_VENV_DIR;
  }
  if (process.platform === "win32") {
    return path.join(
      process.env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local"),
      "merit-api-mcp",
      VERSION,
    );
  }
  const base = process.env.XDG_CACHE_HOME || path.join(os.homedir(), ".cache");
  return path.join(base, "merit-api-mcp", VERSION);
}

function pythonCandidates() {
  const candidates = [];
  if (process.env.MERIT_API_MCP_PYTHON) {
    candidates.push([process.env.MERIT_API_MCP_PYTHON]);
  }
  if (process.platform === "win32") {
    candidates.push(["py", "-3"]);
  }
  candidates.push(["python3"], ["python"]);
  return candidates;
}

function findPython() {
  for (const candidate of pythonCandidates()) {
    const probe = spawnSync(candidate[0], [...candidate.slice(1), "--version"], {
      stdio: "ignore",
    });
    if (probe.status === 0) {
      return candidate;
    }
  }
  fail(
    "Python 3.10+ is required but no usable interpreter was found. " +
      "Install Python and rerun the command.",
  );
}

function runChecked(command, args, options = {}) {
  const result = spawnSync(command, args, {
    stdio: "inherit",
    ...options,
  });
  if (result.error) {
    fail(`failed to run ${command}: ${result.error.message}`);
  }
  if (result.status !== 0) {
    process.exit(result.status || 1);
  }
}

function venvPythonPath(venvDir) {
  if (process.platform === "win32") {
    return path.join(venvDir, "Scripts", "python.exe");
  }
  return path.join(venvDir, "bin", "python");
}

function ensureVenv(pythonCommand, venvDir) {
  const pythonInVenv = venvPythonPath(venvDir);
  if (!fs.existsSync(pythonInVenv)) {
    fs.mkdirSync(venvDir, { recursive: true });
    process.stderr.write("merit-api-mcp: creating private Python environment\n");
    runChecked(pythonCommand[0], [...pythonCommand.slice(1), "-m", "venv", venvDir]);
  }
  return pythonInVenv;
}

function ensureInstalled(pythonInVenv, venvDir) {
  const markerPath = path.join(venvDir, ".installed-version");
  const installedVersion = fs.existsSync(markerPath)
    ? fs.readFileSync(markerPath, "utf8").trim()
    : "";

  if (installedVersion === VERSION) {
    return;
  }

  process.stderr.write("merit-api-mcp: installing bundled Python package\n");
  runChecked(pythonInVenv, [
    "-m",
    "pip",
    "install",
    "--disable-pip-version-check",
    "--upgrade",
    "pip",
  ]);
  runChecked(pythonInVenv, [
    "-m",
    "pip",
    "install",
    "--disable-pip-version-check",
    "--upgrade",
    PACKAGE_ROOT,
  ]);
  fs.writeFileSync(markerPath, `${VERSION}\n`);
}

function main() {
  const venvDir = defaultCacheDir();
  const pythonCommand = findPython();
  const pythonInVenv = ensureVenv(pythonCommand, venvDir);
  ensureInstalled(pythonInVenv, venvDir);

  const result = spawnSync(
    pythonInVenv,
    ["-m", "merit_api.mcp", ...process.argv.slice(2)],
    { stdio: "inherit", env: process.env },
  );
  if (result.error) {
    fail(`failed to launch merit_api.mcp: ${result.error.message}`);
  }
  process.exit(result.status || 0);
}

main();
