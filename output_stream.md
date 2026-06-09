# Output Streaming - Poori Samajh
> Claude Agent SDK mein Output Streaming ka complete guide (Python Beginner ke liye)

---

## 1. Streaming Kya Hoti Hai? (Simple Words Mein)

Soch lo tum ChatGPT use karte ho - words **ek ek karke aate hain**, poora jawab aik saath nahi aata. **Yahi streaming hai.**

```
Normal (Without Streaming):   Claude sochta hai... sochta hai... sochta hai... [POORA TEXT AATA HAI]
Streaming (With Streaming):   Claude "Ye" "ek" "example" "hai" [WORD BY WORD AATA HAI]
```

**Agent SDK mein by default** - poora message **khatam hone ke baad** milta hai.
**Streaming enable karo** - toh words **real-time mein** milte hain.

---

## 2. Streaming Kaise Enable Karein?

Sirf ek option lagana hai: `include_partial_messages=True`

```python
# // Author: Zain Ali
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import StreamEvent
import asyncio

async def stream_response():
    options = ClaudeAgentOptions(
        include_partial_messages=True,  # <-- YEH LAGAO - streaming on ho jaayegi
        allowed_tools=["Bash", "Read"],
    )

    async for message in query(prompt="Mere project mein kya files hain?", options=options):
        if isinstance(message, StreamEvent):       # 1. Check karo: kya yeh StreamEvent hai?
            event = message.event
            if event.get("type") == "content_block_delta":   # 2. Kya yeh text chunk hai?
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":        # 3. Kya yeh text hai (tool nahi)?
                    print(delta.get("text", ""), end="", flush=True)  # Print karo!

asyncio.run(stream_response())
```

**3 Checks Yaad Rakho:**
1. `isinstance(message, StreamEvent)` → Kya streaming event hai?
2. `type == "content_block_delta"` → Kya text ka tukda (chunk) aa raha hai?
3. `delta.type == "text_delta"` → Kya yeh text hai (tool input nahi)?

---

## 3. StreamEvent Kya Hota Hai?

Jab streaming on hoti hai, toh normal `AssistantMessage` ke saath **`StreamEvent` bhi aata hai** - yeh raw events hote hain.

```python
# StreamEvent ka structure:
@dataclass
class StreamEvent:
    uuid: str            # Har event ka unique ID
    session_id: str      # Session ka ID
    event: dict          # <-- YEH IMPORTANT HAI - actual raw event
    parent_tool_use_id: str | None  # Agar subagent se aaya toh
```

**`event` field ke andar kya hota hai?**

| Event Type            | Matlab                                     |
| :-------------------- | :----------------------------------------- |
| `message_start`       | Naya message shuru hua                     |
| `content_block_start` | Naya block shuru hua (text ya tool)        |
| `content_block_delta` | Chunk aa raha hai (text ya tool input)     |
| `content_block_stop`  | Block khatam hua                           |
| `message_delta`       | Message level update (stop reason, usage)  |
| `message_stop`        | Poora message khatam                       |

---

## 4. Message Flow - Sequence Mein Kya Aata Hai?

```
StreamEvent (message_start)          <- Message shuru
StreamEvent (content_block_start)    <- Text block shuru
StreamEvent (content_block_delta)    <- "Ye"
StreamEvent (content_block_delta)    <- " ek"
StreamEvent (content_block_delta)    <- " example"
StreamEvent (content_block_stop)     <- Text block khatam

StreamEvent (content_block_start)    <- Tool call shuru (Bash, Read, etc.)
StreamEvent (content_block_delta)    <- Tool ka input aa raha hai
StreamEvent (content_block_stop)     <- Tool call khatam

StreamEvent (message_delta)          <- Stop reason
StreamEvent (message_stop)           <- Message khatam

AssistantMessage                     <- POORA complete message (ek saath)
... tool execute hota hai ...
ResultMessage                        <- Final result
```

**Without Streaming** (jab `include_partial_messages=False` ho):
- `StreamEvent` nahi aata
- Sirf milta hai: `SystemMessage`, `AssistantMessage`, `ResultMessage`

---

## 5. Text Streaming - Sirf Text Print Karo

```python
# // Author: Zain Ali
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import StreamEvent
import asyncio

async def stream_text():
    options = ClaudeAgentOptions(include_partial_messages=True)

    async for message in query(prompt="Database kya hota hai samjhao", options=options):
        if isinstance(message, StreamEvent):
            event = message.event
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    # Har chunk turant print karo
                    print(delta.get("text", ""), end="", flush=True)

    print()  # End mein naya line

asyncio.run(stream_text())
```

**`end=""` aur `flush=True` kyon?**
- `end=""` → print ke baad naya line mat lagao (sab ek line mein aaye)
- `flush=True` → buffer wait mat karo, turant screen pe dikhao

---

## 6. Tool Calls Streaming - Tool ka Input Dekho

