# Custom Tools — Claude Agent SDK
### Complete Beginner Guide (Roman Urdu)

---

## Sabse Pehle: Custom Tool Kya Hota Hai?

Socho Claude ek bahut smart dost hai jo sab kuch jaanta hai — lekin **bahar ki duniya se completely cut off** hai.
Woh internet nahi use kar sakta, koi database nahi dekh sakta, koi API nahi call kar sakta.

**Custom Tool** matlab: tum Claude ko ek "haath" dete ho jo woh use kar sake bahar ki duniya se baat karne ke liye.

**Real life example:**
- Tum Claude se poochho: *"Karachi mein aaj kitni garmi hai?"*
- Claude ke paas real-time data nahi hai
- Lekin agar tumne usse ek **weather tool** diya ho — toh Claude khud woh tool call karega, data lega, aur tumhe jawab dega

Yeh sab automatically hota hai — Claude khud decide karta hai **kab** tool use karna hai!

---

## Docs ka Quick Reference — Kya Matlab Hai?

| Kaam | Tarika |
|------|--------|
| Tool banana | `@tool` decorator (Python) ya `tool()` (TypeScript) |
| Claude ko tool dena | `create_sdk_mcp_server` mein wrap karo, phir `query()` ko do |
| Tool ko pre-approve karna | `allowed_tools` list mein daalo |
| Built-in tool hatana | `tools` array mein sirf woh dalo jo chahiye |
| Tools parallel chalana | `readOnlyHint: True` lagao |
| Error handle karna | `is_error: True` return karo — kabhi throw mat karo |
| Image return karna | `"type": "image"` block use karo content array mein |
| JSON data return karna | `structuredContent` use karo |

---

## Tool Ke 4 Zaroori Parts

Har tool mein exactly **4 cheezein** honi chahiye.
Yeh 4 cheezein mil ke Claude ko batati hain ke tool kya hai, kab use karna hai, aur kaise use karna hai.

```
+---------------------------------------------+
|  TOOL                                       |
|                                             |
|  1. NAME        -> tool ka unique naam      |
|  2. DESCRIPTION -> kya karta hai (Claude    |
|                    yahi padh ke decide karta)|
|  3. SCHEMA      -> kya arguments chahiye    |
|  4. HANDLER     -> actual kaam karne wala   |
|                    function                 |
+---------------------------------------------+
```

---

### Part 1: NAME (Naam)

```
"get_weather"
```

- Tool ka unique naam hota hai
- Claude isse **call** karta hai jab tool use karna ho
- Koi spaces nahi — underscore use karo
- Bilkul Python function ke naam ki tarah socho

---

### Part 2: DESCRIPTION (Tafseel)

```
"Kisi bhi city ka mausam pata karo"
```

- **Yeh sabse important part hai!**
- Claude yeh read karta hai aur decide karta hai **KAB** tool use karna hai
- Agar description weak hai — Claude galat waqt pe tool use karega ya bilkul nahi karega
- Jitni clear aur specific description — utna better kaam karega Claude

> **Tip:** Description mein likho KAB use karo, KAISE use karo, kya milega.
> Sirf "weather fetch karo" mat likho — "User ke kisi bhi weather sawal pe yeh tool call karo" likho.

---

### Part 3: INPUT SCHEMA (Inputs ki Definition)

```python
{"city_name": str}
```

- Claude ko batata hai: *"Jab tum yeh tool call karo, yeh arguments do"*
- `str`   -> text (jaise "Karachi")
- `float` -> decimal number (jaise 24.86)
- `int`   -> integer number (jaise 5)
- SDK isko automatically JSON Schema mein convert kar deta hai

**Puri JSON Schema bhi de sakte ho** (jab enum, optional fields, ya nested objects chahiye):

```python
{
    "type": "object",
    "properties": {
        "city_name": {
            "type": "string",
            "description": "City ka naam jiska weather chahiye"
        }
    },
    "required": ["city_name"]    # yeh field zaroori hai
}
```

---

### Part 4: HANDLER (Actual Kaam Karne Wala Function)

```python
async def get_weather(args):
    city = args["city_name"]   # Claude ne jo bheja woh args mein hai
    # ... API call ya koi bhi kaam ...
    return {
        "content": [
            {"type": "text", "text": f"{city} mein Sunny +35C hai"}
        ]
    }
```

