import asyncio
from claude_agent_sdk import query, ResultMessage, AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, TextBlock




# print Final Result:
# async def main():
#     async for message in query(prompt="Read main.py and tell me what it does", options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Glob"], max_turns=3)):
#         if isinstance(message, AssistantMessage):
#             print(f"\n\n Assistant Message: {message.content}")

#         if isinstance(message, ResultMessage) and message.subtype=="success":
#             print(f"Total Turns: {message.num_turns}")
#             print(f"Max Turns: {3}")
#             print(message.result)



# # print Assistant Message: agent progress.
# async def main():
#     async for message in query(prompt="Write 15 lines on the benefits of Agentic AI."):
#         if isinstance(message, AssistantMessage):
#             for block in message.content:
#                 if hasattr(block, "text"):
#                     print(block.text)


# print all agents Events:
# async def main():
#     async for message in query(prompt="Write 15 lines on the benefits of Agentic AI."):
#         print(message)



# Loading Claude.md file in SDK:
# async def main():
#     async for message in query(
#         prompt="My name is Sameer! how are you." , 
#         options=ClaudeAgentOptions(allowed_tools=["Read", "Write", "Bash", "Edit"])
#     ):
#         # if isinstance(message, AssistantMessage):
#         #     print("Assistant Message -->", message.content)
        
#         if isinstance(message, ResultMessage):
#             print("\n\n Final Response -->", message.result)


    
#     async for message in query(
#         prompt="What is my name please tell me my name!"
#     ):
#         if isinstance(message, ResultMessage) and message.subtype == "success":
#             print("\n\n", message.result)




# -------------------------

# <---------  !) Manage Session and Context: maintain a conversation with context across multiple queries. --------->

# 1) session manage with ClaudeSDKClient:

# async def main():

#     options = ClaudeAgentOptions(
#         allowed_tools=["Read", "Write", "Glob", "Grep"],
#     )

#     async with ClaudeSDKClient(options=options) as client:
#         await client.query("My brother name is Sarim!")
#         async for message in client.receive_response():
#             if isinstance(message, ResultMessage) and message.subtype == "success":
#                 print(message.result)

#             # print(message)


#         await client.query("Whats my bro name & tell me whats my first message! also tell me how you mangaing conversation history how you catch previous messeage!")
#         async for message in client.receive_response():
#             if isinstance(message, ResultMessage) and message.subtype == "success":
#                 print("\n\n", message.result)

#             # print(message)

        
#         await client.query("What is my most recent message?")
#         async for message in client.receive_response():
#             if isinstance(message, ResultMessage) and message.subtype == "success":
#                 print(message.result)



# ------------------



# 2. Session resume with session id:
# async def main():
#     session_id = None

#     # Fix 1: WebSearch tool diya taake real-time news mil sake
#     async for message in query(
#         prompt="tell me most important today AI news",
#         options=ClaudeAgentOptions(allowed_tools=["WebSearch"]),
#     ):
#         if isinstance(message, ResultMessage) and message.subtype == "success":
#             print("\n\n SESSION ID  -------->", message.session_id)
#             session_id = message.session_id
#             print("\n\n RESPONSE   -------->", message.result)

#     # Fix 2: session_id return karo taake bahar use ho sake (resume ke liye)


#     async for message in query(prompt="what is my previous message and also make linkedin post which is about the most impotrant develpment or business upadte in AI", options=ClaudeAgentOptions(resume=session_id)):
#         if isinstance(message, ResultMessage) and message.subtype == "success":
#             print("\n\n RESPONSE 2 -------->", message.result)

#     return session_id

# session_id = asyncio.run(main())
# print("\n\n After REturn SEssion id :", session_id)



# -------------------------------




# # 3. Session manage with Fork feature:
# async def main():
#     session_id = None
#     fork_session_id = None

#     async for message in query(
#         prompt="create addition.py file and write add function ok",
#         options=ClaudeAgentOptions(allowed_tools=["Read", "Write", "Bash", "Glob", "Edit"])
#     ):
#         if isinstance(message, ResultMessage) and message.subtype == "success":
#             print(message.result)
#             print(message.session_id)
#             session_id = message.session_id


#     async for message in query(
#         prompt="add error handling in this function",
#         options=ClaudeAgentOptions(allowed_tools=["Bash", "Glob", "Read", "Write", "Edit"], resume=session_id, fork_session=True)
#     ):
#         if isinstance(message, ResultMessage) and message.subtype == "success":
#             print("\n\n", message.result)
#             print("\n\n", message.session_id)
#             fork_session_id = message.session_id
        
#     return [session_id , fork_session_id]



# session_id , fork_session_id = asyncio.run(main())

# print("Session ID: ", session_id)
# print("FORK Session ID: ", fork_session_id)




# -------------------




# 4. Continue_conversation with most recent session:
# async def main():
#     async for message in query(
#         prompt="Add only multiplication function in addition.py file without error handling!",
#         options=ClaudeAgentOptions(allowed_tools=["Read", "Bash", "Write", "Edit", "Glob"])
#     ):
#         if isinstance(message, ResultMessage) and message.subtype == "success":
#             print("\n\n RESPONSE 1:" , message.result)
#             print("\n\n SESSION ID:", message.session_id)

    
#     async for message in query(
#         prompt="Add error handling in it", 
#         options=ClaudeAgentOptions(allowed_tools=["Read", "Write", "Edit", "Bash", "Glob"], continue_conversation=True)
#     ):
#         if isinstance(message, ResultMessage) and message.subtype == "success":
#             print("\n\n RESPONSE 2:" , message.result)
#             print("\n\n SESSION ID 2:", message.session_id)




# asyncio.run(main())


             
# --------------


## Streaming Input - async generator to stream input to the agent in real-time:
# // Author: Zain Ali
async def main():

    async def generator_input():
        yield {
            "type": "user", 
            "message": {
                "role": "user", 
                "content": "Hi my name is Zain and I am from Pakistan!"
            }
        }

        await asyncio.sleep(2)

        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": "This is my request 2 , IN streaming input in claude agent sdk had qeury function second time call to process this second reponse?"
            }
        }


    options = ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Edit", "Write", "Bash"], max_turns=10)

    async with ClaudeSDKClient(options) as client:
        await client.query(generator_input())

        turn = 0
        while True:
            try:
                async with asyncio.timeout(30.0):
                    async for message in client.receive_response():
                        if isinstance(message, AssistantMessage):
                            for block in message.content:
                                if isinstance(block, TextBlock):
                                    print("\n\n [=] RESPONSE:", block.text)
                        elif isinstance(message, ResultMessage) and message.subtype == "success":
                            turn += 1
                            print(f"\n\n [=] Turn {turn} completed!")
            except (asyncio.TimeoutError, StopAsyncIteration):
                break



asyncio.run(main())

