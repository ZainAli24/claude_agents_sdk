# Claude Agent SDK — Sessions Complete Notes

---

## Session kya hai?

Session = **conversation history jo disk pe automatically save hoti hai.**

Teri har query, Claude ka har jawab, har tool call, har result — sab ek file mein likha jata hai.

```
~/.claude/projects/E--claude-agents-sdk/
    └── 15d357bd-f279-4449.jsonl   ← yeh session file hai
```

Yeh ek `.jsonl` file hai — har line ek message hai (JSON format mein).

---

## Session aur Conversation History — Fark

```
Session     → conversation ka naam / ID / file
History     → us session ke andar jo kuch hua (messages, tool calls, results)

Session = container
History = us container ka content
```

> **Note:** Session sirf **conversation** save karta hai — filesystem changes nahi. Agar Claude ne koi file edit ki, woh change real hai aur session se undo nahi hoga.

---

## `ClaudeSDKClient` — Behind-Scene Kaise Kaam Karta Hai

### Step 1 — Client Object Bana

```python
async with ClaudeSDKClient(options=options) as client:
```

- Client object bana
- SDK se connection hua
- **Abhi koi session nahi** → `session_id = None`

---

### Step 2 — Pehli Query

```python
await client.query("My brother name is Sarim!")
```

```
1. Client ne Claude ko prompt bheja → NAYA session shuru hua
2. SDK ne naya session_id generate kiya → "15d357bd-..."
3. Claude ne jawab diya
4. Conversation disk pe save hui:
   ~/.claude/projects/E--claude-agents-sdk/15d357bd.jsonl
5. Client ne session_id apne andar yaad kar liya (internally store)
```

---

### Step 3 — Doosri Query

```python
await client.query("Whats my bro name?")
```

```
1. Client ke paas wahi session_id = "15d357bd-..." hai (yaad hai usse)
2. Client ne SDK ko kaha: "is session_id ke saath resume karo"
3. SDK ne disk se 15d357bd.jsonl padhi → puri history load ki
4. History + naya prompt → Claude ko bheja
5. Claude ko pata tha "Sarim" → jawab diya
6. Naya message usi 15d357bd.jsonl file mein add hua
```

---

### Step 4 — Teesri Query (aur uske baad bhi)

```python
await client.query("What did I say in my first message?")
```

```
1. Wahi session_id = "15d357bd-..." client ke paas hai
2. Usi session resume → file se poori history load
3. Claude ko sab pata → jawab diya
4. Message file mein add
```

**Pattern:** Har nayi query mein client wahi session_id use karta hai → history load → Claude ko bheja → jawab → file mein add.

---

## Visual Flow

```
async with ClaudeSDKClient as client:
         |
         | session_id = None (abhi koi session nahi)
         |
    client.query("Query 1")
         |
         ↓
    NAYA session bana → session_id = "15d357bd"
    File bani: 15d357bd.jsonl
    Content: [Q1, A1]
         |
    client.query("Query 2")
         |
         ↓
    session_id = "15d357bd" (client ke paas yaad hai)
    File se history load: [Q1, A1]
    Claude ko bheja: [Q1, A1, Q2]
    Jawab aya: A2
    File update: [Q1, A1, Q2, A2]
         |
    client.query("Query 3")
         |
         ↓
    session_id = "15d357bd" (wahi)
    File se history load: [Q1, A1, Q2, A2]
    Claude ko bheja: [Q1, A1, Q2, A2, Q3]
    Jawab aya: A3
    File update: [Q1, A1, Q2, A2, Q3, A3]
```

---

## `query()` vs `ClaudeSDKClient` — Fark

```
query()            → har baar NAYA session banta hai
                     do alag queries ka koi link nahi

ClaudeSDKClient    → ek hi session_id track karta hai internally
                     saari queries ek hi session mein chalti hain
```

**Example:**

```python
# query() — ALAG sessions
await query("My name is Zain")    # Session A
await query("Whats my name?")     # Session B — Claude ko pata nahi!

# ClaudeSDKClient — EK session
async with ClaudeSDKClient() as client:
    await client.query("My name is Zain")    # Session A shuru
    await client.query("Whats my name?")     # Session A continue → Claude ko pata hai!
```

---

## 5 Approaches — Kaunsa Kab Use Karo

| Situation | Kya use karo |
|---|---|
| Ek kaam, khatam — aage koi follow-up nahi | Simple `query()` |
| Ek program mein multiple queries, context chahiye | `ClaudeSDKClient` |
| Program band hua, dobara chalao — same session se | `continue_conversation=True` |
| Kisi specific purani session ko resume karna | `session_id` capture karo, phir `resume=session_id` |
| Ek direction try karo purani session ko destroy kiye bina | `fork_session=True` |

