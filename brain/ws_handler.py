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
from . import vision
from . import self_modify
from .self_modify_agent import generate_skill, build_init_update

_pending_mod: dict | None = None   # proposta in attesa di conferma

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

            elif msg_type == "vision_request":
                image_b64 = msg.get("image", "")
                prompt    = msg.get("prompt", "Descrivi cosa vedi in questo screenshot.")
                if image_b64:
                    await _respond_vision(image_b64, prompt)

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

            elif msg_type == "apply_patch":
                if _pending_mod:
                    await _apply_pending()
                else:
                    await manager.send({"type": "response_chunk",
                                        "content": "Nessuna modifica in attesa.", "stream": False})
                    await manager.send({"type": "response_done", "state": "idle"})

            elif msg_type == "reject_patch":
                await _reject_pending()

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
        # Screen vision: chiede a Swift di catturare lo schermo
        if skill.name == "screen_vision":
            await manager.send({"type": "capture_screen", "prompt": user_input})
            await manager.send({"type": "orb_state", "state": "listening"})
            return
        # Self-modify: genera codice e invia proposta di modifica
        if skill.name == "self_modify":
            await _handle_self_modify(user_input)
            return
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


async def _respond_vision(image_b64: str, prompt: str):
    """Analizza uno screenshot con Gemma 4 12B e risponde in chat."""
    await manager.send({"type": "orb_state", "state": "thinking"})

    result = await vision.analyze(image_b64, prompt)

    working_memory.add("user",      f"[screenshot] {prompt}")
    working_memory.add("assistant", result)

    await manager.send({"type": "response_chunk", "content": result, "stream": False})
    await manager.send({"type": "response_done", "state": "idle"})

    if result.strip():
        tts.speak(result.strip())
        asyncio.create_task(extract_and_save(f"[screenshot] {prompt}", result))


# ── Self-modification ─────────────────────────────────────────────────────────

async def _handle_self_modify(user_input: str):
    global _pending_mod
    await manager.send({"type": "orb_state", "state": "thinking"})
    await manager.send({"type": "response_chunk",
                        "content": "Sto generando il codice...\n", "stream": True})

    skill_info = await generate_skill(user_input)
    if not skill_info:
        await manager.send({"type": "response_chunk",
                            "content": "Non sono riuscita a generare il codice. Riprova con una descrizione più precisa.",
                            "stream": False})
        await manager.send({"type": "response_done", "state": "idle"})
        return

    # Leggi file esistenti per calcolare diff
    changes = []

    # File nuova skill
    new_skill_content = skill_info["content"]
    changes.append({"rel_path": skill_info["filename"], "content": new_skill_content})

    # File __init__.py aggiornato
    current_init  = self_modify.read_file("skills/__init__.py")
    module_name   = skill_info["filename"].replace("skills/", "").replace(".py", "")
    updated_init  = build_init_update(skill_info["class_name"], module_name, current_init)
    diff_init     = self_modify.compute_diff(current_init, updated_init, "skills/__init__.py")
    changes.append({"rel_path": "skills/__init__.py", "content": updated_init})

    _pending_mod = {"changes": changes, "skill_name": skill_info["skill_name"]}

    # Mostra diff nel pannello risposta
    summary = (
        f"PROPOSTA DI MODIFICA\n"
        f"{'─' * 56}\n\n"
        f"Nuova skill: {skill_info['class_name']} ({skill_info['filename']})\n\n"
        f"── {skill_info['filename']} ──\n{new_skill_content}\n\n"
        f"── skills/__init__.py (diff) ──\n{diff_init}\n\n"
        f"{'─' * 56}\n"
        f"Scrivi 'applica' per confermare o 'annulla' per rifiutare."
    )

    await manager.send({"type": "response_chunk", "content": summary, "stream": False})
    await manager.send({"type": "response_done", "state": "idle"})
    await manager.send({"type": "diff_proposal",
                        "description": f"Nuova skill: {skill_info['class_name']}"})


async def _apply_pending():
    global _pending_mod
    if not _pending_mod:
        return
    mod = _pending_mod
    _pending_mod = None

    await manager.send({"type": "orb_state", "state": "thinking"})
    await manager.send({"type": "response_chunk",
                        "content": "Applicazione modifiche...", "stream": True})

    self_modify.apply_changes(mod["changes"])
    commit_out = self_modify.git_commit(f"feat: skill '{mod['skill_name']}' via self-modify")

    await manager.send({"type": "response_chunk",
                        "content": f"\n\nModifiche applicate. {commit_out}\nRiavvio in corso...",
                        "stream": False})
    await manager.send({"type": "response_done", "state": "idle"})
    await manager.send({"type": "modification_applied"})

    tts.speak("Fatto. Mi sto riavviando per caricare la nuova skill.")
    self_modify.restart_daemon()


async def _reject_pending():
    global _pending_mod
    _pending_mod = None
    await manager.send({"type": "response_chunk",
                        "content": "Modifica annullata. Nessun file modificato.", "stream": False})
    await manager.send({"type": "response_done", "state": "idle"})
