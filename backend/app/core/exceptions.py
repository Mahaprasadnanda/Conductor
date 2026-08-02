from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.logger import log

class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

async def app_exception_handler(request: Request, exc: AppException):
    log.error("app_exception", status_code=exc.status_code, detail=exc.detail, path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
from app.gateway.exceptions import GatewayException

async def gateway_exception_handler(request: Request, exc: GatewayException):
    log.error("gateway_exception", status_code=exc.status_code, message=exc.message, path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )

async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", detail=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
