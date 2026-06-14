import asyncio
import atexit
import logging

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

from .logging_config import setup_logging
from .settings import load as load_settings
from .llm import engine, MODEL_PRIMARY
from .ws_handler import handle_ws, manager

setup_logging()
load_settings()

log = logging.getLogger("main")
app = FastAPI(title="Ari Brain", version="0.2.0")


@app.on_event("startup")
async def startup():
    log.info("Ari daemon avviato — porta 8765")

    # Salva il loop del thread principale — usato dal callback nel thread MLX
    main_loop = asyncio.get_event_loop()

    def on_model_ready(model_id: str):
        async def _notify():
            await manager.send({"type": "model_ready", "model": model_id})
        asyncio.run_coroutine_threadsafe(_notify(), main_loop)

    engine.on_ready.append(on_model_ready)
    engine.load_async(MODEL_PRIMARY)


@app.on_event("shutdown")
async def shutdown():
    log.info("Ari daemon in shutdown")


@atexit.register
def _cleanup():
    log.info("cleanup atexit eseguito")


@app.get("/health")
async def health():
    return JSONResponse({
        "status": "ok",
        "version": "0.2.0",
        "fase": 2,
        "model": engine.model_id,
        "model_ready": engine.is_ready,
    })


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await handle_ws(ws)
