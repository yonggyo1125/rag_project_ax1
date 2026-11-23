import json
import os
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from shared.logger import get_logger
from tools import ALL_TOOLS

logger = get_logger("agent")

TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}

SYSTEM_PROMPT = """제공된 도구(preprocess_text, convert_currency, get_weather)를 사용해 사용자의 요청에 답하세요.
- 도구 결과에 'error'가 있으면 추측하지 말고 오류 내용을 안내하세요.
"""


async def run_agent(query: str, max_steps: int = 6) -> dict:
    model_name = os.getenv("CHAT_MODEL", "gpt-4o-mini")
    model_provider = os.getenv("CHAT_MODEL_PROVIDER", "openai")

    llm = init_chat_model(
        model=model_name,
        model_provider=model_provider,
        temperature=0,
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    messages: list[BaseMessage] = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=query),
    ]
    executed_calls: list[dict] = []

    logger.info("[Agent] 시작 - model=%s (%s), query=%s", model_name, model_provider, query)

    for step in range(1, max_steps + 1):
        ai_msg = await llm_with_tools.ainvoke(messages)
        messages.append(ai_msg)

        tool_calls = getattr(ai_msg, "tool_calls", None) or []
        if not tool_calls:
            logger.info("[Agent] 완료 (step=%d) - 추가 tool_calls 없음", step)
            return {
                "answer": str(ai_msg.content),
                "tool_calls": executed_calls,
            }

        logger.info("[Agent] step=%d - %d개 tool_calls 요청됨", step, len(tool_calls))

        for call in tool_calls:
            tool_name = call["name"]
            tool_args = call["args"]
            tool_call_id = call["id"]

            logger.info("[ToolCall] id=%s, name=%s, args=%s", tool_call_id, tool_name, tool_args)
            selected_tool = TOOLS_BY_NAME.get(tool_name)

            if selected_tool is None:
                tool_result = {"error": f"등록되지 않은 도구입니다: {tool_name}"}
            else:
                tool_result = await selected_tool.ainvoke(tool_args)

            executed_calls.append({
                "step": step,
                "id": tool_call_id,
                "name": tool_name,
                "args": tool_args,
                "result": tool_result,
            })

            content_str = (
                tool_result
                if isinstance(tool_result, str)
                else json.dumps(tool_result, ensure_ascii=False, default=str)
            )
            messages.append(ToolMessage(content=content_str, tool_call_id=tool_call_id))

    logger.warning("[Agent] 최대 반복 횟수(%d) 도달", max_steps)
    return {
        "answer": "최대 도구 호출 횟수를 초과해 작업을 마무리하지 못했습니다.",
        "tool_calls": executed_calls,
    }