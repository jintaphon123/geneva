from __future__ import annotations

import argparse
import logging
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from src.geneva.web_api import (
    JsonApiResult,
    MAX_API_BODY_BYTES,
    REMOTE_BIND_OVERRIDE_ENV,
    GENEVA_REQUEST_HEADER,
    SseApiResult,
    WEB_ROOT,
    SessionManager,
    chat_request_from_payload,
    cors_headers,
    dispatch_api_request,
    is_bind_host_allowed,
    is_origin_allowed,
    json_bytes,
    parse_json_request_body,
    security_headers,
    research_request_from_payload,
    stream_sse_bytes,
    validate_request_security,
)

logger = logging.getLogger(__name__)


class GenevaRequestHandler(BaseHTTPRequestHandler):
    manager = SessionManager()
    server_version = "GenevaWeb/0.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_OPTIONS(self) -> None:
        failure = self._security_failure("OPTIONS")
        if failure is not None:
            self._send_json(failure.payload, status=failure.status)
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", f"Content-Type, Accept, {GENEVA_REQUEST_HEADER}")
        self.send_header("Cache-Control", "no-store")
        self._send_security_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api" or path.startswith("/api/"):
            failure = self._security_failure("GET")
            if failure is not None:
                self._send_json(failure.payload, status=failure.status)
                return
            try:
                self._send_api_result(dispatch_api_request(self.manager, "GET", path, parsed.query))
            except Exception as exc:
                self._send_json(
                    {"error": "Internal server error", "detail": str(exc)},
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )
            return
        failure = self._security_failure("GET")
        if failure is not None:
            self._send_json(failure.payload, status=failure.status)
            return
        self._serve_static(path)

    def do_POST(self) -> None:
        failure = self._security_failure("POST")
        if failure is not None:
            self._send_json(failure.payload, status=failure.status)
            return
        parsed = urlparse(self.path)
        payload, parse_error = parse_json_request_body(self._read_body())
        if parse_error is not None:
            self._send_json(parse_error, status=HTTPStatus.BAD_REQUEST)
            return
        try:
            self._send_api_result(dispatch_api_request(self.manager, "POST", parsed.path, parsed.query, payload))
        except Exception as exc:
            self._send_json(
                {"error": "Internal server error", "detail": str(exc)},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def do_PUT(self) -> None:
        failure = self._security_failure("PUT")
        if failure is not None:
            self._send_json(failure.payload, status=failure.status)
            return
        parsed = urlparse(self.path)
        payload, parse_error = parse_json_request_body(self._read_body())
        if parse_error is not None:
            self._send_json(parse_error, status=HTTPStatus.BAD_REQUEST)
            return
        try:
            self._send_api_result(dispatch_api_request(self.manager, "PUT", parsed.path, parsed.query, payload))
        except Exception as exc:
            self._send_json(
                {"error": "Internal server error", "detail": str(exc)},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def do_DELETE(self) -> None:
        failure = self._security_failure("DELETE")
        if failure is not None:
            self._send_json(failure.payload, status=failure.status)
            return
        parsed = urlparse(self.path)
        try:
            self._send_api_result(dispatch_api_request(self.manager, "DELETE", parsed.path, parsed.query, {}))
        except Exception as exc:
            self._send_json(
                {"error": "Internal server error", "detail": str(exc)},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def _read_body(self) -> bytes:
        try:
            length = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError:
            length = 0
        return self.rfile.read(length) if length > 0 else b""

    def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._send_security_headers()
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_api_result(self, result: JsonApiResult | SseApiResult) -> None:
        if isinstance(result, JsonApiResult):
            self._send_json(result.payload, result.status)
            return
        self._send_sse_result(result)

    def _send_sse_result(self, result: SseApiResult) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self._send_security_headers()
        self._send_cors_headers()
        self.end_headers()
        try:
            for frame in stream_sse_bytes(self.manager, result):
                self.wfile.write(frame)
                self.wfile.flush()
        except BrokenPipeError:
            return

    def _serve_static(self, path: str) -> None:
        if path in {"", "/"}:
            path = "/index.html"
        relative = Path(unquote(path.lstrip("/")))
        target = (WEB_ROOT / relative).resolve()
        try:
            target.relative_to(WEB_ROOT.resolve())
        except ValueError:
            self._send_json({"error": "Forbidden"}, status=HTTPStatus.FORBIDDEN)
            return
        if not target.exists() or not target.is_file():
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return
        body = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _origin_allowed(self) -> bool:
        return is_origin_allowed(self.headers.get("Origin"))

    def _send_cors_headers(self) -> None:
        for name, value in cors_headers(self.headers.get("Origin")).items():
            self.send_header(name, value)

    def _send_security_headers(self) -> None:
        for name, value in security_headers().items():
            self.send_header(name, value)

    def _security_failure(self, method: str):
        auth = self.headers.get("X-Geneva-Auth") or self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            auth = auth[len("Bearer "):]
        return validate_request_security(
            method,
            origin=self.headers.get("Origin"),
            host=self.headers.get("Host"),
            content_type=self.headers.get("Content-Type"),
            content_length=self._content_length(),
            client_host=self.client_address[0] if self.client_address else None,
            geneva_header=self.headers.get(GENEVA_REQUEST_HEADER),
            auth_token=auth or None,
        )

    def _content_length(self) -> int:
        try:
            return max(0, int(self.headers.get("Content-Length", "0") or 0))
        except ValueError:
            return MAX_API_BODY_BYTES + 1


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    from .web_security import install_secret_log_filter
    install_secret_log_filter()
    if not is_bind_host_allowed(host):
        raise ValueError(
            f"Refusing to bind Geneva web UI to non-loopback host {host!r}. "
            f"Set {REMOTE_BIND_OVERRIDE_ENV}=1 only for an explicitly secured deployment."
        )
    server = ThreadingHTTPServer((host, port), GenevaRequestHandler)
    logger.info("Geneva web UI running at http://%s:%s", host, port)
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Geneva web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
