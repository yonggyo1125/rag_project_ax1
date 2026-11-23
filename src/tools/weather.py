import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from shared.logger import get_logger

logger = get_logger("tools.weather")


class WeatherInput(BaseModel):
    city: str = Field(..., min_length=1, description="도시명 (예: Seoul, Incheon, Tokyo)")


@tool("get_weather", args_schema=WeatherInput)
async def get_weather(city: str) -> dict:
    """도시의 현재 기온(℃)과 풍속(km/h)을 조회합니다."""
    logger.info("[Tool:get_weather] city=%s", city)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            geo = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "ko"},
            )
            geo.raise_for_status()
            places = geo.json().get("results") or []
            if not places:
                return {"error": f"'{city}' 도시를 찾을 수 없습니다."}

            place = places[0]
            weather = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "current_weather": True,
                },
            )
            weather.raise_for_status()
            current = weather.json().get("current_weather", {})

        return {
            "city": place.get("name", city),
            "temperature_c": current.get("temperature"),
            "windspeed_kmh": current.get("windspeed"),
            "weather_code": current.get("weathercode"),
        }
    except httpx.HTTPError as exc:
        logger.warning("[Tool:get_weather] API 오류: %s", exc)
        return {"error": f"날씨 조회 실패: {exc}"}