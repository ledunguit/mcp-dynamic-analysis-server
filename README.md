# Dynamic Analysis MCP Server (Valgrind Memcheck)

A local MCP (Model Context Protocol) server over STDIO focused on dynamic analysis. This build ships with Valgrind Memcheck as the first tool, and the codebase is structured to add more dynamic-analysis tools later.

## Overview

- Python 3.11+
- MCP server over STDIO (JSON-RPC)
- Valgrind Memcheck execution + XML parsing
- Normalized findings JSON for LLM reasoning
- Per-run artifact storage under `runs/`
- Basic tests with pytest

## Architecture

Layers:

1. **MCP Interface Layer**: `src/mcp_dynamic_analysis_server/app.py`
2. **Execution Layer**: `core/command_builder.py`, `core/runner.py`, `core/validators.py`
3. **Parsing + Normalization**: `core/parser_memcheck.py`, `core/normalizer.py`, `core/severity.py`
4. **Artifact / Persistence**: `core/artifact_store.py`

Tools are registered in `app.py` and can be extended with additional dynamic-analysis tools. Valgrind Memcheck is currently exposed under `valgrind.*`.

## Environment Requirements

### Option A: Docker (recommended, no host Valgrind needed)
- Docker + Docker Compose

### Option B: Host (advanced)
- Python 3.11+ (pyenv recommended)
- Valgrind installed locally (Linux)
- A C compiler (`cc` or `clang`) for example binaries

## Configuration

Set `WORKSPACE_ROOT` to the root directory you want to allow for execution. By default it is the project root. All `target_path`, `cwd`, and suppression files must resolve under this directory.

For R2 uploads, configure credentials in `.env` (see `.env.example`).
`R2_ENDPOINT` is used for SDK/presigning, while `R2_ALLOW_HOSTS` controls which hosts are allowed for downloads. If you use a custom public domain for R2, set `R2_ALLOW_HOSTS` to that domain (and optionally also include the raw R2 endpoint host as a fallback). **Use hostnames only (no scheme).**
Optional: enable `R2_HEALTHCHECK_ON_STARTUP=true` to run a quick `head_bucket` at startup (timeout via `R2_HEALTHCHECK_TIMEOUT_SEC`). Failures are logged as warnings and do not stop the server.

## Setup (pyenv) [Host Only]

```bash
pyenv virtualenv 3.12.8 mcp-da
pyenv local mcp-da
pip install -e .[test]
```

## Install Valgrind [Host Only]

On macOS (Homebrew):

```bash
brew install valgrind
```

On Ubuntu/Debian:

```bash
sudo apt-get update && sudo apt-get install -y valgrind
```

## Docker (Recommended on macOS)

Valgrind is Linux-only. On macOS, use Docker to run the server and tools inside a Linux container.

Build and run the MCP server over HTTP (Valgrind runs inside the container):

```bash
docker compose up --build
```

The server listens on `http://localhost:8080`.

Artifacts will be written to `runs/` on the host via the volume mount.

## Build Example Vulnerable Binaries

If running on host (no Docker):

```bash
make -C examples/vulnerable
```

If running in Docker (recommended):

```bash
docker compose exec -T mcp-da make -C examples/vulnerable
```

Outputs:
- `examples/vulnerable/bin/invalid_read`
- `examples/vulnerable/bin/leak`

## Start MCP Server (STDIO) [Host Only]

```bash
mcp-da-server
```

The server reads JSON-RPC messages from STDIN and writes responses to STDOUT.

## HTTP API Mode

You can also run the server as a simple HTTP JSON-RPC API:

```bash
mcp-da-server --transport http --host 0.0.0.0 --port 8080
```

Send JSON-RPC to `POST /mcp`:

```bash
curl -s http://localhost:8080/mcp \\\n  -H 'Content-Type: application/json' \\\n  -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\",\"params\":{}}'\n```

Example JSON-RPC (tools/call):

```json
{ "jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": { "name": "valgrind.analyze_memcheck", "arguments": { "target_path": "examples/vulnerable/bin/invalid_read" } } }
```

Response (result content is JSON text):

```json
{ "jsonrpc": "2.0", "id": 1, "result": { "content": [ { "type": "text", "text": "{\\n  \\\"run_id\\\": \\\"...\\\"\\n}" } ] } }
```

## MCP Client/Host Configuration

Example host configuration (pseudo):

```json
{
  "mcpServers": {
    "dynamic-analysis": {
      "command": "mcp-da-server",
      "args": []
    }
  }
}
```

## Tooling

### `valgrind.analyze_memcheck`

Input (example):

```json
{
  "target_path": "examples/vulnerable/bin/invalid_read",
  "args": [],
  "cwd": "examples/vulnerable",
  "timeout_sec": 30,
  "track_origins": true,
  "leak_check": "full",
  "show_leak_kinds": "all",
  "xml": true,
  "suppressions": [],
  "env": {},
  "stdin": "",
  "labels": ["demo"]
}
```

