# Claude Agent SDK — Python Quickstart Notes

> Yeh file meri personal revision notes hain. Claude Agent SDK ka Python code line by line samjhaya gaya hai.

---

## Project Setup (Windows)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install claude-agent-sdk
```

`.env` file banao aur API key daalo:
```
ANTHROPIC_API_KEY=your-api-key-here
```

---

## Quickstart: Buggy File (`utils.py`)

```python
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)   # BUG: empty list pe ZeroDivisionError


def get_user_name(user):
    return user["name"].upper()   # BUG: user=None pe TypeError
```

---

## Agent Code (`agent.py`) — Full Example

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage


async def main():
    async for message in query(
        prompt="Review utils.py for bugs that would cause crashes. Fix any issues you find.",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Glob"],
            permission_mode="acceptEdits",
        ),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)
                elif hasattr(block, "name"):
                    print(f"Tool: {block.name}")
        elif isinstance(message, ResultMessage):
            print(f"Done: {message.subtype}")


asyncio.run(main())
```

**Chalane ka command:**
```bash
python agent.py
```

---

## Line-by-Line Explanation

### `import asyncio`

Python normally ek kaam karta hai phir doosra — yeh **synchronous** hai.
`asyncio` se code **bina rukay** multiple kaam manage kar sakta hai.

**Real life example:** Tune delivery order kiya. Synchronous mein delivery tak sirf betha rehta.
Asyncio mein delivery wait ke dauran TV bhi dekh sakte ho.

Claude SDK asyncio isliye use karta hai kyunki Claude server se messages **slowly stream** hote hain — hum wait karne ki bajaye dusra kaam kar sakte hain.

---

### `from claude_agent_sdk import ...`

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage
```

| Import | Kya hai |
|---|---|
| `query` | Main function — agent ko start karta hai |
| `ClaudeAgentOptions` | Settings/config ka object |
| `AssistantMessage` | Claude ke jawab ka message type |
| `ResultMessage` | Task khatam hone ka message type |

---

### `async def main():`

```python
async def main():
```

- `def` = function banana
- `async def` = woh function jo asyncio ke saath kaam kare

**Rule:** Agar function ke andar `await` ya `async for` use karna ho, tab `async def` ZAROOR likhna hai.

```python
# Galat — normal def mein async nahi chalta
def main():
    async for ...  # ERROR!

# Sahi
async def main():
    async for ...  # OK
```

---

### `query()` — SDK ka Dil

```python
async for message in query(
    prompt="...",
    options=ClaudeAgentOptions(...),
):
```

`query()` ek **Async Generator** hai — ek machine jo ek ek message produce karta rehta hai.

**Internally kya hota hai:**
```
Tera prompt → Claude API ko bheja
Claude socha → SDK ne Read tool chalaya → result wapas Claude ko diya
Claude socha → SDK ne Edit tool chalaya → result wapas Claude ko diya
Claude socha → "Kaam hogaya" → ResultMessage bheja
LOOP KHATAM
```

Tu sirf `async for` likh — SDK baaki sab handle karta hai (tools chalana, retry, context).

---

### `prompt=` Parameter

```python
prompt="Review utils.py for bugs that would cause crashes. Fix any issues you find."
```

Yeh woh instruction hai jo Claude ko diya jata hai. Claude khud decide karta hai:
- Konsa tool use karun?
- Kaunsi file padun?
- Kya fix karun?

---

### `ClaudeAgentOptions(...)` — Settings Object

```python
options=ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Glob"],
    permission_mode="acceptEdits",
)
```

**`ClaudeAgentOptions`** ek Python class hai. Iska object banake settings dete hain.

#### `allowed_tools` — Konse Tools Dene Hain Claude Ko

```python
allowed_tools=["Read", "Edit", "Glob"]
```

| Tool | Kya karta hai |
|---|---|
| `"Read"` | Files padh sakta hai |
| `"Edit"` | Files edit kar sakta hai |
| `"Glob"` | File patterns dhundh sakta hai (`*.py`) |
| `"Grep"` | Text dhundh sakta hai files mein |
| `"Bash"` | Terminal commands chala sakta hai |
| `"WebSearch"` | Internet search kar sakta hai |

**Combinations aur unka effect:**

| Tools | Agent kya kar sakta hai |
|---|---|
| `Read`, `Glob`, `Grep` | Sirf padh sakta hai, edit nahi |
| `Read`, `Edit`, `Glob` | Padh aur edit kar sakta hai |
| `Read`, `Edit`, `Bash`, `Glob`, `Grep` | Full automation |

#### `permission_mode` — Kitni Permission Deni Hai

```python
permission_mode="acceptEdits"
```

| Mode | Kya karta hai | Kab use karo |
|---|---|---|
| `"acceptEdits"` | File edits auto-approve | Normal development |
| `"dontAsk"` | Sirf `allowed_tools` use kare | Locked-down agents |
| `"bypassPermissions"` | Sab kuch bina poochhe | CI/CD pipelines |
| `"default"` | Har cheez ke liye poochhe | Custom approval flows |

---

### `async for message in query(...):`

```python
async for message in query(...):
```

- Normal `for` = synchronous lists ke liye
- `async for` = streaming/async generators ke liye

Yeh loop tab tak chalta rehta hai jab tak Claude kaam karta rehta hai.

**Messages ka flow:**
```
Iteration 1: AssistantMessage → "utils.py padh raha hun..."
Iteration 2: AssistantMessage → Tool: Read
Iteration 3: AssistantMessage → "bug mila, edit kar raha hun..."
Iteration 4: AssistantMessage → Tool: Edit
Iteration 5: ResultMessage    → "Done: success"
LOOP KHATAM
```

---

### `isinstance()` — Message Type Check

```python
if isinstance(message, AssistantMessage):
    ...
