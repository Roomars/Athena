import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.memory import memory
from core.ollama import chat, chat_stream
from core import brain, watcher


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Avvia il cervello in background all'avvio
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _init_brain)
    yield
    watcher.stop()


def _init_brain():
    try:
        count = brain.index_vault()
        watcher.start()
        print(f"[brain] {count} chunks indicizzati — watcher attivo")
    except Exception as e:
        print(f"[brain] errore init: {e}")


app = FastAPI(title="Athena", lifespan=lifespan)

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


def _build_rag_context(query: str) -> str:
    results = brain.search(query, n_results=4)
    if not results:
        return ""
    parts = [f"[{r['source']}]\n{r['text']}" for r in results]
    return "---\nContesto dal vault:\n" + "\n\n".join(parts) + "\n---"


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Messaggio vuoto")

    rag = _build_rag_context(req.message)
    user_msg = f"{rag}\n\n{req.message}" if rag else req.message
    memory.add("user", user_msg)

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


@app.get("/brain/stats")
async def brain_stats():
    return brain.stats()
