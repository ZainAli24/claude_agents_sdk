# Structured Outputs — Beginner Guide

---

## Structured Output kya hota hai?

Jab aap Claude Agent se kuch poochte ho, toh normally woh **free-form text** deta hai — matlab seedha paragraph ya sentence mein jawab deta hai. Jaise:

```
"Anthropic ek AI company hai jo 2021 mein San Francisco mein bani."
```

Lekin agar aap ye data apni app mein use karna chahte ho (jaise database mein save karna, ya UI mein dikhana), toh aapko us text ko **parse** karna padega — jo mushkil aur error-prone hota hai.

**Structured Output** ka matlab hai ke aap Claude ko batao ke data **kis shape mein** chahiye, aur woh exactly wahi shape mein validated JSON return karega:

```json
{
  "company_name": "Anthropic",
  "founded_year": 2021,
  "headquarters": "San Francisco, CA"
}
```

Ab aap directly `data["company_name"]` likh ke use kar sakte ho — koi parsing nahi, koi guessing nahi.

---

## Kyun Structured Output?

Soch lo aap ek **Recipe App** bana rahe ho. Agent web se recipe lata hai.

**Bina Structured Output ke** — aapko ye milega:
```
Here's a classic chocolate chip cookie recipe!
Prep time: 15 minutes | Cook time: 10 minutes
Ingredients:
- 2 1/4 cups all-purpose flour
...
```
Ab aapko khud "15 minutes" ko number mein convert karna hoga, ingredients alag karne honge — bahut kaam!

**Structured Output ke saath** — aapko ye milega:
```json
{
  "name": "Chocolate Chip Cookies",
  "prep_time_minutes": 15,
  "cook_time_minutes": 10,
  "ingredients": [
    {"item": "flour", "amount": 2.25, "unit": "cups"}
  ]
}
```
Direct use karo UI mein — koi parsing nahi!

---

## Step 1 — Basic Example (JSON Schema se)

Pehle simple tarika: aap khud **JSON Schema** likhte ho jo batata hai data ki shape kya hogi.

```python
# Author: Zain Ali
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

# Step 1: Schema define karo — data ki "shape" batao
schema = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},   # string = text
        "founded_year": {"type": "number"},   # number = integer/float
        "headquarters": {"type": "string"},
    },
    "required": ["company_name"],  # ye field zaroor honi chahiye
}


async def main():
    # Step 2: query() mein output_format pass karo
    async for message in query(
        prompt="Research Anthropic and provide key company information",
        options=ClaudeAgentOptions(
            output_format={"type": "json_schema", "schema": schema}
        ),
    ):
        # Step 3: ResultMessage check karo aur structured_output use karo
        if isinstance(message, ResultMessage) and message.structured_output:
            print(message.structured_output)
            # Output: {'company_name': 'Anthropic', 'founded_year': 2021, ...}


asyncio.run(main())
```

**Kya ho raha hai yahan:**
1. `schema` — aap batate ho "mujhe object chahiye jisme company_name, founded_year, headquarters ho"
2. `output_format` — ye schema `query()` ko dete ho
3. `message.structured_output` — yahan validated dictionary milti hai

---

## Step 2 — Pydantic ke saath (Recommended!)

JSON Schema manually likhna thoda complex hota hai. **Pydantic** ek Python library hai jo aapko **Python classes** se schema banana deti hai — bahut aasaan!

Pehle install karo:
```
pip install pydantic
```

