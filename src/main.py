from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel, Field
from agent import run_agent
from shared.exception_handlers import register_exception_handlers
from shared.logger import get_logger
from shared.schemas import APIResponse

logger = get_logger("main")


app = FastAPI(title="도구 연동 실습")
register_exception_handlers(app)


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, description="질문 또는 요청")


@app.post("/v1/ask", response_model=APIResponse[dict])
async def ask(req: AskRequest):
    result = await run_agent(req.query)
    return APIResponse.ok(data=result)