- Yeh function **tab chalta hai** jab Claude tool call kare
- `args` ek dictionary hoti hai — Claude ne jo values bheji woh yahan hoti hain
- Return karna **zaroori hai** ek specific format mein (niche detail hai)

---

## Handler Ka Return Format

Handler hamesha ek specific format mein return karta hai:

```python
return {
    "content": [
        {
            "type": "text",
            "text": "Yahan apna result likho"
        }
    ]
}
```

**`content` ek list hai** — matlab tum multiple cheezein ek saath return kar sakte ho:

```python
return {
    "content": [
        {"type": "text",  "text": "Yeh text hai"},
        {"type": "image", "data": "...", "mimeType": "image/png"},
    ]
}
```

**Agar error ho:**

```python
return {
    "content": [{"type": "text", "text": "Kuch gadbad hui!"}],
    "is_error": True        # <- yeh flag zaroori hai error pe
}
```

---

## MCP Server Kya Hota Hai?

Tool directly Claude tak nahi pahunch sakta — isko ek **wrapper** chahiye jise **MCP Server** kehte hain.

**Analogy:**

```
Tool       = Chef     (kaam karta hai)
MCP Server = Kitchen  (jahan chef kaam karta hai)
Claude     = Customer (kitchen se order karta hai)
```

```python
weather_server = create_sdk_mcp_server(
    name="weather",           # Server ka naam
    version="1.0.0",          # Version
    tools=[get_weather],      # Is server mein kaunse tools hain
)
```

**Important:** Yeh server alag process mein nahi chalta — **same program ke andar** (in-process) chalta hai.
Koi extra terminal ya process nahi chalani.

---

## Tool Ko `query()` Mein Dena

```python
options = ClaudeCodeOptions(
    mcp_servers={"weather": weather_server},         # Server do
    allowed_tools=["mcp__weather__get_weather"],     # Tool approve karo
)

async for message in query(
    prompt="Karachi ka weather kya hai?",
    options=options,
):
    ...
```

**2 cheezein dhyan se dekho:**

1. `mcp_servers` — dictionary hai `{"server_naam": server_object}`
2. `allowed_tools` — list hai, har tool ka **full naam** likhna hota hai

---

## Tool Ka Full Naam Kaise Banta Hai?

Yeh ek zaroori rule hai — bhool mat jaana:

```
mcp__{server_name}__{tool_name}
 ^          ^              ^
prefix  server ka naam  tool ka naam

Double underscore hai __ (single nahi)
```

**Example:**

```
Server naam : weather
Tool naam   : get_weather
Full naam   : mcp__weather__get_weather
```

Yahi naam `allowed_tools` mein likhna hoga.

---

## `allowed_tools` Kyun Zaroori Hai?

Security ke liye — tum explicitly batate ho ke kaunse tools **bina permission ke** automatically chal sakte hain.

```python
allowed_tools=["mcp__weather__get_weather"]
```

Agar yeh list mein nahi — Claude tool use karne se pehle **permission maangega** (ya block ho jaega).

**Wildcard bhi chal sakta hai:**

```python
allowed_tools=["mcp__weather__*"]   # weather server ke SARE tools allow
```

---

## Multiple Tools Ek Server Mein

Ek server mein **jitne chahiye utne tools** rakh sakte ho:

```python
weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[get_weather, get_rain_chance, get_forecast],   # 3 tools!
)
```

**Dhyan rakho:** Har tool context window mein space leta hai.
Bahut zyada tools — Claude slow ho jaega aur zyada costly hoga.
Agar dozens of tools hain — **Tool Search** feature use karo (yeh alag topic hai).

---

## Tool Annotations — Optional Metadata

Annotations tool ke baare mein extra info hoti hain. Claude inhe padh ke better decisions leta hai.

```python
from claude_agent_sdk import ToolAnnotations

@tool(
    "get_weather",
    "Mausam pata karo",
    {"city_name": str},
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def get_weather(args):
    ...
```

| Annotation | Default | Matlab |
|---|---|---|
| `readOnlyHint` | `False` | Tool sirf read karta hai, kuch change nahi karta — parallel chal sakta hai |
| `destructiveHint` | `True` | Tool kuch delete ya overwrite kar sakta hai |
| `idempotentHint` | `False` | Same input pe hamesha same output aata hai |
| `openWorldHint` | `True` | Tool bahar internet/API se baat karta hai |

