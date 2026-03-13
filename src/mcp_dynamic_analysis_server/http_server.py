from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, Optional


class MCPHTTPHandler(BaseHTTPRequestHandler):
    server_version = "MCPDynamicAnalysisHTTP/0.1"

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if self.path == "/":
            self._send_json(200, {"name": "dynamic-analysis-mcp", "status": "running"})
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/mcp":
            self._send_json(404, {"error": "Not found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b""

        try:
            message = json.loads(raw.decode("utf-8")) if raw else None
        except json.JSONDecodeError:
            self._send_json(400, {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}})
            return

        if message is None:
            self._send_json(400, {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}})
            return

        handler: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]] = self.server.handle_message  # type: ignore[attr-defined]
        response = handler(message)

        if response is None:
            self.send_response(204)
            self.end_headers()
            return

        self._send_json(200, response)

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class MCPHTTPServer(HTTPServer):
    def __init__(self, server_address: tuple[str, int], handler: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]):
        super().__init__(server_address, MCPHTTPHandler)
        self.handle_message = handler


def run_http(handler: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]], host: str, port: int) -> None:
    server = MCPHTTPServer((host, port), handler)
    server.serve_forever()
