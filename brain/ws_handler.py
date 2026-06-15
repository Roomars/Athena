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
from .self_modify_agent import (
    generate_skill, build_init_update,
    classify_request, generate_swift_change, generate_personality_change,
)

_pending_mod:   dict | None = None   # proposta in attesa di conferma utente
_pending_build: dict | None = None   # modifica applicata, in attesa del build Swift

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

            elif msg_type == "build_success":
                await _on_build_success()

            elif msg_type == "build_failed":
                await _on_build_failed(msg.get("error", "Errore sconosciuto."))

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

    # File write: se la risposta contiene SAVE_TO:/path, salva il file
    if "SAVE_TO:" in full_response:
        _handle_save_to(full_response)


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
                        "content": "Analizzo la richiesta...\n", "stream": True})

    kind = classify_request(user_input)
    changes: list[dict] = []
    description = ""

    if kind == "python_skill":
        skill_info = await generate_skill(user_input)
        if not skill_info:
            await _send_error("Non sono riuscita a generare il codice. Riprova con una descrizione più precisa.")
            return
        changes.append({"scope": "brain", "rel_path": skill_info["filename"],
                         "content": skill_info["content"]})
        current_init = self_modify.read_file("skills/__init__.py")
        module_name  = skill_info["filename"].replace("skills/", "").replace(".py", "")
        updated_init = build_init_update(skill_info["class_name"], module_name, current_init)
        changes.append({"scope": "brain", "rel_path": "skills/__init__.py",
                         "content": updated_init})
        description = f"Nuova skill Python: {skill_info['class_name']}"

    elif kind == "swift_ui":
        swift_changes = await generate_swift_change(user_input)
        if not swift_changes:
            await _send_error("Non sono riuscita a generare il codice Swift.")
            return
        changes = swift_changes
        description = f"Modifica UI Swift: {', '.join(c['rel_path'] for c in changes)}"

    elif kind == "personality":
        pers_changes = await generate_personality_change(user_input)
        if not pers_changes:
            await _send_error("Non sono riuscita a modificare la personalità.")
            return
        changes = pers_changes
        description = "Aggiornamento personalità/voce"

    has_swift = any(c["scope"] == "swift" for c in changes)
    _pending_mod = {"changes": changes, "description": description, "has_swift": has_swift}

    summary = _build_summary(changes, description)
    await manager.send({"type": "response_chunk", "content": summary, "stream": False})
    await manager.send({"type": "response_done", "state": "idle"})
    await manager.send({"type": "diff_proposal", "description": description})


async def _apply_pending():
    global _pending_mod, _pending_build
    if not _pending_mod:
        return
    mod = _pending_mod
    _pending_mod = None

    await manager.send({"type": "orb_state", "state": "thinking"})
    await manager.send({"type": "response_chunk",
                        "content": "Scrivo i file...", "stream": True})

    backups = self_modify.apply_changes(mod["changes"])

    if mod["has_swift"]:
        # Attende build_success / build_failed da Swift
        _pending_build = {"mod": mod, "backups": backups}
        await manager.send({"type": "response_chunk",
                            "content": "\nCompilazione Swift in corso...", "stream": True})
        await manager.send({"type": "rebuild_app"})
    else:
        # Solo Python / constitution — commit e restart daemon
        commit_out = self_modify.git_commit(f"self-modify: {mod['description']}")
        needs_restart = any(c["scope"] == "brain" for c in mod["changes"])
        msg = f"\n\nApplicato. {commit_out}"
        if needs_restart:
            msg += "\nRiavvio daemon..."
        await manager.send({"type": "response_chunk", "content": msg, "stream": False})
        await manager.send({"type": "response_done", "state": "idle"})
        if needs_restart:
            tts.speak("Fatto. Mi sto riavviando.")
            await manager.send({"type": "modification_applied"})
            self_modify.restart_daemon()
        else:
            tts.speak("Fatto. La modifica è attiva.")


async def _reject_pending():
    global _pending_mod
    _pending_mod = None
    await manager.send({"type": "response_chunk",
                        "content": "Modifica annullata. Nessun file modificato.", "stream": False})
    await manager.send({"type": "response_done", "state": "idle"})


async def _on_build_success():
    global _pending_build
    if not _pending_build:
        return
    build = _pending_build
    _pending_build = None
    commit_out = self_modify.git_commit(f"self-modify: {build['mod']['description']}")
    await manager.send({"type": "response_chunk",
                        "content": f"\nBuild OK. {commit_out}\nRiavvio app...",
                        "stream": False})
    await manager.send({"type": "response_done", "state": "idle"})
    tts.speak("Build completata. Sto riavviando.")


async def _on_build_failed(error: str):
    global _pending_build
    if not _pending_build:
        return
    build = _pending_build
    _pending_build = None
    self_modify.rollback(build["backups"])
    short_error = error[-400:] if len(error) > 400 else error
    await manager.send({"type": "response_chunk",
                        "content": f"\nBuild fallita — rollback eseguito.\n\n{short_error}",
                        "stream": False})
    await manager.send({"type": "response_done", "state": "idle"})
    tts.speak("Build fallita. Ho ripristinato i file originali.")


def _handle_save_to(response: str) -> None:
    """Salva file se la risposta contiene SAVE_TO:/percorso."""
    import re, os
    from pathlib import Path
    m = re.search(r'SAVE_TO:([^\s\n]+)', response)
    if not m:
        return
    raw_path = m.group(1)
    path = Path(os.path.expanduser(raw_path)).resolve()
    # Estrai il contenuto (tutto tranne l'ultima riga SAVE_TO:...)
    content = re.sub(r'\nSAVE_TO:[^\n]+', '', response).strip()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        log.info(f"File salvato: {path}")
    except Exception as e:
        log.error(f"Errore salvataggio {path}: {e}")


async def _send_error(msg: str):
    await manager.send({"type": "response_chunk", "content": msg, "stream": False})
    await manager.send({"type": "response_done", "state": "idle"})


def _build_summary(changes: list[dict], description: str) -> str:
    lines = [
        "PROPOSTA DI MODIFICA",
        "─" * 56,
        f"\n{description}\n",
    ]
    for c in changes:
        lines.append(f"── [{c['scope']}] {c['rel_path']} ──")
        lines.append(c["content"][:1200] + ("..." if len(c["content"]) > 1200 else ""))
        lines.append("")
    lines += ["─" * 56, "Scrivi 'applica' per confermare o 'annulla' per rifiutare."]
    return "\n".join(lines)
