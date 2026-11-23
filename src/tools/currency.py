import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from shared.logger import get_logger

logger = get_logger("tools.currency")


class CurrencyInput(BaseModel):
    base: str = Field(..., min_length=3, max_length=3, description="기준 통화 (예: USD, JPY)")
    target: str = Field(default="KRW", min_length=3, max_length=3, description="대상 통화 (예: KRW)")
    amount: float = Field(default=1.0, gt=0, description="환산 금액")


@tool("convert_currency", args_schema=CurrencyInput)
async def convert_currency(base: str, target: str = "KRW", amount: float = 1.0) -> dict:
    """기준 통화 금액을 실시간 환율로 대상 통화 금액으로 환산합니다."""
    base_code = base.upper()
    target_code = target.upper()
    logger.info("[Tool:convert_currency] %s %s -> %s", amount, base_code, target_code)

    if base_code == target_code:
        return {"base": base_code, "target": target_code, "rate": 1.0, "amount": amount, "converted": amount}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(
                "https://api.frankfurter.dev/v1/latest",
                params={"from": base_code, "to": target_code},
            )
            res.raise_for_status()
            rate = res.json().get("rates", {}).get(target_code)

        if rate is None:
            return {"error": f"지원하지 않는 통화입니다: {base_code} -> {target_code}"}

        return {
            "base": base_code,
            "target": target_code,
            "rate": rate,
            "amount": amount,
            "converted": round(amount * rate, 2),
        }
    except httpx.HTTPError as exc:
        logger.warning("[Tool:convert_currency] API 오류: %s", exc)
        return {"error": f"환율 조회 실패: {exc}"}