```python
# // Author: Zain Ali
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import StreamEvent
import asyncio

async def stream_tool_calls():
    options = ClaudeAgentOptions(
        include_partial_messages=True,
        allowed_tools=["Read", "Bash"],
    )

    current_tool = None   # Kaunsa tool chal raha hai
    tool_input = ""       # Tool ka input collect karo

    async for message in query(prompt="README.md file padho", options=options):
        if isinstance(message, StreamEvent):
            event = message.event
            event_type = event.get("type")

            if event_type == "content_block_start":
                # Tool shuru ho raha hai
                content_block = event.get("content_block", {})
                if content_block.get("type") == "tool_use":
                    current_tool = content_block.get("name")
                    tool_input = ""
                    print(f"Tool shuru: {current_tool}")

            elif event_type == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "input_json_delta":
                    # Tool ka JSON input aa raha hai piece by piece
                    chunk = delta.get("partial_json", "")
                    tool_input += chunk
                    print(f"  Input aaya: {chunk}")

            elif event_type == "content_block_stop":
                # Tool khatam hua
                if current_tool:
                    print(f"Tool {current_tool} complete. Input: {tool_input}")
                    current_tool = None

asyncio.run(stream_tool_calls())
```

**3 Important Events Tool Ke Liye:**

| Event | Matlab |
| :---- | :----- |
| `content_block_start` + `tool_use` | Tool shuru hua |
| `content_block_delta` + `input_json_delta` | Tool ka input aa raha hai |
| `content_block_stop` | Tool khatam hua |

---

## 7. Streaming UI - Real Chat Interface Jaisi

Yeh sabse practical example hai - jaise ChatGPT ka interface:

```python
# // Author: Zain Ali
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage
from claude_agent_sdk.types import StreamEvent
import asyncio
import sys

async def streaming_ui():
    options = ClaudeAgentOptions(
        include_partial_messages=True,
        allowed_tools=["Read", "Bash", "Grep"],
    )

    in_tool = False  # Kya abhi tool chal raha hai?

    async for message in query(
        prompt="Codebase mein saare TODO comments dhundo", options=options
    ):
        if isinstance(message, StreamEvent):
            event = message.event
            event_type = event.get("type")

            if event_type == "content_block_start":
                content_block = event.get("content_block", {})
                if content_block.get("type") == "tool_use":
                    tool_name = content_block.get("name")
                    print(f"\n[{tool_name} use kar raha hun...]", end="", flush=True)
                    in_tool = True  # Tool mode on

            elif event_type == "content_block_delta":
                delta = event.get("delta", {})
                # Text sirf tab dikhao jab tool nahi chal raha
                if delta.get("type") == "text_delta" and not in_tool:
                    sys.stdout.write(delta.get("text", ""))
                    sys.stdout.flush()

            elif event_type == "content_block_stop":
                if in_tool:
                    print(" ho gaya!", flush=True)
                    in_tool = False  # Tool mode off

        elif isinstance(message, ResultMessage):
            print(f"\n\n--- Kaam Mukammal ---")

asyncio.run(streaming_ui())
```

**Output kuch aisa dikhega:**
```
[Read use kar raha hun...] ho gaya!
[Bash use kar raha hun...] ho gaya!
Maine in files mein TODO comments dhunde:
- main.py line 45: TODO: error handling
- utils.py line 12: TODO: refactor

--- Kaam Mukammal ---
```

---

## 8. Important Limitation

**Structured Output stream nahi hoti!**

Agar tum `structured_output` use karo (JSON result), toh woh streaming mein nahi milti - sirf **final `ResultMessage`** mein milti hai.

---

## Quick Summary Table

| Feature                | Kaise Karein                                      |
| :--------------------- | :------------------------------------------------ |
| Streaming on karein    | `include_partial_messages=True`                   |
| Text chunks pakdo      | `content_block_delta` + `text_delta`              |
| Tool start pakdo       | `content_block_start` + `tool_use`                |
| Tool input pakdo       | `content_block_delta` + `input_json_delta`        |
| Tool khatam pakdo      | `content_block_stop`                              |
| Final result pakdo     | `ResultMessage`                                   |

---

## Next Steps (Aage Kya Seekhein)

- **Interactive vs One-shot queries** - Input modes ka farq
- **Structured Outputs** - Typed JSON responses
- **Permissions** - Tools ka control

> Reference: https://code.claude.com/docs/en/agent-sdk/streaming-output

---

## Alag Tools Ke Alag Inputs

```
┌───────┬──────────────────────────────────────────────┐
│ Tool  │                Input Example                 │
├───────┼──────────────────────────────────────────────┤
│ Read  │ {"file_path": "main.py"}                     │
├───────┼──────────────────────────────────────────────┤
│ Bash  │ {"command": "ls -la"}                        │
├───────┼──────────────────────────────────────────────┤
│ Write │ {"file_path": "test.py", "content": "hello"} │
├───────┼──────────────────────────────────────────────┤
│ Grep  │ {"pattern": "TODO", "path": "."}             │
└───────┴──────────────────────────────────────────────┘
```

Har tool ka input alag hota hai - Agent khud decide karta hai kya input dena hai context ke hisaab se.
