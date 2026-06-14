import json
import logging
from fastapi import WebSocket, WebSocketDisconnect

log = logging.getLogger("ws")

# FASE 1: echo puro — nessun LLM. Verrà sostituito in FASE 2.


class ConnectionManager:
    def __init__(self):
        self.connection: WebSocket | None = None
        self._privacy_mode = False

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connection = ws
        log.info("Swift connesso via WebSocket")

    def disconnect(self):
        self.connection = None
        log.info("Swift disconnesso")

    async def send(self, payload: dict):
        if self.connection:
            await self.connection.send_text(json.dumps(payload))

    @property
    def privacy_mode(self) -> bool:
        return self._privacy_mode


manager = ConnectionManager()


async def handle_ws(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "ping":
                await manager.send({"type": "pong"})

            elif msg_type == "user_input":
                content = msg.get("content", "")
                log.info(f"input ricevuto: {content!r}")
                # FASE 1: echo diretto
                await manager.send({"type": "orb_state", "state": "thinking"})
                await manager.send({
                    "type": "response_chunk",
                    "content": content,
                    "stream": False,
                })
                await manager.send({"type": "response_done", "state": "idle"})

            elif msg_type == "privacy_mode":
                manager._privacy_mode = msg.get("enabled", False)
                state = "attivata" if manager._privacy_mode else "disattivata"
                log.info(f"Privacy Mode {state}")

            else:
                log.warning(f"messaggio sconosciuto: {msg_type}")

    except WebSocketDisconnect:
        manager.disconnect()
    except Exception as e:
        log.error(f"errore WebSocket: {e}")
        manager.disconnect()