> **Zaroori baat:** Yeh sirf hints hain — SDK enforcement nahi karta.
> Agar `readOnlyHint=True` rakho lekin tool actually database mein write karta ho — phir bhi likhega.
> Accurate rakho taake Claude sahi decisions le sake.

---

## `tools` Option — Built-in Tools Control

Claude ke apne built-in tools hote hain (file read karna, bash commands, grep, etc.).
Tum inhe control kar sakte ho:

```python
# Sirf yeh 2 built-in tools rakho, baaki sab hatao
options = ClaudeCodeOptions(tools=["Read", "Grep"])

# Sare built-in tools hatao — sirf apne MCP tools rakho
options = ClaudeCodeOptions(tools=[])
```

**`disallowed_tools` bhi use kar sakte ho:**

```python
# Bash tool completely hatao
disallowed_tools=["Bash"]

# Bash mein sirf specific command block karo
disallowed_tools=["Bash(rm *)"]   # rm * wali command block
```

---

## Error Handling — Bahut Important!

Yeh section **critical** hai. Do tarike hain — ek sahi, ek galat.

---

### Tarika 1: Exception Throw Karo  ---  GALAT

```python
async def my_tool(args):
    response = await some_api_call()
    if response.status_code != 200:
        raise Exception("API fail ho gaya!")   # <- GALAT! kabhi mat karo
```

**Kya hota hai:**
- Poora `query()` call **crash** ho jaata hai
- Claude ko kuch pata nahi chalta
- User ko error milta hai
- Koi recovery possible nahi

---

### Tarika 2: `is_error: True` Return Karo  ---  SAHI

```python
async def my_tool(args):
    try:
        response = await some_api_call()

        if response.status_code != 200:
            return {
                "content": [{"type": "text", "text": f"API error: {response.status_code}"}],
                "is_error": True        # <- Claude ko pata chale ke fail hua
            }

        return {
            "content": [{"type": "text", "text": response.text}]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Kuch gadbad hui: {str(e)}"}],
            "is_error": True
        }
```

**Kya hota hai:**
- Program **chalta rehta hai**
- Claude ko pata chalta hai ke error aya
- Claude phir koi aur approach try kar sakta hai ya user ko sahi se bata sakta hai
- Recovery possible hai

> **Rule:** Handler mein **hamesha** `try/except` lagao aur errors ko `is_error: True` ke saath return karo.

---

## Images Return Karna

Tool sirf text nahi — **image bhi return kar sakta hai!**

```python
import base64
import httpx

async def fetch_image_tool(args):
    async with httpx.AsyncClient() as client:
        response = await client.get(args["url"])   # Image URL se bytes lo

    return {
        "content": [
            {
                "type": "image",
                "data": base64.b64encode(response.content).decode("ascii"),  # Bytes -> base64
                "mimeType": response.headers.get("content-type", "image/png")
            }
        ]
    }
```

**2 zaroori baatein:**
1. Image URL directly nahi de sakte — pehle bytes download karo, phir `base64` mein convert karo
2. `data:image/...;base64,` prefix **mat lagao** — sirf pure base64 string do

---

## Resources Return Karna

Resource ek named content hota hai — koi file ya document jo URI se identify ho.

```python
return {
    "content": [
        {
            "type": "resource",
            "resource": {
                "uri": "file:///tmp/report.md",       # Sirf ek label hai — SDK yahan se nahi padhta
                "mimeType": "text/markdown",
                "text": "# Report\nYahan actual content hai..."  # Content yahan inline dena hota hai
            }
        }
    ]
}
```

**Dhyan rakho:** `uri` sirf ek **label** hai Claude ke reference ke liye — SDK actually us path se kuch nahi padhta.
Actual content `text` ya `blob` field mein inline dena hota hai.

---

## Structured Data Return Karna

`structuredContent` ek optional JSON object hai — machine-readable exact data ke liye:

```python
return {
    "content": [
        {"type": "text", "text": "Temperature data yahan hai"}   # Human ke liye text
    ],
    "structuredContent": {          # Machine ke liye exact JSON
        "temperature": 35.2,
        "unit": "celsius",
        "city": "Karachi"
    }
}
```

