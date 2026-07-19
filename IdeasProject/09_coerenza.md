# Athena — Verifica Coerenza

## Scopo

Questo documento verifica che i pezzi dell'architettura siano coerenti tra loro.
Prima di scrivere una riga di codice, ogni punto qui deve avere risposta chiara.

---

## CHECK 1 — Confine Swift/Python ✅

**Domanda:** Chi fa cosa? C'è sovrapposizione?

| Responsabilità | Layer | Coerente? |
|---|---|---|
| UI, animazioni, orb | Swift | ✅ |
| Microfono, speaker | Swift (AVFoundation) | ✅ |
| Wake word detection | Swift | ✅ |
| STT trascrizione | Swift (whisper.cpp) OPPURE Python subprocess | ⚠️ DA DECIDERE |
| TTS output | Swift (Apple TTS) | ✅ |
| Elaborazione LLM | Python | ✅ |
| Memoria, embeddings | Python (ChromaDB) | ✅ |
| Skills, tools | Python | ✅ |
| Self-modification | Python | ✅ |
| Git operations | Python | ✅ |
| Home Assistant | Python | ✅ |

**Punto aperto STT:** whisper.cpp in Swift richiede xcframework (più complesso).
Alternativa: Swift registra audio → salva file WAV temporaneo → Python trascrive → invia testo via WS.
Più semplice, latenza aggiuntiva ~200ms. Accettabile per conversazione.
**Decisione suggerita:** Python trascrive (più semplice, un layer solo per AI).

---

## CHECK 2 — RAM e modelli ✅

**Domanda:** I modelli stanno in RAM contemporaneamente?

| Componente | RAM |
|---|---|
| OS + background | ~5GB |
| Swift app | ~200MB |
| Python daemon | ~300MB |
| whisper.cpp large-v3 | ~1.5GB |
| ChromaDB + SQLite | ~500MB |
| **Subtotale infrastruttura** | **~7.5GB** |
| Qwen3 14B Q4 (primario) | ~9GB |
| **Totale normale** | **~16.5GB ✅** |
| Qwen2.5 32B Q4 (on-demand) | ~21GB |
| **Totale con 32B** | **~28.5GB ⚠️** |

Il 32B è al limite ma possibile se il 14B viene scaricato prima.
Athena deve gestire lo swap esplicitamente e comunicarlo all'utente.

**Regola:** mai caricare 14B e 32B contemporaneamente.

---

## CHECK 3 — Self-modification e rollback ✅

**Domanda:** Il ciclo di modifica è sicuro e non può bloccarsi?

Casi edge verificati:

| Scenario | Comportamento |
|---|---|
| Test passano → tutto ok | Deploy + git commit |
| Test falliscono al 1° tentativo | Retry con fix, max 3 |
| Test falliscono 3 volte | Rollback + log + stop + notifica Roby |
| xcodebuild fallisce (Swift) | Rollback + log + notifica |
| Roby dice "No" alla proposta | Archivia proposta, nessuna modifica |
| self_modify.py si auto-propone modifica | ❌ BLOCCATO — regola hard-coded |
| Daemon Python crasha durante modifica | git stash automatico al boot successivo |

✅ Tutti i casi hanno gestione definita.

---

## CHECK 4 — Hot reload skills vs restart ✅

**Domanda:** Quando si ricarica cosa?

| Modifica | Meccanismo | Downtime |
|---|---|---|
| Skills Python | watchdog + importlib.reload | 0 secondi |
| Core Python | shutdown daemon + restart | ~3 secondi |
| Dipendenze Python | pip install + restart daemon | ~30-60 secondi |
| Swift UI | xcodebuild + app restart | ~30-60 secondi |

**Coerenza:** Le skills (95% delle modifiche) hanno hot reload. Solo modifiche strutturali richiedono restart.
Il daemon Python rimane attivo durante rebuild Swift — la conversazione non si interrompe.

---

## CHECK 5 — Memoria e Vault ✅

**Domanda:** Architettura vault — chi legge cosa, chi scrive dove?

**Fonte di verità:** file su disco (Google Drive AthenaInput o vault locale). ChromaDB è sempre l'indice, mai la fonte.

| Layer | Accesso Athena | Accesso Roby |
|---|---|---|
| `Google Drive/AthenaInput/` | Read-only + watchdog | Read+Write (da Mac o iPhone) |
| `/vault/athena/knowledge/` | Read+Write (copie locali) | Read (locale Mac) |
| `/vault/athena/notes/` | Read+Write | Read (locale Mac) |
| ChromaDB | Read+Write (indice) | Non visibile direttamente |

Se ChromaDB viene cancellato → re-index completo da `/vault/athena/knowledge/` (le copie locali sono la fonte di verità locale).

✅ Nessun conflitto. AthenaInput (GDrive) → elaborato → knowledge/ (locale) → indicizzato in ChromaDB.

---

## CHECK 6 — Privacy e NVIDIA fallback ✅

**Domanda:** Quando si usa NVIDIA, i dati escono dalla macchina?

Sì. NVIDIA NIM è un'API cloud. I dati escono.

**Regola:**
- NVIDIA è disabilitato di default
- Viene usato solo se Roby lo abilita esplicitamente nelle settings
- Prima di ogni chiamata NVIDIA, Athena avvisa: "userò NVIDIA, il testo uscirà dalla macchina"
- Athena non usa NVIDIA per input che contengono dati sensibili (file personali, contenuti del vault)

✅ Privacy preservata con consenso informato.

---

## CHECK 7 — Wake word e latenza ✅

**Domanda:** Il wake word sempre in ascolto non appesantisce il sistema?

Porcupine SDK: ~2-5% CPU su un core, ~50MB RAM.
Sempre attivo, leggero.

Quando la wake word viene rilevata:
1. Swift avvia registrazione utterance (< 50ms)
2. Audio va a whisper.cpp per trascrizione (~500ms per frase breve)
3. Testo inviato a Python via WebSocket (< 5ms)
4. LLM inizia elaborazione

**Latenza totale wake-to-response:** ~600ms - 2s (dipende dalla lunghezza frase e modello).
Accettabile per conversazione naturale.

---

## DECISIONI PRESE

1. **STT:** Python subprocess per v1 (semplice, +200ms accettabile nel contesto).
   Swift xcframework in FASE 9 per streaming parola-per-parola.

2. **Wake word:** Porcupine SDK. Wake word: "Athena" (custom model da creare su console.picovoice.ai).

3. **TTS:** Apple TTS nativa, voce italiana premium.
   Piper come alternativa in FASE 10.
   Siri voice non accessibile via API pubblica — usare la migliore voce Premium disponibile.

4. **Vault:** Due vault separati.
   - Vault Roby: Google Drive (Athena solo legge, non scrive — privacy Google non tocca la memoria di Athena)
   - Vault Athena: locale `/vault/athena/` (Athena legge e scrive — privacy totale)

## PUNTI ANCORA APERTI

- Quale voce italiana Apple TTS scegliere? → verificare con `say -v ?` sul Mac le voci installate
- Path esatto vault Google Drive di Roby → configurabile nelle settings, non hardcodato
