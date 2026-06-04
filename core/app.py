from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.memory import memory
from core.ollama import chat, chat_stream

app = FastAPI(title="Athena")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    message: str
    stream: bool = False


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Messaggio vuoto")

    memory.add("user", req.message)

    if req.stream:
        async def generate():
            full = ""
            async for chunk in chat_stream(memory.to_messages()):
                full += chunk
                yield chunk
            memory.add("assistant", full)

        return StreamingResponse(generate(), media_type="text/plain")

    reply = await chat(memory.to_messages())
    memory.add("assistant", reply)
    return {"reply": reply}


@app.delete("/chat")
async def clear_memory():
    memory.clear()
    return {"status": "ok"}