For remote/public servers, you can upload a binary to R2 and pass `artifact_id` or a `target_url`:

```json
{
  "artifact_id": "abcd1234",
  "args": [],
  "cwd": "/app/workdir",
  "timeout_sec": 60,
  "track_origins": true,
  "leak_check": "full",
  "show_leak_kinds": "all",
  "xml": true,
  "suppressions": [],
  "env": {},
  "stdin": ""
}
```

Output (summary):

```json
{
  "run_id": "20260313-153012-acde1234",
  "status": "completed",
  "tool": "memcheck",
  "exit_code": 42,
  "timed_out": false,
  "error_exit_code_triggered": true,
  "stats": {
    "finding_count": 1,
    "high": 1,
    "medium": 0,
    "low": 0
  },
  "top_findings": ["..."],
  "artifacts": {
    "run_dir": "runs/20260313-153012-acde1234",
    "report_path": "runs/20260313-153012-acde1234/normalized_report.json",
    "xml_path": "runs/20260313-153012-acde1234/valgrind.xml",
    "log_path": "runs/20260313-153012-acde1234/valgrind.log",
    "stdout_path": "runs/20260313-153012-acde1234/stdout.txt",
    "stderr_path": "runs/20260313-153012-acde1234/stderr.txt"
  }
}
```

### `valgrind.get_report`

Input:

```json
{ "run_id": "20260313-153012-acde1234" }
```

Output: full normalized report JSON.

### `valgrind.list_findings`

Input:

```json
{
  "run_id": "20260313-153012-acde1234",
  "severity": "high",
  "kind": "InvalidRead",
  "file": "src/main.c",
  "function": "parse_input",
  "limit": 20
}
```

Output:

```json
{
  "run_id": "20260313-153012-acde1234",
  "count": 3,
  "findings": []
}
```

### `valgrind.compare_runs`

Input:

```json
{
  "base_run_id": "20260313-153012-acde1234",
  "new_run_id": "20260313-153512-acde5678"
}
```

Output:

```json
{
  "base_run_id": "20260313-153012-acde1234",
  "new_run_id": "20260313-153512-acde5678",
  "summary": {"fixed": 0, "new": 1, "persistent": 2},
  "fixed_findings": [],
  "new_findings": [],
  "persistent_findings": []
}
```

### `valgrind.get_raw_artifact`

Input:

```json
{ "run_id": "20260313-153012-acde1234", "artifact_type": "xml" }
```

Output:

```json
{
  "run_id": "20260313-153012-acde1234",
  "artifact_type": "xml",
  "path": "runs/20260313-153012-acde1234/valgrind.xml",
  "content": "...",
  "truncated": false,
  "size_bytes": 12345
}
```

### `artifact.create_upload_url`

Create a presigned R2 upload URL for binaries.

Input:

```json
{
  "filename": "app.bin",
  "content_type": "application/octet-stream",
  "size_bytes": 123456,
  "sha256": "..."
}
```

Output:

```json
{
  "artifact_id": "abcd1234",
  "upload_url": "https://...presigned-put...",
  "download_url": "https://...presigned-get...",
  "expires_in_sec": 900,
  "key": "uploads/abcd1234/app.bin"
}
```

## Run Artifacts

Each run creates `runs/<run_id>/` with:

- `request.json`
- `command.txt`
- `stdout.txt`
- `stderr.txt`
- `valgrind.xml`
- `valgrind.log`
- `normalized_report.json`
- `summary.json`
- `metadata.json`

## Resource Provider (Bonus)

Resources are exposed under the URI scheme:

```
artifact://<run_id>/<artifact_type>
```

Example:

```
artifact://20260313-153012-acde1234/xml
```

## Prompts (Bonus)

The server exposes a `judge_guidance` prompt to help LLMs interpret Memcheck findings.

## Demo Script (Bonus)

Run an end-to-end demo (build examples, run Memcheck twice, compare):

```bash
python scripts/demo_end_to_end.py
```

## Tests

```bash
pytest
```

## Known Limitations

- Only Valgrind Memcheck is implemented today, but the registry supports adding more dynamic-analysis tools.
- The JSON-RPC STDIO transport expects one JSON message per line.
- Large artifacts are truncated when read via `valgrind.get_raw_artifact` or resource reads.

## Extending

To add new dynamic-analysis tools:

1. Implement a new tool handler in `src/mcp_dynamic_analysis_server/tools/`.
2. Add parser/normalizer modules under `core/` as needed.
3. Register the tool in `app.py` with a new name and JSON schema.

## Notes on Requirements

- XML output is enforced for Memcheck to ensure structured parsing.
- The server validates executable paths within `WORKSPACE_ROOT`.
- Artifacts are isolated per run id.

## Project Structure (Excerpt)

```
mcp_dynamic_analysis_server/
  pyproject.toml
  README.md
  .env.example
  src/mcp_dynamic_analysis_server/
    app.py
    config.py
    logging_config.py
    models/
    tools/
    core/
    resources/
    prompts/
  runs/
  examples/
  tests/
```
