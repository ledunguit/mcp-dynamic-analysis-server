from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Callable, Dict

from . import __version__
from .config import load_settings
from .http_server import run_http
from .logging_config import configure_logging
from .core.r2_client import R2Client, R2Config
from .prompts.judge_guidance import JUDGE_GUIDANCE
from .resources.artifact_resources import list_resources, read_resource
from .tools.analyze_memcheck import analyze_memcheck
from .tools.compare_runs import compare_runs
from .tools.create_upload_url import create_upload_url
from .tools.get_raw_artifact import get_raw_artifact
from .tools.get_report import get_report
from .tools.list_findings import list_findings
from .models.requests import (
    AnalyzeMemcheckRequest,
    CreateUploadUrlRequest,
    CompareRunsRequest,
    GetReportRequest,
    ListFindingsRequest,
    RawArtifactRequest,
)


def _tool_schema(model_cls: Any) -> Dict[str, Any]:
    return model_cls.model_json_schema()


ToolHandler = Callable[[Dict[str, Any]], Dict[str, Any]]


TOOLS: Dict[str, Dict[str, Any]] = {
    "valgrind.analyze_memcheck": {
        "handler": analyze_memcheck,
        "description": "Run Valgrind Memcheck and return a normalized summary.",
        "input_schema": _tool_schema(AnalyzeMemcheckRequest),
    },
    "valgrind.get_report": {
        "handler": get_report,
        "description": "Get full normalized report for a run.",
        "input_schema": _tool_schema(GetReportRequest),
    },
    "valgrind.list_findings": {
        "handler": list_findings,
        "description": "List findings with optional filters.",
        "input_schema": _tool_schema(ListFindingsRequest),
    },
    "valgrind.compare_runs": {
        "handler": compare_runs,
        "description": "Compare two runs and classify findings.",
        "input_schema": _tool_schema(CompareRunsRequest),
    },
    "valgrind.get_raw_artifact": {
        "handler": get_raw_artifact,
        "description": "Fetch raw artifact content for a run.",
        "input_schema": _tool_schema(RawArtifactRequest),
    },
    "artifact.create_upload_url": {
        "handler": create_upload_url,
        "description": "Create a presigned upload URL for R2.",
        "input_schema": _tool_schema(CreateUploadUrlRequest),
    },
}


def _handle_tools_list() -> Dict[str, Any]:
    tools = []
    for name, meta in TOOLS.items():
        tools.append(
            {
                "name": name,
                "description": meta["description"],
                "inputSchema": meta["input_schema"],
            }
        )
    return {"tools": tools}


def _handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    handler: ToolHandler = TOOLS[name]["handler"]
    result = handler(arguments)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2),
            }
        ]
    }


def _handle_resources_list() -> Dict[str, Any]:
    return {"resources": list_resources()}


def _handle_resources_read(params: Dict[str, Any]) -> Dict[str, Any]:
    uri = params.get("uri")
    if not uri:
        raise ValueError("Missing uri")
    content = read_resource(uri)
    return {"contents": [content]}


def _handle_prompts_list() -> Dict[str, Any]:
    return {
        "prompts": [
            {
                "name": "judge_guidance",
                "description": "Guidance for evaluating Memcheck findings.",
                "arguments": [],
            }
        ]
    }


def _handle_prompts_get(params: Dict[str, Any]) -> Dict[str, Any]:
    name = params.get("name")
    if name != "judge_guidance":
        raise ValueError(f"Unknown prompt: {name}")
    return {
        "messages": [
            {
                "role": "system",
                "content": JUDGE_GUIDANCE,
            }
        ]
    }


def _handle_initialize(_: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {"listChanged": False},
            "resources": {},
            "prompts": {},
        },
        "serverInfo": {"name": "dynamic-analysis-mcp", "version": __version__},
    }


METHODS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "initialize": _handle_initialize,
    "initialized": lambda _: {},
    "tools/list": lambda _: _handle_tools_list(),
    "tools/call": _handle_tools_call,
    "resources/list": lambda _: _handle_resources_list(),
    "resources/read": _handle_resources_read,
    "prompts/list": lambda _: _handle_prompts_list(),
    "prompts/get": _handle_prompts_get,
}


def _make_error_response(request_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _handle_message(message: Dict[str, Any]) -> Dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}

    if not method:
        return _make_error_response(request_id, -32600, "Invalid Request")

    handler = METHODS.get(method)
    if handler is None:
        if request_id is None:
            return None
        return _make_error_response(request_id, -32601, f"Method not found: {method}")

    try:
        result = handler(params)
        if request_id is None:
            return None
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except Exception as exc:
        return _make_error_response(request_id, -32000, str(exc))


def run_stdio() -> None:
    configure_logging()
    _log_startup("stdio")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            response = _make_error_response(None, -32700, "Parse error")
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue

        response = _handle_message(message)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


def run_http_server(host: str, port: int) -> None:
    configure_logging()
    _log_startup("http", host=host, port=port)
    run_http(_handle_message, host=host, port=port)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dynamic Analysis MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
    )
    parser.add_argument("--host", default=os.environ.get("MCP_HTTP_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("MCP_HTTP_PORT", "8080")))
    args = parser.parse_args()

    if args.transport == "http":
        run_http_server(args.host, args.port)
    else:
        run_stdio()


def _log_startup(transport: str, host: str | None = None, port: int | None = None) -> None:
    settings = load_settings()
    logger = logging.getLogger("mcp_dynamic_analysis_server")

    r2_configured = all(
        [
            settings.r2_endpoint,
            settings.r2_access_key_id,
            settings.r2_secret_access_key,
            settings.r2_bucket,
        ]
    )

    logger.info("Starting MCP server transport=%s version=%s", transport, __version__)
    if transport == "http":
        logger.info("HTTP bind %s:%s", host, port)

    logger.info("WORKSPACE_ROOT=%s", settings.workspace_root)
    logger.info("RUNS_DIR=%s", settings.runs_dir)
    logger.info("ARTIFACTS_DIR=%s", settings.artifacts_dir)
    logger.info("VALGRIND_BIN=%s", settings.valgrind_bin)
    logger.info("R2 configured=%s endpoint=%s bucket=%s region=%s ssl=%s prefix=%s",
                r2_configured,
                settings.r2_endpoint,
                settings.r2_bucket,
                settings.r2_region,
                settings.r2_use_ssl,
                settings.r2_upload_prefix)
    logger.info("R2 limits max_upload_bytes=%s download_timeout_sec=%s allow_hosts=%s",
                settings.r2_max_upload_bytes,
                settings.r2_download_timeout_sec,
                settings.r2_allow_hosts)

    if r2_configured and settings.r2_healthcheck_on_startup:
        try:
            r2 = R2Client(
                R2Config(
                    endpoint=settings.r2_endpoint or "",
                    access_key_id=settings.r2_access_key_id or "",
                    secret_access_key=settings.r2_secret_access_key or "",
                    bucket=settings.r2_bucket or "",
                    region=settings.r2_region,
                    use_ssl=settings.r2_use_ssl,
                    presign_expires_sec=settings.r2_presign_expires_sec,
                    upload_prefix=settings.r2_upload_prefix,
                    request_timeout_sec=settings.r2_healthcheck_timeout_sec,
                )
            )
            ok, err = r2.health_check()
            if ok:
                logger.info("R2 healthcheck: OK")
            else:
                logger.warning("R2 healthcheck failed: %s", err)
        except Exception as exc:
            logger.warning("R2 healthcheck error: %s", exc)


if __name__ == "__main__":
    main()