```python
# Author: Zain Ali
import asyncio
from pydantic import BaseModel
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


# Step 1: Pydantic class banao — ye hi tumhara schema hai
class Step(BaseModel):
    step_number: int          # int = poora number
    description: str          # str = text
    estimated_complexity: str  # 'low', 'medium', ya 'high'


class FeaturePlan(BaseModel):
    feature_name: str
    summary: str
    steps: list[Step]   # list of Step objects
    risks: list[str]    # list of strings


async def main():
    async for message in query(
        prompt="Plan how to add dark mode support to a React app.",
        options=ClaudeAgentOptions(
            output_format={
                "type": "json_schema",
                # Pydantic khud JSON Schema generate kar deta hai!
                "schema": FeaturePlan.model_json_schema(),
            }
        ),
    ):
        if isinstance(message, ResultMessage) and message.structured_output:
            # Pydantic se validated typed object banao
            plan = FeaturePlan.model_validate(message.structured_output)

            print(f"Feature: {plan.feature_name}")
            print(f"Summary: {plan.summary}")

            for step in plan.steps:
                print(f"{step.step_number}. [{step.estimated_complexity}] {step.description}")


asyncio.run(main())
```

**Pydantic ke fayde:**
- `plan.feature_name` — seedha property access, dictionary keys nahi
- `FeaturePlan.model_json_schema()` — JSON Schema khud generate ho jata hai
- `model_validate()` — data validate hota hai aur typed object milta hai

---

## Step 3 — Error Handling

Kabhi kabhi agent valid JSON nahi bana pata (schema bohat complex ho, ya prompt unclear ho). Isliye hamesha error check karo:

```python
# Author: Zain Ali
async for message in query(
    prompt="Extract contact info from the document",
    options=ClaudeAgentOptions(
        output_format={"type": "json_schema", "schema": contact_schema}
    ),
):
    if isinstance(message, ResultMessage):
        if message.subtype == "success" and message.structured_output:
            # Sab theek — data use karo
            print(message.structured_output)

        elif message.subtype == "error_max_structured_output_retries":
            # Agent ne try kiya lekin fail ho gaya
            print("Could not produce valid output — schema simplify karo ya prompt clear karo")
```

---

## Real World Example — TODO Finder

Yeh example dikhaata hai ke agent tools use karta hai (Grep, Bash), phir sab kuch ek structured output mein deta hai:

```python
# Author: Zain Ali
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

todo_schema = {
    "type": "object",
    "properties": {
        "todos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "file": {"type": "string"},
                    "line": {"type": "number"},
                    "author": {"type": "string"},  # optional
                    "date": {"type": "string"},    # optional
                },
                "required": ["text", "file", "line"],  # ye teen zaroor hain
            },
        },
        "total_count": {"type": "number"},
    },
    "required": ["todos", "total_count"],
}


async def main():
    async for message in query(
        prompt="Find all TODO comments in this codebase and identify who added them",
        options=ClaudeAgentOptions(
            output_format={"type": "json_schema", "schema": todo_schema}
        ),
    ):
        if isinstance(message, ResultMessage) and message.structured_output:
            data = message.structured_output
            print(f"Found {data['total_count']} TODOs")
            for todo in data["todos"]:
                print(f"{todo['file']}:{todo['line']} - {todo['text']}")
                if "author" in todo:
                    print(f"  Added by {todo['author']} on {todo['date']}")


asyncio.run(main())
```

---

## Quick Summary

| Concept | Matlab |
|---|---|
| `schema` | Data ki shape define karna (kya fields chahiye) |
| `output_format` | Schema ko query mein pass karna |
| `structured_output` | Result message mein validated dictionary |
| `Pydantic BaseModel` | Python class se schema banana — easy aur type-safe |
| `model_json_schema()` | Pydantic class ko JSON Schema mein convert karna |
| `model_validate()` | Dictionary ko typed Pydantic object mein convert karna |
| `subtype == "success"` | Output successfully generate aur validate hua |
| `error_max_structured_output_retries` | Agent valid output nahi bana paya |

---

## Tips — Errors Se Bachne Ke Liye

1. **Schema simple rakho** — shuruaat mein kam fields rakho, baad mein complex banao
2. **Optional fields use karo** — agar agent ke paas sab info na ho toh `required` mein mat rakho
3. **Clear prompt likho** — ambiguous prompt se agent confuse hota hai
