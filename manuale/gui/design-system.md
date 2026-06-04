# Design System — Athena UI

**Aggiornato:** 04-06-2026

---

## Palette colori

| Token | Valore | Utilizzo |
|---|---|---|
| `--color-bg` | `#FFFFFF` | sfondo principale |
| `--color-accent` | `#0084FF` | pulsanti, link, highlight |
| `--color-text` | `#1A1A1A` | testo principale |
| `--color-text-secondary` | `#666666` | testo secondario, placeholder |
| `--color-border` | `#E5E5E5` | bordi, separatori |
| `--color-bubble-user` | `#0084FF` | bolla messaggio utente |
| `--color-bubble-athena` | `#F0F0F0` | bolla messaggio Athena |

---

## Tipografia

Font: system font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`)

| Elemento | Dimensione | Peso |
|---|---|---|
| Testo chat | 15px | 400 |
| Input | 15px | 400 |
| Sidebar label | 13px | 500 |
| Intestazioni | 17px | 600 |

---

## Dimensioni finestra

- Larghezza: **680px** (definita in `tauri.conf.json`)
- Altezza: variabile, ridimensionabile

---

## Icone

Libreria: **Lucide** (SVG inline o sprite)

Task aperto: sostituire le emoji nella sidebar con icone Lucide SVG.

Icone personalizzate di Roby:
- `static/icons/athena-menubar.png` — menu bar macOS
- `static/icons/athena-app.png` — icona applicazione
- `static/icons/athena-menubar.svg` — versione vettoriale
- `static/icons/athena-app.svg` — versione vettoriale

---

## Componenti

### Bolla messaggio
- Utente: sfondo `#0084FF`, testo bianco, allineata a destra
- Athena: sfondo `#F0F0F0`, testo `#1A1A1A`, allineata a sinistra
- Border radius: 18px (stile iMessage)

### Input area
- Border: 1px solid `#E5E5E5`
- Focus: border `#0084FF`
- Padding: 12px 16px
- Invio: Enter (Shift+Enter per newline)

### Sidebar
- Larghezza: ~200px
- Sfondo: `#F8F8F8`
- Items: icon + label, hover `#EEEEEE`

### Quick Entry (da implementare)
- Overlay a schermo intero con sfondo semi-trasparente
- Pannello centrato ~500px di larghezza
- Si apre con ⌘⇧A, si chiude con Escape
- Focus automatico sull'input al momento dell'apertura
