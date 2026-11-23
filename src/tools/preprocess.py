import re
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from shared.logger import get_logger

logger = get_logger("tools.preprocess")


class PreprocessInput(BaseModel):
    text: str = Field(..., min_length=1, description="정리할 원본 텍스트")
    to_lower: bool = Field(default=False, description="소문자 변환 여부")


@tool("preprocess_text", args_schema=PreprocessInput)
def preprocess_text(text: str, to_lower: bool = False) -> dict:
    """연속된 공백/줄바꿈을 정리하고 글자 수와 단어 수를 반환합니다."""
    logger.info("[Tool:preprocess_text] to_lower=%s", to_lower)
    cleaned = re.sub(r"\s+", " ", text).strip()
    if to_lower:
        cleaned = cleaned.lower()
    return {
        "cleaned_text": cleaned,
        "char_count": len(cleaned),
        "word_count": len(cleaned.split(" ")) if cleaned else 0,
    }