elif isinstance(message, ResultMessage):
    ...
```

`isinstance(message, AssistantMessage)` — "Kya yeh message object AssistantMessage class ka hai?"

**Kyun zaroor hai?** `query()` alag alag types ke messages bhejta hai. Bina filter ke sab kuch print hoga — noisy. Filter lagake sirf jo chahiye woh print karo.

---

### `AssistantMessage` ke Andar — Blocks

```python
if isinstance(message, AssistantMessage):
    for block in message.content:         # content ek list hai
        if hasattr(block, "text"):         # text block?
            print(block.text)
        elif hasattr(block, "name"):       # tool use block?
            print(f"Tool: {block.name}")
```

`message.content` ek **list** hai — ek message ke andar multiple blocks ho sakte hain.

**`hasattr(block, "text")`** — "Kya is block mein `.text` attribute hai?"

#### Block Type 1: Text Block
```python
if hasattr(block, "text"):
    print(block.text)
```
Output example:
```
I'll start by reading utils.py to understand the code structure...
I found a division by zero bug in calculate_average...
```

#### Block Type 2: Tool Use Block
```python
elif hasattr(block, "name"):
    print(f"Tool: {block.name}")
```
Output example:
```
Tool: Read
Tool: Edit
```

---

### `ResultMessage` — Task Complete Signal

```python
elif isinstance(message, ResultMessage):
    print(f"Done: {message.subtype}")
```

Jab Claude kaam poora karta hai yeh message aata hai.

`message.subtype` ki values:
- `"success"` — kaam ho gaya
- `"error"` — koi error aayi

**F-string kya hai?**
```python
# f-string — string ke andar variable seedha {} mein dalo
name = "Zain"
print(f"Hello {name}")   # Hello Zain
print("Hello " + name)   # Same result, purana tarika
```

---

### `asyncio.run(main())` — Async Function Chalao

```python
asyncio.run(main())
```

`async def main()` ko directly call nahi kar sakte:
```python
main()           # GALAT — sirf coroutine object banaega, chalega nahi
asyncio.run(main())  # SAHI — asyncio event loop start karke actually chalata hai
```

**Simple analogy:** `async def` ek recipe hai. `asyncio.run()` woh stove hai jis par recipe pakti hai.

---

## Pura Internal Flow

```
Tu likhe: asyncio.run(main())
    |
    v
asyncio event loop start hota hai
    |
    v
query() call hota hai — Claude Code process start hoti hai background mein
    |
    v
Tu ne kaha: "Review utils.py for bugs..."
    |
    v
Claude socha → SDK ne Read tool chalaya → utils.py pada
    |
    v
AssistantMessage aya → print(block.text) → Claude ki soch dikhti hai
    |
    v
Claude socha → SDK ne Edit tool chalaya → file fix ki
    |
    v
AssistantMessage aya → print(f"Tool: {block.name}") → "Tool: Edit"
    |
    v
Claude bola "kaam ho gaya" → ResultMessage aya → "Done: success"
    |
    v
Loop khatam → asyncio.run() return → program end
```

---

## Agent Ko Customize Karna

### Web Search Add Karo

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Glob", "WebSearch"],
    permission_mode="acceptEdits",
)
```

### Custom System Prompt Do

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Glob"],
    permission_mode="acceptEdits",
    system_prompt="You are a senior Python developer. Always follow PEP 8 style guidelines.",
)
```

### Terminal Commands Bhi Chalao

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Glob", "Bash"],
    permission_mode="acceptEdits",
)
# Prompt try karo: "Write unit tests for utils.py, run them, and fix any failures"
```

---

## Quick Reference — Har Cheez Ek Jagah

| Code | Matlab |
|---|---|
| `import asyncio` | Async programming ka module |
| `async def main()` | Async function banana |
| `query(prompt=..., options=...)` | Agent start karo |
| `ClaudeAgentOptions(...)` | Agent ki settings |
| `allowed_tools=[...]` | Claude kaunse tools use kar sakta hai |
| `permission_mode="acceptEdits"` | File edits auto-approve |
| `async for message in query(...)` | Streaming messages receive karo |
| `isinstance(message, AssistantMessage)` | Message ka type check karo |
| `message.content` | Message ke blocks ki list |
| `hasattr(block, "text")` | Block mein text attribute hai? |
| `hasattr(block, "name")` | Block mein tool name hai? |
| `ResultMessage` | Task khatam ka signal |
| `asyncio.run(main())` | Async function ko actually chalao |

---

## Next Steps (Seekhne Ka Order)

1. **Permissions** — agent ko kya karne ki ijazat hai
2. **Hooks** — tool calls se pehle/baad apna code chalao (PreToolUse, PostToolUse)
3. **Sessions** — multi-turn agents jo context yaad rakhen
4. **MCP Servers** — databases, browsers, APIs se connect karo

---

*Source: https://code.claude.com/docs/en/agent-sdk/quickstart*
