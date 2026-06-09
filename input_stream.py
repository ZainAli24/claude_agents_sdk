# // Author: Zain Ali
import sys
sys.stdout.reconfigure(encoding="utf-8")

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)
import asyncio


async def streaming_analysis():
    async def message_generator():
        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": "I am learning Python. My favorite number is 42 and my pet's name is Bruno.",
            },
        }

        await asyncio.sleep(2)

        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": "What am I learning? What is my favorite number? What is my pet's name?",
            },
        }

    options = ClaudeAgentOptions(max_turns=10, allowed_tools=["Read", "Grep"])

    async with ClaudeSDKClient(options) as client:
        await client.query(message_generator())

        # FIX: receive_response() sirf ek ResultMessage tak sunti hai.
        # Multiple yields ke liye loop mein chalao with timeout.
        # Official repo pattern: examples/streaming_mode.py -> example_async_iterable_prompt()
        turn = 0
        while True:

            try:
                async with asyncio.timeout(30.0):
                    async for message in client.receive_response():
                        if isinstance(message, AssistantMessage):
                            for block in message.content:
                                if isinstance(block, TextBlock):
                                    print(f"\n[Turn {turn + 1}] Claude: {block.text}")
                        elif isinstance(message, ResultMessage):
                            turn += 1
                            print(f"\n--- Turn {turn} complete ---")
            except (asyncio.TimeoutError, StopAsyncIteration):
                break


asyncio.run(streaming_analysis())
