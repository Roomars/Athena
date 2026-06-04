import httpx
from typing import AsyncIterator

OLLAMA_BASE = "http://localhost:11434"
MODEL = "qwen3:14b"


async def chat(messages: list[dict]) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE}/api/chat",
            json={"model": MODEL, "messages": messages, "stream": False},
        )
        response.raise_for_status()
        return response.json()["message"]["content"]


async def chat_stream(messages: list[dict]) -> AsyncIterator[str]:
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{OLLAMA_BASE}/api/chat",
            json={"model": MODEL, "messages": messages, "stream": True},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    import json
                    chunk = json.loads(line)
                    if not chunk.get("done"):
                        yield chunk["message"]["content"]
