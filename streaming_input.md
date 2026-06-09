# Streaming Input — Claude Agent SDK (Python)

## Do Input Modes

| Mode | Kab Use Karein |
|---|---|
| **Streaming Input** (Recommended) | Multiple messages, images, interrupt, persistent session |
| **Single Message** | Ek sawaal ek jawab, stateless (lambda etc.) |

---

## Streaming Input Kya Hai

`ClaudeSDKClient` ke saath ek **persistent connection** khulta hai. Tum ek `AsyncGenerator` banate ho jo ek ek `yield` karke messages bhejta hai. Claude ka session dono yields ke beech **zinda rehta hai** — context maintain hota hai.

```
AsyncGenerator (message_generator)
    |
    yield 1  ──►  Claude  ──►  jawab 1
    yield 2  ──►  Claude  ──►  jawab 2  (yield 1 yaad hai)
```

---

## AsyncGenerator — yield Kya Hai

Normal function sab kuch ek baar `return` karta hai.  
`AsyncGenerator` ek ek piece `yield` karta hai — jab maango tab.

```python
async def message_generator():
    yield {"type": "user", "message": {"role": "user", "content": "Message 1"}}
    await asyncio.sleep(2)   # real app mein: user input, API call, condition
    yield {"type": "user", "message": {"role": "user", "content": "Message 2"}}
```

`query()` is generator ko receive karta hai aur dono yields Claude ko bhej deta hai.  
`query()` khatam hone ke baad dono yields Claude ke paas **pending** hain — jawab queue mein ready.

---

## receive_response() Ki Stopping Behavior

`receive_response()` pehli `ResultMessage` milte hi **khud band ho jaati hai**.

```
receive_response() chali
    AssistantMessage  →  yield kiya
    AssistantMessage  →  yield kiya
    ResultMessage     →  yield kiya  →  BAND  ✗
```

Yeh `ResultMessage` Claude ka signal hai: "mera is turn ka jawab poora hua."  
Lekin agar generator mein 2 yields hain toh **dono ke alag alag ResultMessage** aate hain.  
Ek `receive_response()` call sirf **pehle wala** pakad sakti hai — doosra miss.

---

## Old Code — Problem

```python
# // Author: Zain Ali
await client.query(message_generator())   # yield 1 aur yield 2 dono gaye

# ❌ BROKEN — sirf yield 1 ka jawab milega
async for message in client.receive_response():
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print(block.text)
# yield 2 ka jawab queue mein pada raha — koi sun-ne wala nahi tha
```

**Kya hua:**
```
query()  →  yield 1 gaya, yield 2 gaya

receive_response() chali:
    yield 1 ka jawab aaya  →  print kiya
    ResultMessage aaya     →  receive_response() BAND HO GAYI

yield 2 ka jawab aaya  →  koi sun-ne wala nahi  →  SILENTLY LOST ✗
```

Koi error nahi aata — output simply miss ho jaata hai. Yeh silent bug hai.

---

## Fixed Code — while Loop Pattern

```python
# // Author: Zain Ali
await client.query(message_generator())   # yield 1 aur yield 2 dono gaye

# ✅ SAHI — while loop receive_response() ko baar baar call karta hai
turn = 0
while True:
    try:
        async with asyncio.timeout(30.0):             # 30 sec ka alarm
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
```

**Kya hua:**
```
query()  →  yield 1 gaya, yield 2 gaya

while loop iteration 1:
    receive_response() chali:
        yield 1 ka jawab aaya  →  print "[Turn 1] Claude: ..."
        ResultMessage aaya     →  turn = 1  →  receive_response() BAND
    (koi error nahi — while loop dobara chala)

while loop iteration 2:
    receive_response() dobara call:
        yield 2 ka jawab aaya  →  print "[Turn 2] Claude: ..."
        ResultMessage aaya     →  turn = 2  →  receive_response() BAND
    (koi error nahi — while loop dobara chala)

while loop iteration 3:
    receive_response() call:
        30 second wait...
        kuch nahi aaya  →  TimeoutError  →  BREAK  →  loop khatam ✓
```

---

## while Loop Ki Zaroorat Kyun — Ek Line Mein

```
while loop = receive_response() ko baar baar call karne ki machine
             jab tak saare yields ke jawab na aa jayein
```

- `while True` = darwaze pe khara raho
- `asyncio.timeout(30.0)` = 30 second ka alarm — agar kuch nahi aaya toh ghar jao
- `break` = loop khatam karo

---

## receive_response() vs receive_messages()

| Method | Kab ruke | Kab use karein |
|---|---|---|
| `receive_response()` | Pehli `ResultMessage` pe | Ek yield ke jawab ke liye, ya while loop mein |
| `receive_messages()` | Kabhi nahi — manually cancel karo | Sari messages indefinitely sunni ho |

---

## Old vs New — Side by Side

```python
# ❌ OLD — sirf yield 1 ka jawab
await client.query(message_generator())
async for message in client.receive_response():
    ...
# yield 2 silently lost


# ✅ NEW — dono yields ke jawab
await client.query(message_generator())
while True:
    try:
        async with asyncio.timeout(30.0):
            async for message in client.receive_response():
                ...
    except (asyncio.TimeoutError, StopAsyncIteration):
        break
```

---

## Verified Output (Tested)

Input:
- Yield 1: `"I am learning Python. My favorite number is 42 and my pet's name is Bruno."`
- Yield 2: `"What am I learning? What is my favorite number? What is my pet's name?"`

Output:
```
[Turn 1] Claude: That's awesome that you're learning Python! ...
--- Turn 1 complete ---

[Turn 2] Claude: Based on what you shared earlier:
- Learning: Python
- Favorite Number: 42
- Pet's Name: Bruno
--- Turn 2 complete ---
```

Yield 2 mein koi context repeat nahi kiya gaya — Claude ne yield 1 ki memory apne paas rakhi.

---

## Official Repo Reference

- Sahi pattern: `examples/streaming_mode.py` → `example_async_iterable_prompt()`
- Comment in repo: *"the CLI may group multiple user messages into fewer ResultMessages, so we cannot assume a 1:1 mapping"*
- PR contributed: https://github.com/anthropics/claude-agent-sdk-python/pull/1023
  - `receive_response()` docstring mein multi-yield warning add ki
