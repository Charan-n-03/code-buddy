import json
from typing import AsyncIterator
from pathlib import Path
from .nvidia_client import LLMClient
from .tools import TOOL_SCHEMAS, execute_tool
from .sessions import Session
from .config import settings

async def run_agent_loop(session: Session, user_message: str) -> AsyncIterator[dict]:
    session.messages.append({"role": "user", "content": user_message})
    client = LLMClient(api_key=session.api_key, base_url=session.base_url)

    for _ in range(settings.max_iterations):
        try:
            collected_text = ""
            tool_calls: dict[int, dict] = {}

            async for event in client.stream_chat_completion(
                model=session.model,
                messages=session.messages,
                tools=TOOL_SCHEMAS,
            ):
                t = event["type"]
                if t == "text_delta":
                    collected_text += event["text"]
                    yield {"type": "text", "text": event["text"]}
                elif t == "tool_call_delta":
                    idx = event["index"]
                    slot = tool_calls.setdefault(idx, {"id": event["id"] or f"call_{idx}", "name": "", "args_buffer": ""})
                    if event["id"]: slot["id"] = event["id"]
                    if event["name"]: slot["name"] = event["name"]
                    slot["args_buffer"] += event["args_delta"]
                elif t == "finish":
                    pass

            assistant_msg: dict = {"role": "assistant", "content": collected_text or ""}
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {"id": v["id"], "type": "function", "function": {"name": v["name"], "arguments": v["args_buffer"]}}
                    for _, v in sorted(tool_calls.items())
                ]
            session.messages.append(assistant_msg)

            if not tool_calls:
                yield {"type": "done"}
                return

            for idx in sorted(tool_calls):
                tc = tool_calls[idx]
                name = tc["name"]
                raw_args = tc["args_buffer"].strip()
                try:
                    args = json.loads(raw_args) if raw_args else {}
                except json.JSONDecodeError:
                    args = {}
                    result = f"[ERROR] invalid JSON: {raw_args!r}"
                else:
                    yield {"type": "tool_call", "id": tc["id"], "name": name, "args": args}
                    result = execute_tool(name, args, session.workspace)
                yield {"type": "tool_result", "id": tc["id"], "name": name, "result": result}
                session.messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})

        except Exception as e:
            yield {"type": "error", "message": f"{type(e).__name__}: {e}"}
            return

    yield {"type": "error", "message": f"Reached max_iterations={settings.max_iterations}"}