import os
import asyncio
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel
from typing import List, Union, Dict, Any

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Message(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]

class ChatRequest(BaseModel):
    messages: List[Message]
    model_config = {"extra": "ignore"}




# Dummy Tool Definition
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    }
]

async def get_current_weather(location, unit="celsius"):
    """Mock weather function"""
    # Simulate API call latency
    await asyncio.sleep(1) 
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": unit, "forecast": "Rainy"})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": unit, "forecast": "Sunny"})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": unit, "forecast": "Cloudy"})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

async def stream_generator_sse(messages: list):
    current_messages = list(messages)
    
    # 1. First Call to LLM
    stream = await client.chat.completions.create(
        model="gpt-4o",
        messages=current_messages,
        tools=tools,
        tool_choice="auto",
        stream=True,
    )

    tool_calls = {} # {index: {"id": ..., "name": ..., "arguments": ...}}
    
    async for chunk in stream:
        delta = chunk.choices[0].delta
        
        # Handle Content (Streaming Text)
        if delta.content:
            yield f"data: {json.dumps({'type': 'text', 'text': delta.content})}\n\n"
            
        # Handle Tool Calls (Accumulate)
        if delta.tool_calls:
            for tc in delta.tool_calls:
                index = tc.index
                if index not in tool_calls:
                    tool_calls[index] = {"id": "", "name": "", "arguments": ""}
                
                if tc.id:
                    tool_calls[index]["id"] += tc.id
                    # Emit Tool Start Event immediately to UI
                    yield f"data: {json.dumps({'type': 'tool_start', 'toolCallId': tc.id, 'toolName': tc.function.name or 'unknown'})}\n\n"
                
                if tc.function:
                    if tc.function.name:
                         tool_calls[index]["name"] += tc.function.name
                    if tc.function.arguments:
                         tool_calls[index]["arguments"] += tc.function.arguments

    # 2. Process Tool Calls if any
    if tool_calls:
        # Append Assistant Message with Tool Calls to history
        assistant_msg = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": v["id"],
                    "type": "function",
                    "function": {"name": v["name"], "arguments": v["arguments"]}
                } for k, v in tool_calls.items()
            ]
        }
        current_messages.append(assistant_msg)

        # Execute Tools
        for index, tc_data in tool_calls.items():
            func_name = tc_data["name"]
            arguments_str = tc_data["arguments"]
            call_id = tc_data["id"]
            
            try:
                args = json.loads(arguments_str)
                result_content = ""
                
                if func_name == "get_current_weather":
                    result_content = await get_current_weather(**args)
                else:
                    result_content = json.dumps({"error": "Unknown function"})
                
                # Emit Tool Result Event to UI
                yield f"data: {json.dumps({'type': 'tool_result', 'toolCallId': call_id, 'result': json.loads(result_content)})}\n\n"

                # Append Tool Output to history
                current_messages.append({
                    "tool_call_id": call_id,
                    "role": "tool",
                    "name": func_name,
                    "content": result_content,
                })
                
            except Exception as e:
                print(f"Tool Execution Error: {e}")
                current_messages.append({
                    "tool_call_id": call_id,
                    "role": "tool",
                    "name": func_name,
                    "content": str(e),
                })

        # 3. Second Call to LLM (with tool results) - Recursive Stream
        # We need a new stream for the final answer
        stream2 = await client.chat.completions.create(
            model="gpt-4o",
            messages=current_messages,
            stream=True,
        )
        
        async for chunk in stream2:
            delta = chunk.choices[0].delta
            if delta.content:
                 yield f"data: {json.dumps({'type': 'text', 'text': delta.content})}\n\n"

@app.post("/api/chat/sse")
async def chat_endpoint_sse(request: ChatRequest):
    formatted_messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    return StreamingResponse(
        stream_generator_sse(formatted_messages),
        media_type="text/event-stream"
    )
