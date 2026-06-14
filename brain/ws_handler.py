import json
import logging
from fastapi import WebSocket, WebSocketDisconnect

from .llm import engine
from .memory import working_memory
from .prompt import build_system_prompt
from .complexity_router import classify

log = logging.getLogger("ws")


class ConnectionManager:
    def __init__(self):
        self.connection: WebSocket | None = None
        self._privacy_mode = False

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connection = ws
        log.info("Swift connesso via WebSocket")
        # Comunica stato modello
        if engine.is_ready:
            await self.send({"type": "model_ready", "model": engine.model_id})
        else:
            await self.send({"type": "model_loading"})

    def disconnect(self):
        self.connection = None
        log.info("Swift disconnesso")

    async def send(self, payload: dict):
        if self.connection:
            try:
                await self.connection.send_text(json.dumps(payload))
            except Exception:
                pass

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
                content = msg.get("content", "").strip()
                if not content:
                    continue
                log.info(f"input: {content!r}")
                await _respond(content)

            elif msg_type == "privacy_mode":
                manager._privacy_mode = msg.get("enabled", False)
                log.info(f"privacy mode: {manager._privacy_mode}")

            elif msg_type == "clear_memory":
                working_memory.clear()
                await manager.send({"type": "memory_cleared"})

            else:
                log.warning(f"messaggio sconosciuto: {msg_type}")

    except WebSocketDisconnect:
        manager.disconnect()
    except Exception as e:
        log.error(f"errore ws: {e}")
        manager.disconnect()


async def _respond(user_input: str):
    # 1. Classifica complessità → token budget
    tier, max_tokens, use_thinking = classify(user_input)
    log.info(f"tier={tier} max_tokens={max_tokens} thinking={use_thinking}")

    # 2. Aggiunge messaggio utente alla memoria
    working_memory.add("user", user_input)

    # 3. Costruisce il contesto completo
    system = build_system_prompt()
    messages = [{"role": "system", "content": system}] + working_memory.get()[:-1]
    # Nota: l'ultimo messaggio (user) è già nel working_memory,
    # ma lo passiamo come parte della lista completa
    messages = [{"role": "system", "content": system}] + working_memory.get()

    # 4. Segnala a Swift che stiamo elaborando
    await manager.send({"type": "orb_state", "state": "thinking"})

    # 5. Streaming risposta
    full_response = ""
    first_chunk = True

    async for kind, token in engine.stream(messages, max_tokens=max_tokens, thinking=use_thinking):
        if kind == "thinking":
            # Ari sta ragionando — orb rimane in thinking, non streama testo
            continue
        elif kind == "chunk":
            if first_chunk:
                await manager.send({"type": "orb_state", "state": "speaking"})
                first_chunk = False
            full_response += token
            await manager.send({"type": "response_chunk", "content": token, "stream": True})
        elif kind == "done":
            break

    # 6. Salva risposta in memoria
    if full_response.strip():
        working_memory.add("assistant", full_response.strip())

    # 7. Segnala fine
    await manager.send({"type": "response_done", "state": "idle"})
    log.info(f"risposta completata ({len(full_response)} chars)")
