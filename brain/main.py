import atexit
import logging

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

from .logging_config import setup_logging
from .settings import load as load_settings
from .ws_handler import handle_ws

setup_logging()
load_settings()

log = logging.getLogger("main")
app = FastAPI(title="Ari Brain", version="0.1.0")


@app.on_event("startup")
async def startup():
    log.info("Ari daemon avviato — porta 8765")


@app.on_event("shutdown")
async def shutdown():
    log.info("Ari daemon in shutdown")


@atexit.register
def _cleanup():
    log.info("cleanup atexit eseguito")


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "version": "0.1.0", "fase": 1})


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await handle_ws(ws)