---

## Session ID Capture Karna

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def main():
    session_id = None

    async for message in query(
        prompt="Analyze the auth module",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Glob", "Grep"],
        ),
    ):
        if isinstance(message, ResultMessage):
            session_id = message.session_id   # ID yahan milti hai
            if message.subtype == "success":
                print(message.result)

    print(f"Session ID: {session_id}")
    return session_id

session_id = asyncio.run(main())
```

---

## Resume — Specific Session Wapas Lao

```python
# Pehle session ne code analyze kiya tha
# Ab usi context mein refactor karo

async for message in query(
    prompt="Now implement the refactoring you suggested",
    options=ClaudeAgentOptions(
        resume=session_id,                          # wahi ID
        allowed_tools=["Read", "Edit", "Glob"],
    ),
):
    if isinstance(message, ResultMessage) and message.subtype == "success":
        print(message.result)
```

**Resume kab use karo:**
- Follow-up karna ho completed task pe
- Program crash ya band hua, wapas shuru karna ho
- `error_max_turns` aya, limit badhake dobara try karna ho

---

## Session ID se Resume — Behind-Scene Kaise Kaam Karta Hai

### Step 1 — Query 1: Naya Session Bana

```python
session_id = None

async for message in query(
    prompt="tell me most important today AI news",
    options=ClaudeAgentOptions(allowed_tools=["WebSearch"]),
):
    if isinstance(message, ResultMessage) and message.subtype == "success":
        session_id = message.session_id   # "abc123" capture kiya
        print(message.result)
```

```
Query 1 ke baad:
→ naya session bana → session_id = "abc123"
→ file bani: abc123.jsonl
→ file content: [Q1: "AI news", A1: "...news response..."]
```

---

### Step 2 — Query 2: session_id se Resume

```python
async for message in query(
    prompt="make linkedin post about the most important AI update",
    options=ClaudeAgentOptions(resume=session_id),   # "abc123" pass kiya
):
    if isinstance(message, ResultMessage) and message.subtype == "success":
        print(message.result)
```

```
Query 2 ke time behind-scene:
→ SDK ne resume=session_id dekha → "abc123"
→ disk se abc123.jsonl file load ki
→ history nikali: [Q1: "AI news", A1: "...news..."]
→ Claude ko bheja: [Q1, A1, Q2: "linkedin post"]
→ Claude ko pata tha pehli query kya thi → context ke saath jawab diya
→ Q2 aur A2 usi abc123.jsonl file mein add howe
```

```
abc123.jsonl ab:
[Q1: "AI news", A1: "...news...", Q2: "linkedin post", A2: "...post..."]
```

---

### Visual Flow

```
Query 1:
    query(prompt="AI news", allowed_tools=["WebSearch"])
         |
         ↓
    NAYA session → session_id = "abc123"
    abc123.jsonl bani → [Q1, A1]
    session_id capture kiya

Query 2:
    query(prompt="linkedin post", resume="abc123")
         |
         ↓
    SDK ne abc123.jsonl load ki → history: [Q1, A1]
    Claude ko bheja: [Q1, A1, Q2]
    Claude ne jawab diya (Q1 ka context tha)
    abc123.jsonl update: [Q1, A1, Q2, A2]
```

---

### Practical Code — Query 1 se ID Pakad ke Query 2 Resume Karo

```python
# // Author: Zain Ali
import asyncio
from claude_agent_sdk import query, ResultMessage, ClaudeAgentOptions

