import asyncio
import json
import logging
from fastapi import WebSocket, WebSocketDisconnect

from .llm import engine
from .memory import working_memory
from .prompt import build_system_prompt
from .complexity_router import classify
from .tts import tts
from .stt import stt
from .skill_router import router as skill_router
from .memory_extractor import extract_and_save, save_episode
from . import vision
from . import self_modify
from .cognitive import ActionExecutor
from .self_modify_agent import (
    generate_skill, build_init_update,
    classify_request, generate_swift_change, generate_personality_change,
)

_pending_mod:      dict | None = None
_pending_build:    dict | None = None
_approval_future:  asyncio.Future | None = None
_always_allowed:   set[str] = set()

log = logging.getLogger("ws")

# Layer 4 — Azione: istanziato a modulo-load, wired dopo che _request_tool_approval è definita
_action_executor: "ActionExecutor | None" = None


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


async def _notify_tts_done():
    await manager.send({"type": "tts_done"})


async def handle_ws(ws: WebSocket):
    global _action_executor
    if _action_executor is None:
        _action_executor = ActionExecutor(
            approval_fn=_request_tool_approval,
            always_allowed=_always_allowed,
        )
    tts.set_loop(asyncio.get_event_loop())
    tts.set_done_callback(_notify_tts_done)
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
                use_vad = msg.get("vad", False)
                asyncio.create_task(_stt_start(use_vad))
                log.info(f"voce: STT Whisper avviato (vad={use_vad})")

            elif msg_type == "voice_stop":
                asyncio.create_task(_stt_stop())
                log.info("voce: stop manuale → trascrizione Whisper")

            elif msg_type == "tts_enabled":
                tts.set_enabled(msg.get("enabled", True))

            elif msg_type == "tts_stop":
                tts.stop()

            elif msg_type == "set_tts_engine":
                tts.set_engine(msg.get("engine", "apple"))

            elif msg_type == "set_thresholds":
                from .stats_monitor import update_thresholds
                update_thresholds(
                    cpu  = float(msg.get("cpu",  85.0)),
                    ram  = float(msg.get("ram",  88.0)),
                    temp = float(msg.get("temp", 85.0)),
                )

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

            elif msg_type == "tool_approved":
                if _approval_future and not _approval_future.done():
                    _approval_future.set_result(True)

            elif msg_type == "tool_denied":
                if _approval_future and not _approval_future.done():
                    _approval_future.set_result(False)

            elif msg_type == "tool_always_allowed":
                action_type = msg.get("action_type", "")
                if action_type:
                    _always_allowed.add(action_type)
                    log.info(f"Whitelist aggiornata: {action_type} sempre consentito")
                if _approval_future and not _approval_future.done():
                    _approval_future.set_result(True)

            elif msg_type == "build_success":
                await _on_build_success()

            elif msg_type == "build_failed":
                await _on_build_failed(msg.get("error", "Errore sconosciuto."))

            elif msg_type == "memory_dump":
                from .memory_store import memory_store
                await manager.send({
                    "type":      "memory_dump_response",
                    "facts":     memory_store.get_facts_full(),
                    "relations": memory_store.get_relations(),
                    "episodes":  memory_store.get_episodes_full(n=200),
                    "graph":     memory_store.graph_snapshot(),
                })

            elif msg_type == "voice_enroll":
                asyncio.create_task(_voice_enroll())

            elif msg_type == "voice_verify_toggle":
                from .speaker_verifier import verifier
                verifier.enabled = msg.get("enabled", True)
                log.info(f"speaker verification: {verifier.enabled}")

            elif msg_type == "model_switch":
                model_id = msg.get("model_id", "")
                backend  = msg.get("backend", "mlx")
                api_key  = msg.get("api_key", "")
                if model_id:
                    await manager.send({"type": "model_loading"})
                    engine.switch_to(model_id, backend, api_key)

            elif msg_type == "model_reload":
                await manager.send({"type": "model_loading"})
                engine.reload()

            elif msg_type == "model_redownload":
                await manager.send({"type": "model_loading"})
                engine.redownload()

            else:
                log.warning(f"messaggio sconosciuto: {msg_type}")

    except WebSocketDisconnect:
        await save_episode(working_memory.get())
        manager.disconnect()
    except Exception as e:
        log.error(f"errore ws: {e}")
        await save_episode(working_memory.get())
        manager.disconnect()


async def _request_tool_approval(skill_name: str, description: str) -> bool:
    """Chiede approvazione a Swift per skill pericolose. Ritorna True se approvata."""
    global _approval_future
    if skill_name in _always_allowed:
        return True
    _approval_future = asyncio.get_event_loop().create_future()
    await manager.send({
        "type":        "request_tool_approval",
        "action_type": skill_name,
        "description": description,
    })
    try:
        return await asyncio.wait_for(asyncio.shield(_approval_future), timeout=30.0)
    except asyncio.TimeoutError:
        log.warning(f"Timeout approvazione tool: {skill_name}")
        return False
    finally:
        _approval_future = None


async def _voice_enroll() -> None:
    """Registra 8 secondi di voce e crea il profilo per il speaker verification."""
    import sounddevice as sd
    import numpy as np
    from .speaker_verifier import verifier, ENROLL_SEC, SAMPLE_RATE as SV_SR

    await manager.send({"type": "orb_state", "state": "listening"})
    await manager.send({"type": "response_chunk",
                        "content": "Registrazione in corso per 8 secondi... parla normalmente.",
                        "stream": False})
    await manager.send({"type": "response_done", "state": "listening"})

    loop = asyncio.get_event_loop()
    def _record():
        audio = sd.rec(int(ENROLL_SEC * SV_SR), samplerate=SV_SR,
                       channels=1, dtype="float32")
        sd.wait()
        return audio.flatten()

    audio = await loop.run_in_executor(None, _record)
    msg   = verifier.enroll(audio, SV_SR)

    await manager.send({"type": "orb_state", "state": "idle"})
    await manager.send({"type": "response_chunk", "content": msg, "stream": False})
    await manager.send({"type": "response_done", "state": "idle"})


