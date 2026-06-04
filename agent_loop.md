# Claude Agent SDK — Agent Loop Complete Notes

---

## Agent Loop kya hai?

Yeh ek **cycle** hai jo tab tak chalti rehti hai jab tak Claude apna kaam poora nahi kar leta.

```
Prompt → Claude socha → Tool use kiya → Result aya → Claude phir socha → Tool use kiya → ... → Khatam
```

---

## Loop ke 5 Steps

```
┌─────────────────────────────────────────────┐
│              AGENT LOOP                      │
│                                              │
│  1. Prompt receive hua                       │
│         ↓                                    │
│  2. Claude ne evaluate kiya                  │
│     (text likha ya tool call kiya)           │
│         ↓                                    │
│  3. SDK ne tool execute kiya                 │
│         ↓                                    │
│  4. Result wapas Claude ko gaya              │
│         ↓                                    │
│  5. Step 2 pe wapas gaya (repeat)            │
│         ↓                                    │
│     Jab koi tool call nahi → KHATAM          │
│         ↓                                    │
│     ResultMessage aya                        │
└─────────────────────────────────────────────┘
```

---

## Turn kya hota hai?

**Ek Turn** = Claude ne output diya (tool calls ke saath) → SDK ne tools chalaye → Result Claude ko gaya.

Real example — `"Fix the failing tests in auth.ts"`:

```
Turn 1: Claude → Bash("npm test") chalao
        SDK ne chalaya → 3 tests fail ka result aya

Turn 2: Claude → Read("auth.ts") aur Read("auth.test.ts") chalao
        SDK ne chalaya → file contents aye

Turn 3: Claude → Edit("auth.ts") fix karo, phir Bash("npm test")
        SDK ne chalaya → 3 tests pass

Final:  Claude → "Fixed the auth bug, all tests pass." (koi tool nahi)
        ResultMessage → khatam
```

**4 turns lagay — 3 tool wale, 1 final text.**

---

## Message Types — Poori List

Loop ke dauran SDK yeh messages yield karta hai:

| Message | Kab aata hai | Kya hota hai andar |
|---|---|---|
| `SystemMessage` | Sabse pehle | Session start, tools list, model info |
| `AssistantMessage` | Har turn ke baad | Claude ka text + tool calls |
| `UserMessage` | Har tool execute hone ke baad | Tool ka result Claude ko wapas |
| `ResultMessage` | Bilkul aakhir mein | Final answer, cost, turns, session_id |
| `StreamEvent` | Sirf streaming enable ho tab | Token by token text |

---

## Tool Execution — Parallel ya Sequential?

```
Read-only tools  → PARALLEL chalte hain (ek saath)
├── Read
├── Glob
└── Grep

State-change tools → SEQUENTIAL chalte hain (ek ek karke)
├── Edit
├── Write
└── Bash
```

**Kyun?** Edit/Write ek saath chalein toh file corrupt ho sakti hai. Isliye ek ek karke.

---

## Loop ko Control Karna

```python
options = ClaudeAgentOptions(
    max_turns=30,           # zyada se zyada 30 turns
    max_budget_usd=0.50,    # zyada se zyada 50 cents
    effort="high",          # kitna sochna hai
)
```

### `max_turns` ka 3-Step Cycle

**1 max_turn = yeh 3 steps poore hone pe:**
```
Step 1: Claude ko request gayi → Claude ne kaha "Read aur Bash karo"
Step 2: SDK ne tools chalaye
Step 3: Tool results wapas Claude ko gaye
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
= 1 max_turn ✅
```

**`max_turns=2` ka matlab:**
```
Cycle 1 (3 steps complete) = max_turn 1  ✅
Cycle 2 (3 steps complete) = max_turn 2  ✅
Cycle 3 shuru hone se pehle = RUKJA ❌
```

**Effort levels:**

| Level | Kab use karo |
|---|---|
| `"low"` | Simple kaam — file dhundho, list karo |
| `"medium"` | Normal editing |
| `"high"` | Complex debugging, refactoring |
| `"max"` | Bahut mushkil multi-step problems |

---

## Context Window — Memory ki Tarah

Context window = Claude ki **working memory** — session mein jo kuch bhi hua sab yahan hota hai.

