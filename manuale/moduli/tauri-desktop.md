# Modulo: Tauri Desktop

**Cartella:** `src-tauri/`  
**Stato:** attivo (v0.2, macOS)  
**Aggiornato:** 04-06-2026

---

## Configurazione (`tauri.conf.json`)

| Parametro | Valore | Note |
|---|---|---|
| width | 680 | larghezza finestra |
| decorations | true | barra titolo nativa |
| resizable | true | l'utente può ridimensionare |
| Bundle identifier | — | vedere tauri.conf.json |

---

## Comportamento

- **Menu bar**: Athena appare solo nella barra dei menu macOS, non nel Dock
- **System tray**: click sull'icona → toggle mostra/nascondi finestra
- **Menu contestuale** (tasto destro sull'icona):
  - Athena OS *(intestazione, non cliccabile)*
  - Apri
  - Nuova chat
  - Esci

---

## Fix applicati

**Fix "Load failed"**: la webview aspetta che il backend FastAPI sia pronto prima di caricare l'URL. Senza questo fix, aprire l'app prima che il backend sia partito causava una pagina bianca.

---

## Icone

| File | Utilizzo |
|---|---|
| `src-tauri/icons/icon.icns` | icona .app macOS |
| `src-tauri/icons/tray-icon.png` | icona nella menu bar |
| `static/icons/athena-menubar.png` | icona menu bar (Roby) |
| `static/icons/athena-app.png` | icona app (Roby) |

Le icone personalizzate di Roby sono in `static/icons/` — da integrare correttamente nei path Tauri (FASE 1, task aperto).

---

## Build

```bash
# macOS
./build-mac.sh
# Output: src-tauri/target/release/bundle/macos/Athena.app

# Installa
cp -r src-tauri/target/release/bundle/macos/Athena.app /Applications/
open /Applications/Athena.app
```

---

## Regole Tauri

- La logica applicativa rimane in Python/FastAPI — Rust solo per OS-level
- Il frontend comunica col backend via `localhost:8000` (non tramite comandi Tauri)
- Ogni nuovo comando Tauri richiede aggiornamento di `capabilities/default.json`
- `src-tauri/target/` è gitignored (build artifacts, centinaia di MB)