**Kab use karo:** Jab tumhara tool koi exact data return kare (numbers, structured info) aur tum chahte ho ke
Claude woh values precisely read kare — text parse karne ki bajaye.

> **Note:** Python SDK mein abhi `structuredContent` fully support nahi hota. TypeScript mein zyada kaam karta hai.

---

## Poora Flow — Ek Baar Phir Dekho

```
+----------------------------------------------------------+
|                                                          |
|  Tum    ->  query("Karachi ka weather kya hai?")         |
|                          |                               |
|                          v                               |
|  Claude ->  Socha... "Mujhe weather tool use karna hai"  |
|                          |                               |
|                          v                               |
|  Claude ->  get_weather({"city_name": "Karachi"})        |
|                          |                               |
|                          v                               |
|  Handler ->  wttr.in API call ki, data mila              |
|                          |                               |
|                          v                               |
|  Handler ->  return {"content": [{"type": "text",        |
|                 "text": "Sunny +35C"}]}                  |
|                          |                               |
|                          v                               |
|  Claude ->  Result dekha, jawab taiyar kiya              |
|                          |                               |
|                          v                               |
|  Tum    ->  "Karachi mein Sunny hai, 35C temperature"    |
|                                                          |
+----------------------------------------------------------+
```

---

## Complete Code Structure — Ek Nazar Mein

```python
# Step 1: Tool define karo
@tool(
    "tool_naam",             # Part 1: naam
    "Kya karta hai",         # Part 2: description
    {"input_field": str},    # Part 3: schema
)
async def tool_handler(args):                   # Part 4: handler
    try:
        result = args["input_field"]
        return {
            "content": [{"type": "text", "text": result}]
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": str(e)}],
            "is_error": True
        }

# Step 2: MCP Server mein wrap karo
my_server = create_sdk_mcp_server(
    name="my_server",
    version="1.0.0",
    tools=[tool_handler],
)

# Step 3: query() ko do
options = ClaudeCodeOptions(
    mcp_servers={"my_server": my_server},
    allowed_tools=["mcp__my_server__tool_naam"],
)

async for message in query(prompt="...", options=options):
    ...
```

---

## 6 Golden Rules — Yaad Rakhna Zaroori Hai

```
1. Tool = 4 parts: naam, description, schema, handler

2. Handler ka return format:
   {"content": [{"type": "text", "text": "..."}]}

3. Error pe is_error: True return karo — kabhi throw mat karo

4. Tool ka full naam: mcp__{server}__{tool}
   (double underscore __ hai, single nahi)

5. allowed_tools mein tool ka full naam likhna zaroori hai

6. Description jitni clear — Claude utna better use karega
```

---

## Ab Aage Kya Seekhna Hai?

- **Tool Search**  -> Bahut saare tools efficiently load karna (dozens of tools ke liye)
- **MCP Servers**  -> External MCP servers se connect karna (GitHub, Slack, filesystem, etc.)
- **Permissions**  -> Tools ko granular level pe control karna

---

*Yeh notes Claude Agent SDK ki official docs se liye gaye hain aur Roman Urdu mein explain kiye gaye hain.*

---

# `tool.py` — Har Line Ki Tafseel

---

## BLOCK 1: Imports (Lines 1–5)

```python
from typing import Any
```
**Python concept:** `typing` ek built-in module hai jo tumhe batata hai ke function mein **kaunsa data type** aana chahiye. `Any` ka matlab hai: *"yeh variable koi bhi type ho sakta hai — string, number, dict, kuch bhi."*

---

```python
import asyncio
```
**Python concept:** `asyncio` Python ka built-in module hai jo **asynchronous code** chalata hai. Matlab: ek kaam hone ka intezaar karte hue doosra kaam bhi kar sakte ho. Jaise: API ka response aane ka wait karte waqt processor khali nahi baithta.

---

```python
import httpx
```
**Python concept:** `httpx` ek third-party library hai jo **HTTP requests** karne ke liye use hoti hai — jaise internet pe kisi website ya API ko call karna. (Built-in `requests` se better hai kyunki yeh `async` support karta hai.)

