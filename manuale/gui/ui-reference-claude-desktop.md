# UI Reference — Claude Desktop → Athena
**Documento per:** Antigravity IDE  
**Scopo:** implementare in Athena l'UI di Claude Desktop  
**Aggiornato:** 2026-06-04

---

## Struttura generale

Claude Desktop è un'app a finestra singola con tre zone principali:

```
┌─────────────────────────────────────────────────────┐
│  SIDEBAR SINISTRA  │  AREA PRINCIPALE               │
│  (240px fissa)     │  (flex, occupa il resto)       │
│                    │                                 │
│  Logo + nome app   │  HEADER (48px)                 │
│  ─────────────     │  titolo sessione + status      │
│  Lista sessioni    │  ─────────────────────────     │
│  (scrollabile)     │  AREA MESSAGGI (flex)          │
│                    │  messaggi in colonna            │
│  ─────────────     │  scrollabile                   │
│  Footer:           │  ─────────────────────────     │
│  modello attivo    │  INPUT AREA (auto-height)      │
│  + settings        │  textarea + bottone invio      │
└─────────────────────────────────────────────────────┘
```

---

## Colori e tokens

```css
/* Sfondi */
--bg-main: #FFFFFF;           /* area chat */
--bg-sidebar: #F5F4EF;        /* sidebar — beige caldo, non grigio */
--bg-hover: #EEEADE;          /* hover elementi sidebar */
--bg-active: #E8E4D9;         /* elemento selezionato */
--bg-input: #FFFFFF;          /* box input */

/* Bordi */
--border: #E2DDD5;            /* bordo sidebar/header — caldo */
--border-input: #D1CEC7;      /* bordo input a riposo */
--border-input-focus: #0084FF; /* bordo input focus — azzurro Athena */

/* Testo */
--text-primary: #1A1A17;      /* testo principale — quasi nero caldo */
--text-secondary: #706B5E;    /* testo secondario — grigio caldo */
--text-muted: #9E9A8E;        /* placeholder, labels */

/* Accenti */
--accent: #0084FF;            /* azzurro Athena (Claude usa #C96442) */
--accent-hover: #006ED9;      /* hover bottoni */

/* Bolle messaggi */
--bubble-user-bg: #F0EDE6;    /* bolla utente — beige caldo */
--bubble-user-text: #1A1A17;
--bubble-ai-bg: transparent;  /* Athena non ha sfondo bolla */
--bubble-ai-text: #1A1A17;
```

---

## Sidebar sinistra — dettaglio

**Dimensioni:** 240px fissa, non collassabile in desktop  
**Sfondo:** beige caldo #F5F4EF  
**Bordo destro:** 1px solid #E2DDD5

### Header sidebar
```
┌─────────────────────────┐
│ [icona]  Athena      ▾  │  ← logo 28px + nome + menu account
└─────────────────────────┘
```
- Altezza: 56px
- Padding: 0 12px
- Font nome: 16px, weight 600
- Freccia dropdown: apre menu account/impostazioni

### Bottone nuova chat
```
┌─────────────────────────┐
│  +  Nuova conversazione │  ← bottone full-width
└─────────────────────────┘
```
- Margin: 8px 12px
- Border-radius: 8px
- Background: trasparente con bordo #D1CEC7
- Hover: #EEEADE
- Font: 14px, weight 500
- Icona: + a sinistra

### Lista conversazioni
- Ogni item: padding 8px 12px, border-radius 8px
- Titolo conversazione: 14px, truncato con ellipsis
- Data/ora: 12px, color muted, destra
- Hover: background #EEEADE
- Selezionato: background #E8E4D9, font-weight 500
- Bordo sinistro su selezionato: 2px solid #0084FF
- Raggruppate per data: "Oggi", "Ieri", "Settimana scorsa"
- Label gruppi: 11px uppercase, muted, padding 8px 12px

### Footer sidebar
```
┌─────────────────────────┐
│ [dot] qwen3:14b         │  ← modello attivo
│ [⚙] Impostazioni       │  ← link settings
└─────────────────────────┘
```
- Separato dal corpo con bordo top
- Padding: 12px
- Font: 13px

---

## Area principale — header

**Altezza:** 48px fissi  
**Bordo bottom:** 1px solid #E2DDD5  
**Contenuto:**

```
│ Titolo sessione               [●] pronta  [Nuova chat] │
```

- Titolo: 15px, weight 600, flex-1
- Status dot: 8px, verde #34C759 / arancio animato
- Status text: 12px, muted
- Bottone "Nuova chat": ghost, bordo sottile, 12px

