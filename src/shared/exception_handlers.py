from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from shared.logger import get_logger
from shared.schemas import APIResponse

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors_map: dict[str, list[str]] = {}
        for err in exc.errors():
            loc = ".".join(str(item) for item in err["loc"] if item != "body") or "non_field_errors"
            errors_map.setdefault(loc, []).append(err["msg"])

        logger.warning("입력 검증 실패 (%s): %s", request.url.path, errors_map)
        body = APIResponse.fail(
            code="REQUEST_VALIDATION_ERROR",
            message="요청 파라미터 검증에 실패했습니다.",
            errors=errors_map,
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=body.model_dump(mode="json"))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("미처리 서버 오류 (%s): %s", request.url.path, exc)
        body = APIResponse.fail(
            code="INTERNAL_SERVER_ERROR",
            message="서버 내부 오류가 발생했습니다.",
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body.model_dump(mode="json"))