# Modulo: UI PWA

**Cartella:** `static/`  
**Stato:** attivo (v0.2)  
**Aggiornato:** 04-06-2026

---

## File

| File | Funzione |
|---|---|
| `static/index.html` | Frontend completo (HTML + CSS + JS inline) |
| `static/manifest.json` | PWA manifest |
| `static/sw.js` | Service worker base |
| `static/icons/` | Icone app personalizzate di Roby |

---

## Design System

| Elemento | Valore |
|---|---|
| Background | `#FFFFFF` (bianco) |
| Accent principale | `#0084FF` (azzurro) |
| Font | System font stack |
| Stile generale | Essenziale, moderno, niente fronzoli |

---

## Componenti attuali

- **Chat area**: lista messaggi utente / Athena
- **Input**: campo testo + invio
- **Streaming**: le risposte di Athena appaiono token per token
- **Sidebar**: presente, icone ancora emoji (da sostituire con Lucide — task aperto)

---

## Task aperti (FASE 1)

| Task | Descrizione |
|---|---|
| Icone Lucide | Sostituire le emoji nella sidebar con icone SVG Lucide |
| Markdown rendering | Renderizzare `**grassetto**`, `# titoli`, `` `code` `` nelle risposte |
| Quick Entry | Overlay leggero aperto da shortcut globale ⌘⇧A |

---

## Come comunica col backend

```javascript
// Invio messaggio con streaming
const response = await fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ message: text, stream: true })
});
// Legge lo stream chunk per chunk
const reader = response.body.getReader();
```

---

## Regole UI

- Nessun framework — HTML/CSS/JS puro
- Nessun valore di stile hardcodato nel JS — variabili CSS
- Stato UI sempre esplicito: vuoto / caricamento / dati / errore
- Messaggi di errore in italiano, chiari, mai stack trace
- La finestra è larga 680px (definito in Tauri)
