from typing import Any
import asyncio
import httpx
from claude_agent_sdk import tool, create_sdk_mcp_server, query, ClaudeAgentOptions, ResultMessage


@tool(
    "get_weather",
    "Fetches the current weather for a given city name. Call this whenever the user asks about weather.",
    {"cityName": str},
)
async def get_weather(args: dict[str, Any]) -> dict[str, Any]:
    try:
        city = args["cityName"]
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://wttr.in/{city.lower()}?format=%C+%t"
            )

            if response.status_code != 200:
                return {
                    "content": [{"type": "text", "text": f"Weather API error: {response.status_code}"}],
                    "is_error": True,
                }

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Weather in {city}: {response.text.strip()}",
                }
            ]
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Failed to fetch weather: {str(e)}"}],
            "is_error": True,
        }


weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[get_weather],
)


async def main():
    options = ClaudeAgentOptions(
        mcp_servers={"weather": weather_server},
        allowed_tools=["mcp__weather__get_weather"],
    )

    async for message in query(
        prompt="What's the weather in Karachi?",
        options=options,
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(message.result)


asyncio.run(main())


