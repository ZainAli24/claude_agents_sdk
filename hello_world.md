# Claude Agent SDK — Hello World & Streaming Events Concept

## Mera Samjha Hua Concept

`query()` function se Agent ko run kiya. Agent ne jo jo kaam kiye, actions liye,
wo sab events/classes mein record hote hain. Jab jab jo event perform hota hai,
wo streaming mein message ban ke return hota hai. `async for` loop unhe ek ek
karke pakad ta hai.

---

## Agent Loop ka Flow

```
query(prompt="...")
       |
       v
  Agent Loop Shuru
       |
       |---> Event 1 → RateLimitEvent    (kya API limit hai?)
       |
       |---> Event 2 → SystemMessage     (session start, tools load)
       |
       |---> Event 3 → AssistantMessage  (Claude soch raha hai - ThinkingBlock)
       |
       |---> Event 4 → AssistantMessage  (Claude ka jawab - TextBlock)
       |
       |---> Event 5 → ResultMessage     (kaam khatam, cost, time)
       |
  Agent Loop Khatam
```

---

## 5 Events ki Detail

### 1. `RateLimitEvent`
SDK ne pehle check kiya — "kya API use ho sakti hai?"
```
status='allowed' → haan, chalo
```

### 2. `SystemMessage`
Session start hua, tools load hue, model set hua.
```
model='claude-sonnet-4-6'
tools=['Read', 'Edit', 'Bash', ...]
```

### 3. `AssistantMessage` (ThinkingBlock)
Claude andar se soch raha tha — yeh private soch hai, user ko normally nahi dikhti.
```
thinking="The user is introducing themselves. I'll respond warmly..."
```

### 4. `AssistantMessage` (TextBlock)
Claude ka actual jawab — yahi screen pe dikhta hai.
```
text="Hey Zain! 👋 Welcome!..."
```

### 5. `ResultMessage`
Sab khatam. Summary info:
```
duration_ms=4402       → 4.4 seconds laga
total_cost_usd=0.059   → 6 cents laga ek message mein
num_turns=1            → Claude ne 1 baar socha
```

---

## Key Concept (Ek Line Mein)

> Har action/event ek class object ban ke stream mein aata hai, ek ek karke.
> `async for` loop unhe pakad ke print karta hai.


---

## Common Mistake — `message.subtype` Direct Access

### Galat Code ❌
```python
async for message in query(prompt="..."):
    if message.subtype == 'success' and message.result:
        print(message)
```

**Problem:** Har message mein `subtype` nahi hota!

```
RateLimitEvent   → subtype nahi hai  ← AttributeError crash!
SystemMessage    → subtype nahi hai  ← AttributeError crash!
AssistantMessage → subtype nahi hai  ← AttributeError crash!
ResultMessage    → subtype HAI ✓
```

Loop pehle `RateLimitEvent` pe aata hai — `message.subtype` access karo — **crash!**

---

### Sahi Code ✅ — `isinstance()` use karo
```python
import asyncio
from claude_agent_sdk import query, ResultMessage

async def main():
    async for message in query(prompt="..."):
        if isinstance(message, ResultMessage) and message.subtype == 'success':
            print(message.result)

asyncio.run(main())
```

---

### Simple Rule
```
Pehle CHECK karo  → yeh message kaunsi class ka hai? (isinstance)
Phir ACCESS karo  → us class ka attribute. (.subtype, .result)
```

---

## Streaming vs Final Response — Kya Fark Hai?

### Level 1: Events Stream (async for loop)
```
RateLimitEvent   ──► aya
SystemMessage    ──► aya
AssistantMessage ──► aya (Claude likh raha hai...)
AssistantMessage ──► aya (Claude aur likh raha hai...)
ResultMessage    ──► aya (khatam)
```
Yeh events **ek ek karke** stream hote hain. ✅

---

### Level 2: Final Response (`message.result`)
```python
if isinstance(message, ResultMessage) and message.subtype == "success":
    print(message.result)  # poora text EK SAATH aata hai
```
`message.result` **stream nahi hota** — ResultMessage ke saath ek dam poora text milta hai
jab Agent ka kaam bilkul khatam ho jata hai.

---

### Agar Streaming Text Chahiye — `AssistantMessage` use karo
```python
from claude_agent_sdk import query, AssistantMessage

async for message in query(prompt="..."):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if hasattr(block, "text"):
                print(block.text, end="", flush=True)  # har chunk seedha print
```
Yahan text **chunks mein** aata hai — jaise ChatGPT mein words ek ek karke dikhte hain.

---

### Summary Table

| | Kya hota hai |
|---|---|
| `async for` events | Stream ✅ ek ek karke |
| `AssistantMessage` text | Stream ✅ chunks mein |
| `ResultMessage.result` | Stream nahi ❌ end mein ek dam poora |

---

## `AssistantMessage` ke Andar Kya Hota Hai?

`AssistantMessage` mein **dono cheezein** aati hain — LLM ka text jawab bhi aur tool call bhi.

`AssistantMessage.content` ek list hai jis mein yeh blocks ho sakte hain:

```
AssistantMessage.content = [
    ThinkingBlock  → Claude ki andar ki private soch
    TextBlock      → Claude ka text jawab (LLM response)
    ToolUseBlock   → Claude ne tool call kiya (action liya)
]
```

---

### Real Example — Agent "Fix bugs" kare toh:

```
AssistantMessage → content: [TextBlock]
                   text: "utils.py padh ke dekhta hun..."

AssistantMessage → content: [ToolUseBlock]
                   name: "Read"                    ← tool call kiya
                   input: {"file": "utils.py"}

AssistantMessage → content: [TextBlock]
                   text: "Bug mila! Line 5 pe division by zero..."

AssistantMessage → content: [ToolUseBlock]
                   name: "Edit"                    ← tool call kiya
                   input: {"file": "utils.py", "changes": ...}

ResultMessage    → "Done: success"
```

---

### `AssistantMessage` kab useful hai vs `ResultMessage`?

| | Kab use karo |
|---|---|
| `ResultMessage.result` | Sirf final answer chahiye — simple queries |
| `AssistantMessage` | Agent tools use kar raha ho — beech ka progress bhi dekhna ho |

---

### Simple Rule

```
AssistantMessage
├── TextBlock    → Claude bol raha hai / soch raha hai
└── ToolUseBlock → Claude action le raha hai (tool call)

ResultMessage    → sab kuch khatam, final answer
```

