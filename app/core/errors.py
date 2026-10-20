import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 500
    code = "internal_error"
    default_message = "Error interno del servidor"

    def __init__(self, message: str | None = None, *, details: Any = None) -> None:
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)


class UnauthorizedError(AppError):
    status_code, code, default_message = 401, "unauthorized", "Credenciales inválidas o ausentes"


class ForbiddenError(AppError):
    status_code, code, default_message = 403, "forbidden", "No tiene permiso para esta operación"


class NotFoundError(AppError):
    status_code, code, default_message = 404, "not_found", "Recurso no encontrado"


class ConflictError(AppError):
    status_code, code, default_message = 409, "conflict", "Conflicto con el estado actual"


class BusinessRuleError(AppError):
    status_code, code, default_message = 422, "business_rule_violation", "Regla de negocio incumplida"


def _body(request: Request, code: str, message: str, details: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {
        "code": code,
        "message": message,
        "request_id": getattr(request.state, "request_id", None),
    }
    if details is not None:
        error["details"] = details
    return {"error": error}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            _body(request, exc.code, exc.message, exc.details), status_code=exc.status_code
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        # No se devuelve el valor recibido (podría ser dato personal o secreto).
        details = [
            {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()
        ]
        return JSONResponse(
            _body(request, "validation_error", "Datos de entrada inválidos", details),
            status_code=422,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            _body(request, f"http_{exc.status_code}", str(exc.detail)),
            status_code=exc.status_code,
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error no controlado", extra={"path": request.url.path})
        return JSONResponse(
            _body(request, "internal_error", "Error interno del servidor"), status_code=500
        )