```
System prompt          → hamesha hota hai
CLAUDE.md             → session start pe load hota hai
Tool definitions      → hamesha hoti hain
Conversation history  → har turn ke saath barhta hai  ← PROBLEM yahan
Tool outputs          → bari files bahut jagah lete hain
```

Jab context window bhar jaye → **Automatic Compaction** hoti hai:
- Purani history summarize ho jati hai
- Nayi jagah banti hai
- SDK ek `SystemMessage (subtype: compact_boundary)` yield karta hai

---

## ResultMessage ke Subtypes

```python
if isinstance(message, ResultMessage):
    if message.subtype == "success":
        print(message.result)            # kaam ho gaya ✅

    elif message.subtype == "error_max_turns":
        print("turns khatam ho gaye")    # limit hit ❌

    elif message.subtype == "error_max_budget_usd":
        print("budget khatam")           # paise khatam ❌

    elif message.subtype == "error_during_execution":
        print("beech mein error aya")    # crash ❌
```

**`message.result`** sirf `"success"` mein hota hai — baaki mein `None`.

---

## Poora Production-Ready Code

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def run_agent():
    async for message in query(
        prompt="Find and fix the bug in auth module",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Bash", "Glob", "Grep"],
            max_turns=30,
            effort="high",
        ),
    ):
        if isinstance(message, ResultMessage):

            if message.subtype == "success":
                print(f"Done: {message.result}")

            elif message.subtype == "error_max_turns":
                print(f"Turns khatam. Session: {message.session_id}")

            elif message.subtype == "error_max_budget_usd":
                print("Budget khatam ho gaya")

            if message.total_cost_usd:
                print(f"Cost: ${message.total_cost_usd:.4f}")

asyncio.run(run_agent())
```

---

## `num_turns` vs `max_turns` — Fark kya hai?

Yeh do alag cheezein hain — mix mat karo:

```
num_turns   → batata hai kitne turns HOWE  (reporting)
max_turns   → LIMIT lagata hai             (control)
```

---

### `num_turns` — Har LLM Request Count Hoti Hai

`ResultMessage.num_turns` mein har LLM request count hoti hai — tool ho ya na ho.

```python
# Simple query — koi tool nahi
prompt = "Hi! My name is Zain."

# Output:
# Total Turns: 1   ← 1 LLM request gayi, 1 response aya
```

**Proof:** Actual run pe `num_turns = 1` aya bina kisi tool ke.

---

### `max_turns` — Sirf Tool-Use Turns Limit Karta Hai

`max_turns` sirf woh turns count karta hai jahan Claude ne tool call kiya.

```
"Hi Zain" query — koi tool nahi:
    num_turns = 1    ← 1 LLM request
    max_turns = 0    ← koi tool nahi, limit affect nahi hui

"Read main.py" query — 1 tool call:
    num_turns = 2    ← 1 tool turn + 1 final text turn
    max_turns = 1    ← sirf tool-use turn count hua
```

---

### Real Example — max_turns=2 lagao:

```
Turn 1: Claude → Bash("npm test")     ← max_turns count: 1
Turn 2: Claude → Read("auth.ts")      ← max_turns count: 2  ← LIMIT HIT, RUKJA
Turn 3: Claude → Edit + Bash          ← yahan pahuncha hi nahi
Final:  Claude → "Fixed!" (text only) ← max_turns count nahi hota
```

---

### Simple Code — Turns Check Karna:

```python
import asyncio
from claude_agent_sdk import query, ResultMessage

async def main():
    async for message in query(prompt="Hi! My name is Zain."):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(f"Total Turns: {message.num_turns}")
            print(message.result)

asyncio.run(main())
```

---

### Summary Table:

| | `num_turns` | `max_turns` |
|---|---|---|
| Kya karta hai | Kitne turns howe batata hai | Limit lagata hai |
| Kya count karta hai | Har LLM request | Sirf tool-use turns |
| Kahan milta hai | `ResultMessage.num_turns` | `ClaudeAgentOptions(max_turns=30)` |
| Simple text query | 1 | 0 |
| 1 tool call query | 2 | 1 |

---

## Ek Line Summary

> Agent Loop = Claude sochta hai → tool chalata hai → result dekhta hai → phir sochta hai → tab tak jab tak kaam khatam na ho.
