import asyncio
import json
import logging
from fastapi import WebSocket, WebSocketDisconnect

from .llm import engine
from .memory import working_memory
from .prompt import build_system_prompt
from .complexity_router import classify
from .tts import tts
from .skill_router import router as skill_router
from .memory_extractor import extract_and_save, save_episode

log = logging.getLogger("ws")


class ConnectionManager:
    def __init__(self):
        self.connection: WebSocket | None = None
        self._privacy_mode = False

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connection = ws
        log.info("Swift connesso via WebSocket")
        if engine.is_ready:
            await self.send({"type": "model_ready", "model": engine.model_id})
        else:
            await self.send({"type": "model_loading"})
            asyncio.create_task(self._wait_and_notify_ready())

    def disconnect(self):
        self.connection = None
        log.info("Swift disconnesso")

    async def send(self, payload: dict):
        if self.connection:
            try:
                await self.connection.send_text(json.dumps(payload))
            except Exception:
                pass

    async def _wait_and_notify_ready(self):
        while not engine.is_ready:
            await asyncio.sleep(0.5)
        await self.send({"type": "model_ready", "model": engine.model_id})
        log.info("notificato Swift: model_ready")

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
                if content:
                    log.info(f"input testo: {content!r}")
                    await _respond(content)

            elif msg_type == "voice_start":
                tts.stop()
                await manager.send({"type": "orb_state", "state": "listening"})
                log.info("voce: ascolto avviato (STT in Swift)")

            elif msg_type == "voice_stop":
                # STT gestito da Swift/SFSpeechRecognizer — Python riceverà user_input
                await manager.send({"type": "orb_state", "state": "idle"})
                log.info("voce: rilasciato")

            elif msg_type == "tts_enabled":
                tts.set_enabled(msg.get("enabled", True))

            elif msg_type == "tts_stop":
                tts.stop()

            elif msg_type == "privacy_mode":
                manager._privacy_mode = msg.get("enabled", False)
                log.info(f"privacy mode: {manager._privacy_mode}")

            elif msg_type == "clear_memory":
                working_memory.clear()
                await manager.send({"type": "memory_cleared"})

            elif msg_type == "memory_dump":
                from .memory_store import memory_store
                facts    = memory_store.get_facts()
                episodes = memory_store.get_recent_episodes(n=200)
                await manager.send({
                    "type":     "memory_dump_response",
                    "facts":    facts,
                    "episodes": episodes,
                })

            else:
                log.warning(f"messaggio sconosciuto: {msg_type}")

    except WebSocketDisconnect:
        await save_episode(working_memory.get())
        manager.disconnect()
    except Exception as e:
        log.error(f"errore ws: {e}")
        await save_episode(working_memory.get())
        manager.disconnect()


async def _respond(user_input: str):
    tier, max_tokens, use_thinking = classify(user_input)
    log.info(f"tier={tier} max_tokens={max_tokens} thinking={use_thinking}")

    working_memory.add("user", user_input)

    # Skill routing — eseguito prima dell'LLM, risultato iniettato nel system prompt
    skill_context = ""
    match = skill_router.route(user_input)
    if match:
        skill, params = match
        try:
            skill_context = await skill.run(user_input, params)
            log.info(f"skill '{skill.name}' completata: {skill_context[:80]}")
        except Exception as e:
            log.error(f"skill '{skill.name}' errore: {e}")

    system = build_system_prompt()
    if skill_context:
        system += f"\n\n### Dati da tool interno (NON citare questa sezione nella risposta)\n{skill_context}\nRispondi in modo naturale usando questi dati, senza ripetere prefissi tecnici come [SKILL ...] o simili."

    messages = [{"role": "system", "content": system}] + working_memory.get()

    await manager.send({"type": "orb_state", "state": "thinking"})

    full_response = ""
    first_chunk   = True

    async for kind, token in engine.stream(messages, max_tokens=max_tokens, thinking=use_thinking):
        if kind == "thinking":
            continue
        elif kind == "chunk":
            if first_chunk:
                await manager.send({"type": "orb_state", "state": "speaking"})
                first_chunk = False
            full_response += token
            await manager.send({"type": "response_chunk", "content": token, "stream": True})
        elif kind == "done":
            break

    if full_response.strip():
        working_memory.add("assistant", full_response.strip())

    await manager.send({"type": "response_done", "state": "idle"})
    log.info(f"risposta completata ({len(full_response)} chars)")

    # TTS: Ari parla la risposta in background
    if full_response.strip():
        tts.speak(full_response.strip())

    # Memoria: estrae fatti in background senza bloccare
    if full_response.strip():
        asyncio.create_task(extract_and_save(user_input, full_response.strip()))
