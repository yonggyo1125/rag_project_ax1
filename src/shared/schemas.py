from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = Field(description="처리 성공/실패 여부")
    code: str | None = Field(None, description="응답 코드")
    message: str | None = Field(None, description="설명 메시지")
    errors: Any | None = Field(None, description="오류 상세")
    data: T | None = Field(None, description="응답 데이터")
    responded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="응답 시각(UTC)",
    )

    @classmethod
    def ok(cls, data: T | None = None, message: str = "성공", code: str = "OK") -> "APIResponse[T]":
        return cls(success=True, code=code, message=message, errors=None, data=data)

    @classmethod
    def fail(cls, message: str, code: str = "BAD_REQUEST", errors: Any | None = None) -> "APIResponse[None]":
        return cls(success=False, code=code, message=message, errors=errors, data=None)