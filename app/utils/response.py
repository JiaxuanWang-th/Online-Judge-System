"""Unified API response helpers."""

from typing import Any

from fastapi.responses import JSONResponse


def success(
    data: Any = None,
    message: str = "ok",
    code: int = 200,
) -> JSONResponse:
    return JSONResponse(
        status_code=code,
        content={"code": code, "message": message, "data": data},
    )


def error(
    message: str,
    code: int = 400,
    data: Any = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=code,
        content={"code": code, "message": message, "data": data},
    )
