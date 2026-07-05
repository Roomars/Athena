import asyncio
import atexit
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

from .logging_config import setup_logging
from .settings import load as load_settings
from .llm import engine, MODEL_PRIMARY
from .ws_handler import handle_ws, manager
from .tts import tts
from .stt import stt
from .proactive.monitor import monitor_loop
from .proactive.heartbeat import heartbeat_loop
from .stats_monitor import stats_loop
from .memory_extractor import decay_confidence

setup_logging()
load_settings()

log = logging.getLogger("main")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.info("Ari daemon avviato — porta 8765")

    main_loop = asyncio.get_event_loop()

    def on_model_ready(model_id: str):
        async def _notify():
            await manager.send({"type": "model_ready", "model": model_id})
        asyncio.run_coroutine_threadsafe(_notify(), main_loop)

    engine.on_ready.append(on_model_ready)
    engine.load_async(MODEL_PRIMARY)

    stt.load_async()

    asyncio.create_task(monitor_loop(manager, tts))
    asyncio.create_task(stats_loop(manager.send, manager))
    asyncio.create_task(heartbeat_loop(manager.send, tts))

    async def _decay_loop():
        await asyncio.sleep(5)
        while True:
            await asyncio.get_event_loop().run_in_executor(None, decay_confidence)
            await asyncio.sleep(86400)
    asyncio.create_task(_decay_loop())

    yield

    log.info("Ari daemon in shutdown")


@atexit.register
def _cleanup():
    log.info("cleanup atexit eseguito")


app = FastAPI(title="Ari Brain", version="0.2.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return JSONResponse({
        "status":      "ok",
        "version":     "0.2.0",
        "fase":        2,
        "model":       engine.model_id,
        "model_ready": engine.is_ready,
        "mlx_memory":  engine.memory_stats(),
    })


@app.get("/memory")
async def memory_report():
    """Snapshot RAM MLX: active / peak / cache in GB."""
    return JSONResponse(engine.memory_stats())


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await handle_ws(ws)
