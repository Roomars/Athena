# Athena — UI e Orb

## Concept visivo

L'orb è discreto ma presente. Non è un'app da aprire — è sempre lì, in attesa.
Stile: sferico, con profondità, luminoso internamente, bordi morbidi.
Colori: palette fredda (blu-viola-bianco) con accenti caldi durante risposta.
Dimensione: ~80x80pt di default, ridimensionabile.

---

## Quattro stati animati (Metal shader)

### Idle
- Pulsazione lenta: 0.8-1.0 scala in 3 secondi
- Luminosità: 20% — quasi trasparente, non distrae
- Colore: blu-grigio freddo
- Particelle: ferme, sparse, quasi invisibili

### Ascolto (dopo wake word / hotkey)
- Cerchi concentrici che si espandono dall'esterno verso l'interno
- Reattivo al volume: l'ampiezza dei cerchi scala con dB input microfono
- Luminosità: 70%
- Colore: blu elettrico
- Bordo: pulsante più deciso

### Elaborazione (LLM sta pensando)
- Rotazione lenta di un pattern di particelle intorno all'orb
- Shader: effetto "nebulosa" interna che si muove
- Luminosità: 50%
- Colore: viola-blu in transizione
- Nessuna risposta ai suoni (non sta ascoltando)

### Risposta (TTS in uscita)
- Onde verticali (tipo equalizzatore) che escono dalla superficie
- Sincronizzate con ampiezza audio TTS
- Luminosità: 90% — più vivido durante il parlato
- Colore: bianco-azzurro
- Effetto: "la voce viene dall'interno"

---

## Struttura UI Swift

```
AthenaApp (MenuBarExtra)
├── MenuBarIcon             ← icona nella barra, sempre visibile
│   ├── Click → mostra/nasconde OrbWindow
│   └── Right click → menu contestuale (quit, settings, silent mode)
│
└── OrbWindow              ← NSPanel flottante, non-activating
    ├── OrbView (Metal)    ← shader animato
    ├── TextOverlay        ← testo risposta (fade in/out)
    ├── InputField         ← per input testo (appare su richiesta)
    └── ConfirmView        ← per proposte self-modification
```

---

## OrbWindow — comportamento

- **Posizione:** angolo inferiore destro schermo (configurabile)
- **Livello:** `NSWindow.Level.floating` — sopra le app, sotto i menu
- **Stile:** `borderless`, `nonactivating` — non ruba focus
- **Trasparenza sfondo:** sì, con `NSVisualEffectView` per blur background
- **Resize:** drag per ridimensionare (min 60pt, max 200pt)
- **Drag:** trascinabile tenendo `Option`

---

## TextOverlay

Quando Athena risponde in testo (modalità silenziosa o aggiuntivo al TTS):
- Testo appare sotto/sopra l'orb con fade-in
- Font: SF Pro, 14pt, colore bianco con ombra leggera
- Max 3 righe visibili, scorri per vedere di più
- Svanisce dopo 5 secondi dall'ultima parola (o clic per chiudere)

---

## ConfirmView — per proposte self-modification

Appare sovrapposto all'orb quando Athena ha una proposta:
```
┌─────────────────────────────────┐
│ PROPOSTA                         │
│ web_search.py — parsing HTML     │
│                                  │
│ [Diff colorato sintetico]        │
│                                  │
│  [Dettagli]  [No]  [Sì →]       │
└─────────────────────────────────┘
```
- "Sì" → conferma, applica
- "No" → archivia
- "Dettagli" → apre file diff completo in editor

---

## MenuBar icon

Icona: versione stilizzata dell'orb — cerchio con punto luminoso interno.
Animata quando Athena è attiva (elaborazione/risposta).
Statica quando idle.

Non usare emoji come icona. SVG custom o SF Symbol personalizzato.

---

## Settings (pannello separato)

Accessibile da right-click sull'icona menu bar:
- Hotkey globale (configurabile)
- Posizione orb sullo schermo
- Dimensione orb
- Orario modalità silenziosa automatica
- Modello LLM da usare (14B / 32B)
- Connessione Home Assistant (URL + token)
- Obsidian vault path

---

## Nota Metal shader

Lo shader dell'orb è un fragment shader Metal su una sfera 3D.
Parametri esposti (aggiornati ogni frame da Swift):
- `time` — per animazioni continue
- `state` — 0=idle, 1=listen, 2=think, 3=speak
- `amplitude` — valore 0-1 per reattività audio (listen + speak)
- `progress` — 0-1 per transizioni di stato

Il shader interpola fluidamente tra gli stati con crossfade ~300ms.
