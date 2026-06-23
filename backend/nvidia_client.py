import json
from typing import AsyncIterator, Any
import httpx

class LLMClient:
    """Async wrapper over any OpenAI-compatible /chat/completions endpoint."""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        if not self.api_key:
            raise RuntimeError("API key is missing for the selected provider.")

    async def stream_chat_completion(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.6,
        top_p: float = 0.95,
        max_tokens: int = 4096,
    ) -> AsyncIterator[dict]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=30.0)) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise RuntimeError(f"API error {resp.status_code}: {body.decode(errors='ignore')}")
                
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        yield {"type": "finish", "reason": "stop"}
                        return
                    
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                        
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                        
                    choice = choices[0]
                    delta = choice.get("delta", {})
                    finish_reason = choice.get("finish_reason")

                    if delta.get("content"):
                        yield {"type": "text_delta", "text": delta["content"]}

                    for tc in delta.get("tool_calls", []) or []:
                        idx = tc.get("index", 0)
                        fn = tc.get("function", {})
                        yield {
                            "type": "tool_call_delta",
                            "index": idx,
                            "id": tc.get("id", ""),
                            "name": fn.get("name", ""),
                            "args_delta": fn.get("arguments", ""),
                        }

                    if finish_reason:
                        yield {"type": "finish", "reason": finish_reason}