---

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, query, ClaudeAgentOptions, ResultMessage
```
**SDK concept:** Yeh 5 cheezein Claude Agent SDK se import ho rahi hain:

| Import | Kya hai |
|--------|---------|
| `tool` | Decorator — function ko tool mein convert karta hai |
| `create_sdk_mcp_server` | Tool ko Claude ke liye ek server mein wrap karta hai |
| `query` | Claude se baat karne ka main function |
| `ClaudeAgentOptions` | Claude ko options dene ka tarika (kaunse tools, kya allowed) |
| `ResultMessage` | Claude ka final jawab jab sab tool calls khatam ho jayein |

---

## BLOCK 2: Tool Definition (Lines 8–32)

```python
@tool(
    "get_weather",
    "Fetches the current weather for a given city name. Call this whenever the user asks about weather.",
    {"cityName": str},
)
```
**Python concept:** `@tool(...)` ek **decorator** hai. Decorator ka matlab — is function ko normal function ki tarah mat chalao, pehle isko process karo aur kuch extra features do. `@tool(...)` ke andar 3 positional arguments hain:

- `"get_weather"` → **Name:** Claude iss naam se tool call karega
- `"Fetches the current weather..."` → **Description:** Claude yeh padh ke decide karta hai KAB tool use karna hai — jitni clear description, utna better
- `{"cityName": str}` → **Schema:** ek Python dict — key hai `"cityName"` (string mein), value hai `str` (Python type). SDK yeh automatically JSON Schema mein convert karta hai Claude ke liye

**SDK concept:** `@tool` decorator ke 4 parts hote hain — naam, description, schema, handler. Yeh pehle 3 hain; handler (actual function) neeche aata hai.

---

```python
async def get_weather(args: dict[str, Any]) -> dict[str, Any]:
```
**Python concept:**
- `async def` → yeh function **asynchronous** hai — iske andar `await` use kar sakte ho. Normal `def` se different hai.
- `get_weather` → function ka naam (decorator mein jo naam diya wahi banana chahiye)
- `args: dict[str, Any]` → **type hint** hai — batata hai ke `args` ek **dictionary** hogi jisme keys strings hain aur values kuch bhi. Yeh sirf documentation ke liye hai, Python enforce nahi karta.
- `-> dict[str, Any]` → function **kya return karega** — ek dictionary (jo content array wali hogi)

**SDK concept:** Handler ko hamesha `args` parameter lena **zaroori** hai. Jab Claude tool call karta hai toh apni values is `args` dictionary mein daal ke bhejta hai.

---

```python
    try:
```
**Python concept:** `try:` block mein woh code likhte hain jo **fail ho sakta hai**. Agar andar koi error aaye — program crash nahi hoga, `except` block mein chala jaega.

**SDK concept:** Custom tool mein hamesha `try/except` lagana chahiye. Agar exception throw ho toh poora `query()` call crash ho jaata hai — Claude ko kuch pata nahi chalta. Isliye errors ko handle karke return karte hain.

---

```python
        city = args["cityName"]
```
**Python concept:** `args` ek dictionary hai. Dictionary se value nikalne ke liye `dict["key"]` syntax use karte hain. Toh `args["cityName"]` ka matlab hai: `args` dictionary mein se `"cityName"` key ki value nikalo.

**SDK concept:** Claude ne jo city name diya tha woh `args` mein `"cityName"` key ke neeche hoga — kyunki tumne schema mein `{"cityName": str}` diya tha.

---

```python
        async with httpx.AsyncClient() as client:
```
**Python concept:**
- `async with` → ek **async context manager** hai. Matlab: yeh resource (client) use karo, kaam hone ke baad automatically band kar do — tumhe manually close nahi karna.
- `httpx.AsyncClient()` → ek HTTP client object banata hai jo `async` requests kar sakta hai
- `as client` → iss object ko `client` naam deta hai taake neeche use kar sako

---

```python
            response = await client.get(
                f"https://wttr.in/{city.lower()}?format=%C+%t"
            )