async def main():
    session_id = None

    # Query 1 — naya session, ID capture karo
    async for message in query(
        prompt="tell me most important today AI news",
        options=ClaudeAgentOptions(allowed_tools=["WebSearch"]),
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            session_id = message.session_id
            print("\n SESSION ID :", session_id)
            print("\n RESPONSE 1 :", message.result)

    # Query 2 — usi session_id se resume karo
    async for message in query(
        prompt="make a linkedin post about the most important AI update",
        options=ClaudeAgentOptions(resume=session_id),
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print("\n RESPONSE 2 :", message.result)

    return session_id

session_id = asyncio.run(main())
print("\n Captured session_id:", session_id)
```

---

### Key Rule

```
resume=session_id diya
    → SDK ne disk se file load ki      (history)
    → history + naya prompt → Claude   (context ke saath)
    → Claude ka jawab                  (aware of past)
    → jawab usi file mein save         (session continue)
```

---

## Fork Session — Naya Direction, Purani Session Safe

Fork = **purani session ki history copy karke naya session banana — purana session intact rehta hai.**

Real life example: Ek writer ne 3 chapters likhe. Ab chapter 4 ke liye 2 different endings try karna chahta hai. Fork karo — dono endings alag alag, original 3 chapters safe.

> **Note:** Fork sirf **conversation history** copy karta hai — filesystem nahi. Agar forked agent ne koi file edit ki, woh change real hai aur original session pe bhi visible hoga.

---

### Behind-Scene — Disk pe Kya Hota Hai?

```
Original session file:
abc123.jsonl → [Q1: "addition function", A1: "def add()..."]

fork_session=True kiya:
SDK ne abc123.jsonl ki COPY banayi → xyz789.jsonl
xyz789.jsonl → [Q1: "addition function", A1: "def add()..."]  (same history)

Ab dono alag alag:
abc123.jsonl → original, apni direction mein chala
xyz789.jsonl → fork, alag direction mein chala
```

---

### Step-by-Step Visual Flow

```
Step 1 — Original Query:
    abc123.jsonl bani
    content: [Q1: "addition function", A1: "def add()..."]
    session_id = "abc123"

Step 2 — fork_session=True:
    SDK ne abc123.jsonl copy ki → xyz789.jsonl (same history)
    Fork mein nayi query add hui:
    xyz789.jsonl: [Q1, A1, Q2: "error handling", A2: "try/except..."]
    abc123.jsonl: [Q1, A1]   ← UNCHANGED, safe

Step 3 — Original resume:
    resume=session_id → abc123.jsonl load ki
    abc123.jsonl: [Q1, A1, Q3: "logging", A3: "import logging..."]
```

---

### Dono Sessions Alag Alag Chalte Hain

```
abc123.jsonl (original):
    Q1: "addition function"
    A1: "def add(a, b): return a + b"
    Q3: "logging add karo"           ← apni direction
    A3: "import logging..."

xyz789.jsonl (fork):
    Q1: "addition function"          ← same start (copy)
    A1: "def add(a, b): return a + b"
    Q2: "error handling add karo"    ← alag direction
    A2: "try: ... except:..."
```

---

### Simple Beginner Code

```python
# // Author: Zain Ali
import asyncio
from claude_agent_sdk import query, ResultMessage, ClaudeAgentOptions

async def main():

    # Step 1: Original Session
    session_id = None
    async for message in query(
        prompt="Python mein addition function likho",
        options=ClaudeAgentOptions(allowed_tools=["Write"]),
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            session_id = message.session_id
            print("\n Original Session ID:", session_id)
            print("\n Response 1:", message.result)

    # Step 2: Fork karo — original safe rahe, naya direction lo
    forked_id = None
    async for message in query(
        prompt="Ab is function mein error handling bhi add karo",
        options=ClaudeAgentOptions(
            resume=session_id,     # original session se shuru karo
            fork_session=True,     # lekin copy mein — original safe rahe
            allowed_tools=["Write", "Edit"],
        ),
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            forked_id = message.session_id   # fork ka NAYA ID milega
            print("\n Forked Session ID:", forked_id)
            print("\n Fork Response:", message.result)

    # Step 3: Original session mein wapas jao — fork se alag
    async for message in query(
        prompt="Ab is function mein logging add karo",
        options=ClaudeAgentOptions(
            resume=session_id,     # original session_id — fork wala nahi
            allowed_tools=["Write", "Edit"],
        ),
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print("\n Original Response:", message.result)

    print("\n session_id (original):", session_id)
    print(" forked_id  (fork)    :", forked_id)

asyncio.run(main())
```

---

### Summary Table

| | Original (`session_id`) | Fork (`forked_id`) |
|---|---|---|
| Pehli query ka context | Hai | Hai (copy) |
| Fork ke baad changes | Apne andar | Apne andar |
| Ek doosre ko affect? | Nahi | Nahi |
| File | `abc123.jsonl` | `xyz789.jsonl` (naya) |

---

### Simple Rule

```
fork_session=True matlab:
    → purani history copy karo naye session mein
    → naya session_id milega (forked_id)
    → dono alag alag paths pe chale jate hain
    → original kabhi affect nahi hota
```

**Fork = do alag raaste, dono pe wapas ja sakte ho.**

---

## `continue_conversation=True` — Program Restart ke Baad Resume

Sabse simple approach — koi session_id track nahi karna. Program band hua, dobara chalao, SDK khud last session dhundh ke resume kar leta hai.

---

### Behind-Scene — SDK Last Session Kaise Dhundta Hai?

SDK **file ki last-modified timestamp** dekhta hai. OS har file ka time automatically track karta hai — jab bhi file mein kuch likha jata hai, OS uska timestamp update karta hai.

```
C:\Users\ZAIN ALI\.claude\projects\E--claude-agents-sdk\

abc123.jsonl   → last modified: 2026-06-01 10:00 AM
pqr456.jsonl   → last modified: 2026-06-03 08:20 AM
xyz789.jsonl   → last modified: 2026-06-04 03:45 PM  ← sabse recent
```

```
continue_conversation=True diya:
    → SDK ne project folder khola
    → saari .jsonl files ki timestamps dekhi
    → sabse naya timestamp = most recent session
    → xyz789.jsonl load ki → history Claude ko gayi
```

---

### Timestamp Kab Update Hoti Hai?

```
Query 1 chali:
    abc123.jsonl mein message likha gaya
    → OS ne timestamp update kiya: "2026-06-04 03:45 PM"

Query 2 chali (usi session mein):
    abc123.jsonl mein phir message add hua
    → OS ne timestamp update kiya: "2026-06-04 03:46 PM"
```

Jo session abhi recently use ho rahi thi, uski file ka timestamp sabse naya hoga — SDK wahi file resume karta hai.

---

### Simple Code

```python
# // Author: Zain Ali
import asyncio
from claude_agent_sdk import query, ResultMessage, ClaudeAgentOptions

# ── Run 1: Pehli baar chalao ──────────────────────────────
async def run_first():
    async for message in query(
        prompt="Python mein add function likho",
        options=ClaudeAgentOptions(allowed_tools=["Write"]),
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print("Run 1 Response:", message.result)
            print("Session ID:", message.session_id)

asyncio.run(run_first())
```

```python
# // Author: Zain Ali
# ── Run 2: Program band kiya, dobara chalaya ──────────────
async def run_second():
    async for message in query(
        prompt="ab subtract function bhi add karo",
        options=ClaudeAgentOptions(
            allowed_tools=["Write", "Edit"],
            continue_conversation=True,   # SDK khud last session dhundhe ga
        ),
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print("Run 2 Response:", message.result)

asyncio.run(run_second())
```

---

### Teen Approaches — Side by Side

```
ClaudeSDKClient:
    async with ClaudeSDKClient() as client:
        await client.query("Q1")    ← ek program run mein
        await client.query("Q2")    ← session internally track

resume=session_id:
    query(..., resume="abc123")     ← ID manually track karni hogi
                                      specific session resume

continue_conversation=True:
    query(..., continue_conversation=True)  ← koi ID nahi
                                              SDK khud last session dhundhe
```

---

### Kab Use Karo

| Situation | Approach |
|---|---|
| Ek program, multiple queries | `ClaudeSDKClient` |
| Program restart, simple 1 session | `continue_conversation=True` |
| Multiple users, specific session chahiye | `resume=session_id` |

---

### Important Note

```
continue_conversation=True → sabse RECENT timestamp wali session resume karta hai

Agar specific session chahiye → resume=session_id use karo
```

---

## Session File Kahan Hoti Hai?

```
Windows:
C:\Users\ZAIN ALI\.claude\projects\E--claude-agents-sdk\
    └── 15d357bd-f279-4449.jsonl

Linux/Mac:
~/.claude/projects/<encoded-cwd>/
    └── <session-id>.jsonl
```

**Encoded CWD:** Directory path mein har non-alphanumeric character `-` se replace hota hai.
`E:\claude_agents_sdk` → `E--claude-agents-sdk`

---

## ClaudeSDKClient — Poora Working Code

```python
# // Author: Zain Ali
import asyncio
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)

def print_response(message):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print(block.text)
    elif isinstance(message, ResultMessage):
        cost = f"${message.total_cost_usd:.4f}" if message.total_cost_usd else "N/A"
        print(f"[Done: {message.subtype} | Cost: {cost}]")

async def main():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Edit", "Glob", "Grep"],
    )

    async with ClaudeSDKClient(options=options) as client:
        # Query 1: naya session bana
        await client.query("Analyze the auth module")
        async for message in client.receive_response():
            print_response(message)

        # Query 2: same session mein automatically continue
        await client.query("Now refactor it to use JWT")
        async for message in client.receive_response():
            print_response(message)

asyncio.run(main())
```

---

## Summary Table

| Feature | `query()` | `ClaudeSDKClient` |
|---|---|---|
| Session per call | Naya banta hai | Ek hi, internally track |
| History | Nahi milti | Milti hai |
| Session ID track karna | Khud karo | SDK karta hai |
| Kab use karo | Single task | Multi-turn conversation |

---

## Ek Line Summary

> `ClaudeSDKClient` internally session_id yaad rakhta hai — pehli query pe session banta hai, baaki sab queries usi session mein resume hoti hain, aur history automatically disk se load hoti hai.

---

*Source: https://code.claude.com/docs/en/agent-sdk/sessions*
