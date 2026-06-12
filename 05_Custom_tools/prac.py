from claude_agent_sdk import create_sdk_mcp_server, query, ResultMessage, tool, ClaudeAgentOptions
import httpx
import asyncio
from typing import Any
from pydantic import BaseModel


class ResultFormate(BaseModel):
    city: str
    condition: str
    temperature: str


@tool(
    "get_weather_info",
    "Fetch the current weather for a given city name",
    {"cityName": str}
)
async def get_weather_info(args: dict[str, Any]) -> dict[str, Any]:
    try:
        cityName = args["cityName"]

        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://wttr.in/{cityName.lower()}?format=%C+%t")

            if response.status_code != 200:
                return {
                    "content": [
                        {
                        "type": "text",
                        "text": f"Something went wrong: {response.status_code}"
                    }   
                ],
                "is_error": True
            }
            
        return {
            "content": [
                {"type": "text", "text": f"Weather is {response.text.strip()}"}
            ]
        }
    
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Something wrong check url, {e}",
                },
            ],
            "is_error": True
        }


weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[get_weather_info]
)


async def main():
    options = ClaudeAgentOptions(mcp_servers={"weather": weather_server}, allowed_tools=["mcp__weather__get_weather_info"], output_format={"type": "json_schema", "schema": ResultFormate.model_json_schema()})
    async for message in query(
        options= options,
        prompt="What`s the weather in Gujar Khan, Pakistan!",
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success" and message.structured_output:
            report = ResultFormate.model_validate(message.structured_output)

            print(f"\n\nCity: {report.city}")
            print(f"Condition: {report.condition}")
            print(f"Temperature: {report.temperature}\n\n")



asyncio.run(main())