async def _stt_start(use_vad: bool) -> None:
    """Avvia registrazione Whisper (hold-to-talk o VAD)."""
    if use_vad:
        loop = asyncio.get_event_loop()
        def _on_vad(text: str):
            asyncio.run_coroutine_threadsafe(_on_stt_result(text), loop)
        stt.start_vad(_on_vad)
    else:
        stt.start()


async def _stt_stop() -> None:
    """Stop manuale (hold-to-talk) → trascrive e risponde."""
    loop = asyncio.get_event_loop()
    await manager.send({"type": "orb_state", "state": "thinking"})
    text = await loop.run_in_executor(None, stt.stop_and_transcribe)
    await _on_stt_result(text)


async def _on_stt_result(text: str) -> None:
    """Risultato STT condiviso tra hold-to-talk e VAD."""
    if text:
        await manager.send({"type": "stt_result", "text": text})
        await _respond(text)
    else:
        await manager.send({"type": "orb_state", "state": "idle"})


async def _respond(user_input: str):
    tier, max_tokens, use_thinking = classify(user_input)
    log.info(f"tier={tier} max_tokens={max_tokens} thinking={use_thinking}")

    working_memory.add("user", user_input)

    # Layer 2 — Riflesso: skill routing pre-LLM, risultato iniettato nel system prompt
    skill_context = ""
    match = skill_router.route(user_input)
    if match:
        skill, params = match

        # Cortocircuiti speciali (non delegati all'ActionExecutor)
        if skill.name == "screen_vision":
            await manager.send({"type": "capture_screen", "prompt": user_input})
            await manager.send({"type": "orb_state", "state": "listening"})
            return
        if skill.name == "self_modify":
            await _handle_self_modify(user_input)
            return

        # Messaggio intermedio per operazioni lente (click VLM-driven)
        if skill.name == "computer_control" and params.get("action") in ("click", "double_click"):
            await manager.send({"type": "response_chunk",
                                "content": "Guardo lo schermo...", "stream": True})

        # Layer 4 — Azione: esecuzione via ActionExecutor (approvazione + retry)
        result = await _action_executor.execute(
            skill, user_input, params,
            require_approval=getattr(skill, "need_approval", False),
        )
        if result is None:
            # Approvazione negata
            await manager.send({"type": "response_chunk",
                                "content": "Azione annullata.", "stream": False})
            await manager.send({"type": "response_done", "state": "idle"})
            return
        skill_context = result

    system = build_system_prompt(query=user_input)
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

    # TTS: Ari parla la risposta (codice escluso)
    if full_response.strip():
        tts.speak(_tts_text(full_response))

    # Memoria: estrae fatti in background e notifica l'orb
    if full_response.strip():
        async def _extract_and_notify(u: str, r: str) -> None:
            await extract_and_save(u, r)
            await manager.send({"type": "orb_event", "event": "memory_save"})
        asyncio.create_task(_extract_and_notify(user_input, full_response.strip()))

    # File write: se la risposta contiene SAVE_TO:/path, salva il file
    if "SAVE_TO:" in full_response:
        _handle_save_to(full_response)


async def _respond_vision(image_b64: str, prompt: str):
    """Analizza uno screenshot: YOLO detection + Gemma strutturata."""
    await manager.send({"type": "orb_state", "state": "thinking"})

    structured = await vision.analyze_structured(image_b64, prompt)
    result     = vision.structured_to_text(structured)

    working_memory.add("user",      f"[screenshot] {prompt}")
    working_memory.add("assistant", result)

    # Invia sia il testo che il JSON strutturato al frontend
    await manager.send({"type": "response_chunk", "content": result, "stream": False})
    await manager.send({"type": "vision_structured", "data": structured})
    await manager.send({"type": "response_done", "state": "idle"})

    if result.strip():
        tts.speak(_tts_text(result))
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
        commit_out = self_modify.git_commit(f"self-modify: {mod['description']}", mod["changes"])
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


def _tts_text(response: str) -> str:
    """Prepara la risposta per il TTS: rimuove codice e markdown, tronca a 400 char."""
    import re
    # Direttiva SAVE_TO — non va letta ad alta voce
    text = re.sub(r'\nSAVE_TO:[^\n]+', '', response)
    text = re.sub(r'^SAVE_TO:[^\n]+\n?', '', text, flags=re.MULTILINE)
    # Blocchi multi-linea ```...```
    text = re.sub(r'```[\s\S]*?```', ' Il codice è nel pannello. ', text)
    # Inline code `...`
    text = re.sub(r'`[^`\n]+`', '', text)
    # Header markdown
    text = re.sub(r'#{1,6}\s+', '', text)
    # Bold / italic
    text = re.sub(r'\*{1,2}([^*\n]+)\*{1,2}', r'\1', text)
    text = re.sub(r'_{1,2}([^_\n]+)_{1,2}',   r'\1', text)
    # Liste e trattini
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    # Newline multipli → pausa naturale
    text = re.sub(r'\n{2,}', '. ', text)
    text = re.sub(r'\s{2,}', ' ', text).strip()
    # Tronca preservando parola intera
    if len(text) > 400:
        text = text[:400].rsplit(' ', 1)[0] + '.'
    return text or response.strip()[:400]


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