---

## Area messaggi — layout Claude

Claude Desktop usa un layout a **larghezza massima centrata**:

```css
.messages-container {
  max-width: 680px;      /* mai più largo */
  margin: 0 auto;        /* centrato */
  padding: 24px 16px;
}
```

### Messaggio utente
```
                    ┌──────────────────┐
                    │ Testo del        │  [R]
                    │ messaggio utente │
                    └──────────────────┘
```
- Allineato a destra
- Bolla: background #F0EDE6, border-radius 18px 18px 4px 18px
- Avatar: cerchio 28px, iniziale "R", background #0084FF, testo bianco
- Max-width bolla: 75%
- Font: 15px, line-height 1.6

### Messaggio Athena
```
[A]
Testo della risposta di Athena senza bolla,
su larghezza piena. Markdown renderizzato.

- lista item
- lista item

**grassetto** e `codice inline`
```
- Nessuna bolla — testo diretto su sfondo bianco
- Avatar: 28px, icona Athena, bordo sottile
- Markdown completamente renderizzato
- Blocchi codice: background #F5F4EF, font monospace, padding 12px, border-radius 8px
- Spaziatura tra messaggi: 24px

### Indicatore "sta pensando"
```
[A]  ● ● ●   (tre dot animati, colore muted)
```

---

## Area input — dettaglio Claude

```
┌────────────────────────────────────────────────┐
│                                                │
│  Scrivi a Athena…                              │
│                                                │
│  [📎] [🎙]                            [INVIA →]│
└────────────────────────────────────────────────┘
```

- Container: border-radius 16px, bordo 1.5px #D1CEC7
- Focus: bordo #0084FF
- Textarea: auto-resize, min 44px, max 200px
- Padding interno: 12px 14px
- Bottone invio: cerchio 36px, background accent, freccia SVG
- Shortcut: Enter invia, Shift+Enter va a capo

### Sotto l'input
```
  Contesto usato: ████░░░░░░ 42%    Athena può fare errori
```
- Barra contesto: mostra token approssimativi usati vs limite (20 messaggi)
- Disclaimer: 12px, muted, centrato

---

## Tipografia completa

```css
font-family: -apple-system, BlinkMacSystemFont, 
             "SF Pro Text", "Helvetica Neue", sans-serif;

--font-app-name:    17px / 700;
--font-section:     11px / 700;   /* label gruppi, uppercase */
--font-nav-item:    14px / 500;
--font-chat-title:  15px / 600;
--font-message:     15px / 400;
--font-code:        13px / 400;   /* SF Mono */
--font-meta:        12px / 400;
--font-placeholder: 15px / 400;

line-height messaggi: 1.65;
letter-spacing titoli: -0.02em;
```

---

## Animazioni e transizioni

```css
transition: background 0.12s ease, 
            color 0.12s ease,
            border-color 0.15s ease,
            opacity 0.1s ease;

@keyframes thinking {
  0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}
/* delay: 0s / 0.16s / 0.32s sui tre dot */

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
```

---

## Differenze Athena vs Claude Desktop

| Elemento | Claude Desktop | Athena |
|---|---|---|
| Colore accent | Arancio #C96442 | Azzurro #0084FF |
| Sidebar bg | Beige #F5F4EF | Beige #F5F4EF ✓ adotta |
| Bolla utente | Beige #F0EDE6 | Beige #F0EDE6 ✓ adotta |
| Bolla Athena | Nessuna bolla | Nessuna bolla ✓ adotta |
| Max-width chat | 680px centrata | 680px centrata ✓ adotta |
| Font | SF Pro | SF Pro ✓ |
| Cronologia | Raggruppata per data | Da implementare (FASE 2) |
| Barra contesto | Token usati | Da implementare |

---

## Piano di implementazione

### Step 1 — Quick wins
- Sidebar bg → #F5F4EF, border → #E2DDD5
- Bordo sinistro accent (#0084FF) su voce attiva sidebar
- Max-width 680px centrata sull'area messaggi
- Rimuove bolla dai messaggi Athena
- Bolla utente → #F0EDE6

### Step 2 — Markdown rendering
- `marked.js` via CDN
- Stile blocchi codice con sfondo beige #F5F4EF
- Liste, grassetto, codice inline funzionanti

### Step 3 — Cronologia (FASE 2 SQLite)
- Lista sidebar raggruppata per data
- Click → carica conversazione

### Step 4 — Barra contesto
- Conta token approssimativi (chars/4)
- Barra sottile sotto l'input