```
**Python concept:**
- `await` → yeh keh raha hai: *"yeh kaam hone tak ruko — lekin rote waqt processor ko doosre kaam karne do"*. Sirf `async def` function mein use ho sakta hai.
- `client.get(url)` → uss URL pe **GET request** bhejo (browser ki tarah URL open karna)
- `f"..."` → **f-string** hai — curly braces `{}` mein Python expression likh sakte ho jo automatically value se replace ho jaata hai
- `city.lower()` → string method — city ka naam **lowercase** mein convert karta hai (`"KARACHI"` → `"karachi"`). wttr.in ke liye consistent URL banana.

**SDK concept:** Yeh actual API call hai — tool ka "kaam" yahan hota hai.

---

```python
            if response.status_code != 200:
                return {
                    "content": [{"type": "text", "text": f"Weather API error: {response.status_code}"}],
                    "is_error": True,
                }
```
**Python concept:**
- `response.status_code` → HTTP response ka status code. `200` matlab success, koi aur number matlab kuch gadbad.
- `!=` → "not equal to" operator
- `return` → function se bahar nikal jao aur yeh value wapis karo

**SDK concept:** `"is_error": True` ek SDK ka special flag hai. Iska matlab: *"Claude, yeh tool fail hua — lekin program band mat karo, tum apne aap koi doosra tarika try karo ya user ko batao."* Bina is flag ke Claude nahi samjhega ke kuch galat hua.

---

```python
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Weather in {city}: {response.text.strip()}",
                }
            ]
        }
```
**Python concept:**
- `response.text` → HTTP response ka content **plain text** ke tor pe nikalo (`.json()` nahi — wttr.in plain text deta hai jaise `"Sunny +35°C"`)
- `.strip()` → string ke start aur end se **whitespace/newlines** hatao

**SDK concept:** Tool ka **success return format** — hamesha yeh exact structure hona chahiye:
```
{
  "content": [          ← list hai (multiple blocks ho sakte hain)
    {
      "type": "text",   ← content ka type
      "text": "..."     ← actual text
    }
  ]
}
```
Claude ko yahi milta hai aur woh isko apne jawab mein use karta hai.

---

```python
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Failed to fetch weather: {str(e)}"}],
            "is_error": True,
        }
```
**Python concept:**
- `except Exception as e:` → `try` block mein **koi bhi** exception aaye — yahan pakad lo. `e` us exception ka object hai.
- `str(e)` → exception object ko **readable string** mein convert karo taake message mein show ho sake

**SDK concept:** Network fail ho ya koi bhi unexpected error aaye — `is_error: True` ke saath return karo. Kabhi exception ko "throw" mat karne do — SDK crash ho jaata hai.

---

## BLOCK 3: MCP Server (Lines 35–39)

```python
weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[get_weather],
)
```
**Python concept:**
- `create_sdk_mcp_server(...)` → ek function call hai jo ek **server object** return karta hai
- `weather_server = ...` → us object ko `weather_server` variable mein store karte hain
- `tools=[get_weather]` → `[]` ek **list** hai. `get_weather` function ko (call nahi kar rahe — sirf reference de rahe hain, koi `()` nahi) list mein daala

**SDK concept:** Tool directly Claude tak nahi pahunch sakta — pehle isko **MCP Server** mein wrap karna zaroori hai. Yeh server same program ke andar chalta hai (alag process nahi). `name="weather"` baad mein tool ke full naam mein use hoga: `mcp__weather__get_weather`.

---

## BLOCK 4: Main Function (Lines 42–59)

```python
async def main():
```
**Python concept:** `async` function define kar rahe hain — jo `await` use karega. Python mein `asyncio.run()` sirf ek async function ko "entry point" se chala sakta hai.

---

```python
    options = ClaudeAgentOptions(
        mcp_servers={"weather": weather_server},
        allowed_tools=["mcp__weather__get_weather"],
    )
```
**Python concept:**
- `ClaudeAgentOptions(...)` → ek **class constructor** hai — naya object banata hai
- `{"weather": weather_server}` → dictionary: key `"weather"` (server ka naam), value `weather_server` (upar banaya hua object)
- `["mcp__weather__get_weather"]` → list with ek string

**SDK concept:**
- `mcp_servers` → Claude ko batata hai kaunse MCP servers available hain
- `allowed_tools` → yeh list bata hai ke kaunse tools **bina permission prompt ke** automatically chal sakte hain. Format hamesha: `mcp__{server_naam}__{tool_naam}` (double underscore `__`)

---

```python
    async for message in query(
        prompt="What's the weather in Karachi?",
        options=options,
    ):
