# UI Reference — Tauri Native Mac
**Aggiornato:** 2026-06-04

---

## 1. ICONA MENU BAR

Claude Desktop usa icona monocromatica template: bianca su sfondo scuro, nera su chiaro — macOS la gestisce automaticamente.

```rust
let icon_bytes = include_bytes!("../../static/icons/athena-menubar.png");
let icon = Image::from_bytes(icon_bytes).unwrap();
tray.set_icon(Some(icon)).unwrap();
tray.set_icon_as_template(true);  // ← fondamentale per Mac
```

**Specifiche icona:**
- PNG trasparente
- Colore: nero puro `#000000`
- Dimensioni: 44×44px (retina 2× per 22pt)
- Stile: silhouette semplice, leggibile a 22px
- Margine: 2px trasparente su tutti i lati

---

## 2. COMPORTAMENTO AVVIO

```rust
fn main() {
    tauri::Builder::default()
        .setup(|app| {
            app.set_activation_policy(ActivationPolicy::Accessory); // no Dock
            start_backend();
            wait_for_backend(); // retry loop localhost:8000
            if let Some(win) = app.get_webview_window("main") {
                let _ = win.eval("window.location.href = 'http://localhost:8000'");
            }
            setup_tray(app)?;
            Ok(())
        })
}
```

---

## 3. MENU TASTO DESTRO

```rust
use tauri::menu::{MenuBuilder, MenuItemBuilder, PredefinedMenuItem};

fn setup_tray(app: &tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let title    = MenuItemBuilder::new("Athena OS").enabled(false).build(app)?;
    let sep1     = PredefinedMenuItem::separator(app)?;
    let open     = MenuItemBuilder::new("Apri Athena").id("open").build(app)?;
    let new_chat = MenuItemBuilder::new("Nuova conversazione").id("new_chat").build(app)?;
    let sep2     = PredefinedMenuItem::separator(app)?;
    let status   = MenuItemBuilder::new("● Pronta").enabled(false).build(app)?;
    let model    = MenuItemBuilder::new("qwen3:14b").enabled(false).build(app)?;
    let sep3     = PredefinedMenuItem::separator(app)?;
    let quit     = MenuItemBuilder::new("Esci").id("quit").build(app)?;

    let menu = MenuBuilder::new(app)
        .item(&title).item(&sep1)
        .item(&open).item(&new_chat)
        .item(&sep2).item(&status).item(&model)
        .item(&sep3).item(&quit)
        .build()?;

    TrayIconBuilder::new()
        .menu(&menu)
        .on_menu_event(|app, event| match event.id().as_ref() {
            "open"     => show_window(app),
            "new_chat" => new_conversation(app),
            "quit"     => std::process::exit(0),
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click { button: MouseButton::Left, .. } = event {
                toggle_window(tray.app_handle());
            }
        })
        .build(app)?;
    Ok(())
}
```

---

## 4. CONFIGURAZIONE FINESTRA

**tauri.conf.json:**
```json
{
  "windows": [{
    "label": "main",
    "url": "http://localhost:8000",
    "width": 780,
    "height": 620,
    "minWidth": 600,
    "minHeight": 500,
    "decorations": true,
    "resizable": true,
    "visible": false,
    "center": true,
    "titleBarStyle": "Overlay"
  }]
}
```

**Chiudi X = nascondi:**
```rust
.on_window_event(|window, event| {
    if let WindowEvent::CloseRequested { api, .. } = event {
        api.prevent_close();
        window.hide().unwrap();
    }
})
```

---

## 5. QUICK ENTRY ⌘⇧A

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

## 6. NOTIFICHE NATIVE

```toml
tauri-plugin-notification = "2"
```

```rust
app.notification().builder()
   .title("Athena")
   .body("Testo notifica.")
   .show().unwrap();
```

---

## 7. ALTRE FEATURES

**Titolo dinamico:**
```rust
win.set_title("Athena — Coach Urago").unwrap();
```

**Badge Dock:**
```rust
#[cfg(target_os = "macos")]
app.set_badge_count(Some(1)).unwrap();
```

**Apri al login:**
```toml
tauri-plugin-autostart = "2"
```
```rust
let autostart = app.autolaunch();
autostart.enable().unwrap(); // o .disable()
```
