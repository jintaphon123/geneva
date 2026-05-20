from typing import Any

from src.geneva.web_api import (
    JsonApiResult,
    MAX_API_BODY_BYTES,
    GENEVA_REQUEST_HEADER,
    SseApiResult,
    WEB_ROOT,
    SessionManager,
    cors_headers,
    dispatch_api_request,
    parse_json_request_body,
    security_headers,
    stream_sse_bytes,
    validate_request_security,
)


def create_app() -> Any:
    try:
        from fastapi import FastAPI, Request, Response
        from fastapi.responses import JSONResponse, StreamingResponse
        from fastapi.staticfiles import StaticFiles
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install fastapi and uvicorn to use create_app().") from exc

    manager = SessionManager()
    app = FastAPI(title="Geneva", version="0.1.0")

    @app.middleware("http")
    async def local_origin_guard(request: Request, call_next):
        origin = request.headers.get("origin")
        failure = validate_request_security(
            request.method,
            origin=origin,
            host=request.headers.get("host"),
            content_type=request.headers.get("content-type"),
            content_length=_content_length(request.headers.get("content-length")),
            client_host=request.client.host if request.client else None,
            geneva_header=request.headers.get(GENEVA_REQUEST_HEADER),
        )
        if failure is not None:
            return JSONResponse(failure.payload, status_code=int(failure.status), headers=security_headers())
        response = await call_next(request)
        for name, value in security_headers().items():
            response.headers[name] = value
        for name, value in cors_headers(origin).items():
            response.headers[name] = value
        return response

    @app.api_route("/api", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    @app.api_route("/api/{api_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    async def api_gateway(request: Request, api_path: str = ""):
        origin = request.headers.get("origin")
        if request.method == "OPTIONS":
            headers = {
                **cors_headers(origin),
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": f"Content-Type, Accept, {GENEVA_REQUEST_HEADER}",
                "Cache-Control": "no-store",
                **security_headers(),
            }
            return Response(status_code=204, headers=headers)

        payload: dict[str, Any] | None = None
        if request.method in {"POST", "PUT"}:
            payload, parse_error = parse_json_request_body(await request.body())
            if parse_error is not None:
                return JSONResponse(parse_error, status_code=400)

        result = dispatch_api_request(
            manager,
            request.method,
            f"/api/{api_path}".rstrip("/") if api_path else "/api",
            request.url.query,
            payload,
        )
        return _fastapi_response(manager, result)

    app.mount("/", StaticFiles(directory=str(WEB_ROOT), html=True), name="web")
    return app


def _fastapi_response(manager: SessionManager, result: JsonApiResult | SseApiResult):
    try:
        from fastapi.responses import JSONResponse, StreamingResponse
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install fastapi and uvicorn to use create_app().") from exc

    if isinstance(result, JsonApiResult):
        return JSONResponse(result.payload, status_code=int(result.status))
    return StreamingResponse(stream_sse_bytes(manager, result), media_type="text/event-stream")


def _content_length(value: str | None) -> int:
    try:
        return max(0, int(value or 0))
    except ValueError:
        return MAX_API_BODY_BYTES + 1