```
**Python concept:**
- `async for` → **asynchronous loop** — har message aane pe process karo, baqi ka intezaar nahi karna
- `query(...)` → Claude se baat karne wala main SDK function — ek **async generator** return karta hai (matlab ek ke baad ek messages deta rehta hai)

**SDK concept:** `query()` Claude ke saath poora conversation chalata hai — including tool calls. Jab Claude `get_weather` call karega, SDK khud handle karega, result Claude ko dega, aur final jawab ready hone pe `ResultMessage` milega.

---

```python
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(message.result)
```
**Python concept:**
- `isinstance(message, ResultMessage)` → check karta hai ke kya `message` object `ResultMessage` type ka hai
- `and` → dono conditions true honi chahiye
- `message.subtype == "success"` → sirf successful result chahiye, error nahi
- `print(...)` → terminal pe output dikhao

**SDK concept:** `query()` loop mein multiple types ke messages aate hain (tool calls, assistant messages, etc.). `ResultMessage` woh **final message** hota hai jab Claude ne sab tool calls kar ke final jawab taiyar kar liya ho. `message.result` mein Claude ka jawab hota hai.

---

## BLOCK 5: Entry Point (Line 62)

```python
asyncio.run(main())
```
**Python concept:** Yeh **program ka starting point** hai. `asyncio.run()` ek async function ko **synchronous** environment (normal Python script) se chala sakta hai. Bina is line ke `main()` kabhi execute nahi hogi.

---

## Poora Flow Ek Baar Phir:

```
asyncio.run(main())
    │
    ▼
query("What's the weather in Karachi?")
    │
    ▼ Claude socha: "weather sawal hai — get_weather tool use karun"
    │
    ▼ SDK ne get_weather({"cityName": "Karachi"}) call kiya
    │
    ▼ Handler ne wttr.in API call ki → "Sunny +35°C" mila
    │
    ▼ Handler ne return {"content": [{"type": "text", "text": "Weather in Karachi: Sunny +35°C"}]}
    │
    ▼ Claude ne yeh result dekha, jawab banaya
    │
    ▼ ResultMessage mila → print(message.result)
    │
    ▼ Terminal pe: "Karachi mein aaj Sunny hai, 35°C temperature hai"
```

Poora code samajh aa gaya hoga — Python basics (`async`, `dict`, `f-string`, `try/except`) aur SDK concepts (`@tool`, `create_sdk_mcp_server`, `query`, `allowed_tools`) dono!

---

# Tool Handler Ka Standard Return Format

## SDK Ka Standard — Har Custom Tool Ka Return Yahi Hoga

```python
{
    "content": [...],        # HAMESHA zaroori
    "is_error": True,        # SIRF error pe — optional
    "structuredContent": {}  # Optional — machine-readable JSON ke liye
}
```

---

### `content` — Hamesha Zaroori

`content` ek **list** hai — iske andar ek ya zyada **content blocks** hote hain. Har block ka `type` hota hai:

| `type` | Kab use karo |
|--------|-------------|
| `"text"` | Normal text result — sabse common |
| `"image"` | Image return karni ho (base64) |
| `"audio"` | Audio return karni ho |
| `"resource"` | Koi file ya document (URI label ke saath) |
| `"resource_link"` | Sirf link dena ho, content inline nahi |

**Minimum valid return:**
```python
return {
    "content": [
        {"type": "text", "text": "Koi bhi result text"}
    ]
}
```

---

### `is_error` — Sirf Error Pe

```python
return {
    "content": [{"type": "text", "text": "Kuch fail hua"}],
    "is_error": True     # yeh flag Claude ko signal deta hai
}
```

- Success pe `is_error` **bilkul mat likho** — ya `False` rakho
- Error pe `True` karo — Claude ko pata chale ke tool fail hua, woh recover kar sake

---

### Yeh Standard Kyun Hai?

Kyunki SDK ke andar **MCP Protocol** use hota hai — aur MCP ka `CallToolResult` type exactly yahi format define karta hai. SDK tumhara return dict le ke Claude tak forward karta hai is protocol ke through. Isliye format change karo toh SDK samjhega nahi.

```
Tumhara Handler
      │
      │ return {"content": [...]}
      ▼
  SDK (MCP Layer)
      │
      │ CallToolResult format mein convert
      ▼
    Claude
