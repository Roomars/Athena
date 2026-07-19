# Ari — Modalità di Interazione

## Nome definitivo

- **Progetto:** Athena (cartella, repository)
- **AI:** Ari (il personaggio, l'assistente)

---

## Due modalità distinte

Ari non ha un'unica interfaccia. Ha due modalità con UX completamente diverse.
Stessa AI, stesso cervello Python, due frontend Swift separati.

```
┌─────────────────────────────────────────────────────┐
│  MODALITÀ VOCE          │  MODALITÀ CHAT             │
│  (Voice Mode)           │  (Chat Mode)               │
│                         │                            │
│  Ari vive nel notch     │  Finestra flottante        │
│  Orb animato 209x32     │  stile Claude Desktop      │
│  Solo voce              │  Testo + voce opzionale    │
│  Espande su hover/wake  │  Storia conversazione      │
│  Minimalista            │  Markdown, codice, file    │
└─────────────────────────────────────────────────────┘
         │                            │
         └────────────────────────────┘
                  Python Brain
              (stesso daemon, stessa AI)
```

---

## Modalità Voce — Notch / Dynamic Island

### Concetto
Ari vive permanentemente nel notch del MacBook Pro (M1 Max ha il notch).
Collassato: piccolo orb pulsante nell'area notch (209x32px).
Espanso: si allarga verso il basso mostrando lo stato e il testo opzionale.

### Stati notch

| Stato | Dimensione | Animazione |
|---|---|---|
| **Idle** | 209x32 — collassato | Pulsazione lenta, blu tenue |
| **Hover** | 209x48 — lieve espansione | Fade-in stato "Ciao" |
| **Ascolto** | 209x80 — espanso | Cerchi reattivi al volume voce |
| **Elaborazione** | 209x64 — medio | Rotazione particelle |
| **Risposta** | 209x96 — espanso | Onde audio + testo risposta |

### Attivazione
- **Wake word** "Ari" → notch si espande, inizia ascolto
- **Hotkey** `Cmd+Shift+A` → stessa cosa
- **Hover** con mouse → lieve espansione, mostra stato

### Implementazione Swift
```swift
// NSPanel sopra la menu bar, nel notch
notchPanel.level = .popUpMenu
notchPanel.setFrameOrigin(CGPoint(x: (screenWidth - 209) / 2, y: screenHeight - 32))
notchPanel.isOpaque = false
notchPanel.backgroundColor = .clear
notchPanel.collectionBehavior = [.canJoinAllSpaces, .stationary]

// Proximity detection per hover
NSEvent.addGlobalMonitorForEvents(matching: .mouseMoved) { event in
    if notchArea.contains(NSEvent.mouseLocation) {
        expandNotch()
    }
}

// Spring animation su espansione
withAnimation(.spring(response: 0.4, dampingFraction: 0.7)) {
    notchHeight = 96
}
```

### Reference open-source
- **Boring Notch**: https://github.com/TheBoredTeam/boring.notch — WindowManager.swift + MouseTracker.swift
- **Atoll**: https://github.com/Ebullioscopic/Atoll — parallax hover, command surface
- **DynamicIsland_Mac**: https://github.com/NKR00711/DynamicIsland_Mac

### Nota tecnica
Nessuna API Apple ufficiale per il notch su Mac.
Tutte le app (NotchNook, HiDock, Boring Notch) usano:
1. `NSWindow.level = .popUpMenu` per stare sopra la menu bar
2. Coordinate hardcoded (notch M1 Pro/Max/Air: 209x32px, centrato)
3. `NSTrackingArea` per proximity detection mouse
4. App distribuite fuori App Store (notarizzate, non sandboxate)

---

## Modalità Chat — Finestra Flottante

### Concetto
Finestra stile Claude Desktop — pannello laterale o centrale, flottante sopra le app.
Si apre con hotkey diversa o click sull'icona menu bar.
Piena storia conversazione, markdown, codice, allegati.

### Layout
```
┌──────────────────────────────────────┐
│  Ari  ●  [Voce] [Chat] [Settings]   │  ← header minimal
├──────────────────────────────────────┤
│                                      │
│  [Storia conversazione]              │
│  • Markdown rendered                 │
│  • Code blocks con syntax hl.        │
│  • Immagini inline                   │
│  • Tool calls visibili               │
│                                      │
├──────────────────────────────────────┤
│  [Allegati drag&drop]                │
│  [Input testo] [🎤] [Invia]         │
└──────────────────────────────────────┘
```

### Feature chat
- **Storia persistente**: conversazioni per progetto, ricercabili
- **Markdown completo**: headers, bold, code, tabelle, LaTeX
- **File attachment**: drag & drop PDF, immagini, testo → Ari li legge
- **Voce opzionale**: microfono integrato nel chat se vuoi dettare
- **Tool visibility**: mostra quando Ari usa tool (web_search, file_ops, etc.)
- **Streaming**: testo appare token per token
- **Copy/Export**: copia risposta, esporta conversazione come MD

### Attivazione
- `Cmd+Shift+C` → apre/nasconde pannello chat
- Click sull'icona menu bar → menu con "Apri Chat"
- Da voice mode: "Ari, mostrami in chat" → passa a chat mode

---

## Switcher tra modalità

Ari sa in quale modalità stai e può passare dall'una all'altra:

```
Voice → Chat: "Ari, aprimi la chat" o Cmd+Shift+C
Chat → Voice: chiudi la finestra, wake word torna attivo
Entrambe attive: possibile — chat aperta mentre notch è attivo
```

---

## Come si scrivono le domande (prompt)

### In Chat mode
Scrivi naturalmente, come con Claude. Non serve formato speciale.
Ari capisce italiano naturale.

Per task complessi, puoi essere più strutturato:
```
"Analizza questo PDF [allegato] e:
1. Dimmi i punti principali
2. Identifica le date importanti
3. Suggerisci i prossimi passi"
```

### In Voice mode
Parli normalmente. Frasi complete.
"Ari, cerca le ultime notizie sull'AI e fammene un riassunto"

### Modalità operativa inline (in entrambe)
Puoi specificare la modalità:
- "Ari, pensa bene a questo" → attiva Deep mode (32B)
- "Ari, risposta rapida" → Quick mode (14B)
- "Ari, fallo in background" → Background mode, ti notifica quando finito

---

## Interazione con file

### Chat mode — Allegati
- **Drag & drop** direttamente nella finestra chat
- **"Ari, leggi [path file]"** → Ari accede via file_ops skill
- **Paste immagine** (Cmd+V) → Ari vede l'immagine se MLX-vlm attivo

### Voice mode
- "Ari, studia il documento che ti ho messo in AthenaInput" → processa vault input
- "Ari, apri [file]" → mac_control lo apre
