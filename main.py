import logging
import os
import time
import traceback
import uuid

import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware, correlation_id
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from starlette.middleware import Middleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from browser.core.infra import Infra, init_global, init_logger
from browser.route.route import register_routes
from browser.server.server import BrowserServer
from browser.util.error import BusinessError, InternalError

VERSION = "1.0.0"
API_TITLE = "Browser Tools API"

# Initialize global configuration
init_global()

# Initialize the infra, This is a global instance that holds globally
# unique instance resources such as databases, configurations, models, etc.
infra = Infra()

middlewares = [
    Middleware(
        CorrelationIdMiddleware,
        header_name="X-Request-ID",
        generator=lambda: uuid.uuid4().hex,
        update_request_header=True,
        transformer=lambda x: x,
    ),
]

# Enable CORS
if infra.config.enable_cors:
    from starlette.middleware.cors import CORSMiddleware

    origins = ["*"]
    middlewares.append(
        Middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )
    )

app = FastAPI(
    title=API_TITLE,
    version=VERSION,
    debug=False,
    middleware=middlewares,
    on_startup=[
        lambda: init_logger(
            json_mode=infra.config.log_json_mode,
            level=logging.DEBUG if infra.config.verbose else logging.INFO,
        )
    ],
)


def custom_openapi():
    """
    Custom OpenAPI schema
    The reason we use custom_openapi instead of directly using FastAPI to define OpenAPI is that
    all API responses are currently 200 status codes (regardless of success or failure), and clients
    determine success based on the "success" field.
    As FastAPI cannot customize response status codes at the moment, we need to remove all responses
    with a 422 status code when generating the OpenAPI documentation.
    """
    openapi_schema = get_openapi(
        title=API_TITLE,
        version=VERSION,
        contact={"name": "mylxsw", "email": "mylxsw@aicode.cc"},
        routes=app.routes,
    )

    for _, method_item in openapi_schema.get("paths", {}).items():
        for _, param in method_item.items():
            responses = param.get("responses")
            # remove 422 response, also can remove other status code
            if "422" in responses:
                del responses["422"]

    return openapi_schema


app.openapi = custom_openapi


@app.middleware("http")
async def request_logger(request: Request, call_next):
    """
    Request logger middleware
    """
    response = None
    start_time = time.time()
    try:
        response = await call_next(request)
        return response
    except BaseException as e:
        if not isinstance(
            e,
            (
                StarletteHTTPException,
                RequestValidationError,
                BusinessError,
                InternalError,
            ),
        ):
            logging.error(
                f"request error: {repr(e)}, stacktrace: {traceback.format_exc()}",
                extra={
                    "user_id": request.headers.get("user-id"),
                    "org_id": request.headers.get("org-id"),
                },
            )

            return JSONResponse(
                content={"success": False, "message": "internal error"},
                status_code=200,
                headers={"X-Request-ID": correlation_id.get() or ""},
            )
        raise
    finally:
        status_code = response.status_code if response else "000"
        duration = (time.time() - start_time) * 1000  # convert to milliseconds
        logging.info(
            f"http_request [{status_code}] {request.method} {request.url} - {duration:.2f}ms",
            extra={
                "user_id": request.headers.get("user-id"),
                "org_id": request.headers.get("org-id"),
            },
        )


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc: StarletteHTTPException):
    if exc.status_code >= 500:
        logging.error(f"http error: {repr(exc)}, stacktrace: {traceback.format_exc()}")

    return JSONResponse(
        content={"success": False, "message": exc.detail},
        status_code=200,
        headers={"X-Request-ID": correlation_id.get() or ""},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    logging.warning(
        f"request validation error: {repr(exc)}, stacktrace: {traceback.format_exc()}"
    )
    return JSONResponse(
        content={"success": False, "message": "invalid request", "data": exc.errors()},
        status_code=200,
        headers={"X-Request-ID": correlation_id.get() or ""},
    )


@app.exception_handler(BusinessError)
async def business_exception_handler(request, exc: BusinessError):
    logging.warning(
        f"business error: {repr(exc)}, stacktrace: {traceback.format_exc()}"
    )

    return JSONResponse(
        content={"success": False, "message": exc.message, "code": exc.code},
        status_code=200,
        headers={"X-Request-ID": correlation_id.get() or ""},
    )


@app.exception_handler(InternalError)
async def custom_exception_handler(request, exc: InternalError):
    logging.error(f"internal error: {repr(exc)}, stacktrace: {traceback.format_exc()}")

    return JSONResponse(
        content={"success": False, "message": "internal error"},
        status_code=200,
        headers={"X-Request-ID": correlation_id.get() or ""},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logging.error(f"internal error: {repr(exc)}, stacktrace: {traceback.format_exc()}")

    return JSONResponse(
        content={"success": False, "message": "internal error"},
        status_code=200,
        headers={"X-Request-ID": correlation_id.get() or ""},
    )


# Register route
browser_server = BrowserServer(
    temp_path=os.path.join(infra.config.temp_path, "server"),
    zerox_model=infra.config.zerox_model,
    page_timeout=infra.config.page_timeout,
)
routers = register_routes(browser_server)
for router in routers:
    app.include_router(router)

logging.info("Browser Tools API started successfully.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, server_header=False)