```

**Short mein:** Har tool — chahe weather ho, database query ho, ya image fetch ho — return format yahi rahega. Sirf `content` ke andar `type` aur fields badlenge.

<br>

---

# Behind The Scene — SDK Custom Tool Ka Poora Flow

## Concept Verification — Kya Sahi Samjha

**Point 1: `@tool` ke andar jo likhte hain woh Claude ko samjhane ke liye hai**
```
✅ BILKUL SAHI
```
Name, description, schema — yeh sab LLM ke liye "documentation" hai. LLM inhe padh ke decide karta hai kab aur kaise tool call karna hai.

---

**Point 2: LLM query se city nikal ke tool call karta hai**
```
✅ SAHI — lekin ek nuance hai (neeche detail)
```

---

**Point 3: Agent function execute karta hai, result LLM ke paas jaata hai**
```
✅ BILKUL SAHI
```

---

**Point 4: Yeh sab loop mein chalta hai jo SDK chalata hai**
```
✅ BILKUL SAHI — yahi sabse important concept hai
```

---

## 2 Chhoti Corrections

### Correction 1: LLM function "call" nahi karta — woh SDK ko instruction deta hai

Galat tasweer:
```
LLM ne kaha → get_weather({"cityName":"Gujar Khan"})  ← direct call nahi hota
```

Actually jo hota hai:
```
LLM ne Claude API ko ek JSON response bheja:
{
  "type": "tool_use",
  "name": "mcp__weather__get_weather",   ← pura naam
  "input": {"cityName": "Gujar Khan"}
}
```
Phir **SDK ne** yeh dekha aur **Python function** execute kiya. LLM khud Python code nahi chala sakta — woh sirf SDK ko instruction deta hai.

---

### Correction 2: Tool ka actual naam `mcp__weather__get_weather` hai — sirf `get_weather` nahi

`create_sdk_mcp_server(name="weather")` ke through jaane ke baad tool ka naam ban jaata hai:
```
mcp__weather__get_weather
```
LLM is pure naam se jaanta hai tool ko.

---

## Poora Sahi Flow

```
1. query() call hua
       │
       ▼
2. SDK ne tool ki name+description+schema ko
   JSON Schema mein convert kiya
   ({"cityName": str} → proper JSON Schema)
       │
       ▼
3. Claude API ko bheja:
   - User prompt: "What's the weather in Karachi?"
   - Tools list: [{name: "mcp__weather__get_weather", description: "...", schema: {...}}]
       │
       ▼
4. LLM (Claude) ne socha:
   "Weather question hai → tool use karna chahiye"
   LLM ne response diya:
   {type: "tool_use", name: "mcp__weather__get_weather", input: {"cityName": "Karachi"}}
       │
       ▼
5. SDK ne yeh "tool_use" response dekha
   → Python function get_weather({"cityName": "Karachi"}) execute kiya
       │
       ▼
6. Handler ne wttr.in API call ki → "Sunny +35°C" mila
   → return {"content": [{"type": "text", "text": "Weather in Karachi: Sunny +35°C"}]}
       │
       ▼
7. SDK ne yeh result wapis Claude API ko bheja:
   {type: "tool_result", content: "Weather in Karachi: Sunny +35°C"}
       │
       ▼
8. LLM ne result dekha → final human-friendly jawab banaya:
   "Karachi mein aaj Sunny hai, temperature 35°C hai"
       │
       ▼
9. SDK ne yeh ResultMessage ke tor pe return kiya
       │
       ▼
10. print(message.result) → terminal pe dikha
```

---

## Summary Table

| Concept | Status | Note |
|---------|--------|------|
| `@tool` Claude ko samjhane ke liye | ✅ Sahi | |
| LLM tool call karta hai | ✅ Sahi | Lekin direct nahi — JSON instruction deta hai SDK ko |
| Agent/SDK function execute karta hai | ✅ Sahi | |
| Result LLM ke paas jaata hai | ✅ Sahi | |
| Loop SDK chalata hai | ✅ Sahi | |
| Tool naam `get_weather` | ⚠️ Partial | Full naam `mcp__weather__get_weather` hai |

**Tera behind-the-scene concept solid hai** — bas yad rakho: LLM "instruction" deta hai, actual Python code **SDK** chalata hai!

<br>
