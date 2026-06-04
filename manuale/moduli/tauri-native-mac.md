# Tauri — Funzionalità native macOS

**Aggiornato:** 04-06-2026

---

## Icona menu bar — template adattiva

File: `static/icons/athena-menubar.png`  
Specifiche: PNG trasparente, colore nero `#000000`, 44×44px (retina 2×), margine 2px  
macOS inverte automaticamente a bianco in dark mode — una sola versione.

```rust
let icon = Image::from_bytes(include_bytes!("../../static/icons/athena-menubar.png")).unwrap();
tray.set_icon(Some(icon)).unwrap();
tray.set_icon_as_template(true);  // fondamentale
```

---

## Menu tasto destro

```
Athena OS          (disabilitato)
───────────────────
Apri Athena        → show_window
Nuova conversazione → DELETE /chat + show_window
───────────────────
● Pronta           (disabilitato — status live)
qwen3:14b          (disabilitato)
───────────────────
Esci               → process::exit(0)
```

---

## Comportamento finestra

**tauri.conf.json:**
```json
{
  "width": 780, "height": 620,
  "minWidth": 600, "minHeight": 500,
  "decorations": true,
  "resizable": true,
  "visible": false,
  "titleBarStyle": "Overlay"
}
```

`titleBarStyle: "Overlay"` = traffic lights sovrapposti al contenuto HTML (stile Claude Desktop).

**Chiudi X = nascondi (non termina):**
```rust
.on_window_event(|window, event| {
    if let WindowEvent::CloseRequested { api, .. } = event {
        api.prevent_close();
        window.hide().unwrap();
    }
})
```

---

## Sequenza di avvio corretta

```rust
.setup(|app| {
    app.set_activation_policy(ActivationPolicy::Accessory); // nasconde dal Dock
    start_backend();       // avvia FastAPI in background
    wait_for_backend();    // retry loop su localhost:8000
    setup_tray(app)?;      // crea icona menu bar
    Ok(())
})
```

---

## Priorità implementazione

| Feature | Priorità | Effort | Plugin |
|---|---|---|---|
| Icona template adattiva | 🔴 subito | 15 min | — |
| Menu tasto destro completo | 🔴 subito | 30 min | — |
| titleBarStyle Overlay | 🔴 subito | 5 min | — |
| Chiudi = nascondi | 🔴 subito | 5 min | — |
| Quick Entry ⌘⇧A | 🟠 FASE 1 | 30 min | global-shortcut |
| Notifiche native | 🟠 FASE 1 | 20 min | notification |
| Titolo finestra dinamico | 🟡 futuro | 20 min | — |
| Badge Dock | 🟡 futuro | 10 min | — |
| Apri al login | 🟡 futuro | 20 min | autostart |

---

## Quick Entry ⌘⇧A (FASE 1)

```toml
# Cargo.toml
tauri-plugin-global-shortcut = "2"
```

```rust
app.global_shortcut().register("CmdOrCtrl+Shift+A", move |app| {
    if let Some(win) = app.get_webview_window("main") {
        if win.is_visible().unwrap_or(false) {
            win.set_focus().unwrap();
        } else {
            win.show().unwrap();
            win.set_focus().unwrap();
        }
    }
})?;
```

---

## Notifiche native (FASE 1)

```toml
tauri-plugin-notification = "2"
```

```rust
app.notification().builder()
   .title("Athena")
   .body("Messaggio completato.")
   .show().unwrap();
```

---

## Riferimento completo

Vedi documento originale: `manuale/gui/tauri-native-mac-reference.md`
