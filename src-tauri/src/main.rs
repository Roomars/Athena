#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::{
    menu::{MenuBuilder, MenuItemBuilder, PredefinedMenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, WindowEvent,
};

struct BackendProcess(Mutex<Option<Child>>);

fn find_project_dir() -> Option<PathBuf> {
    // Packaged .app → Contents/Resources/backend
    if let Ok(exe) = std::env::current_exe() {
        if let Some(contents) = exe.parent().and_then(|p| p.parent()) {
            let res = contents.join("Resources/backend");
            if res.join("core/app.py").exists() {
                return Some(res);
            }
        }
    }
    // Development → ~/athena
    if let Ok(home) = std::env::var("HOME") {
        let dev = PathBuf::from(home).join("athena");
        if dev.join("core/app.py").exists() {
            return Some(dev);
        }
    }
    None
}

fn backend_running() -> bool {
    std::net::TcpStream::connect("127.0.0.1:8000").is_ok()
}

fn start_backend() -> Option<Child> {
    if backend_running() {
        return None;
    }
    let dir = find_project_dir()?;
    let venv_python = dir.join(".venv/bin/python3");
    let python = if venv_python.exists() { venv_python } else { PathBuf::from("python3") };

    Command::new(python)
        .args(["-m", "uvicorn", "core.app:app", "--host", "127.0.0.1", "--port", "8000"])
        .current_dir(&dir)
        .spawn()
        .ok()
}

fn wait_for_backend() {
    for _ in 0..60 {
        if backend_running() {
            return;
        }
        std::thread::sleep(std::time::Duration::from_millis(500));
    }
}

fn main() {
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            #[cfg(target_os = "macos")]
            app.set_activation_policy(tauri::ActivationPolicy::Accessory);

            let child = start_backend();
            *app.state::<BackendProcess>().0.lock().unwrap() = child;
            wait_for_backend();

            // Backend è pronto: forza la webview a caricare (aveva tentato prima che il server fosse su)
            if let Some(win) = app.get_webview_window("main") {
                let _ = win.eval("window.location.href = 'http://localhost:8000'");
            }

            let tray_bytes = include_bytes!("../../static/icons/athena-menubar.png");
            let img = image::load_from_memory(tray_bytes)
                .expect("athena-menubar.png non valida").into_rgba8();
            let (w, h) = img.dimensions();
            let tray_icon = tauri::image::Image::new_owned(img.into_raw(), w, h);

            let title_item = MenuItemBuilder::with_id("title", "Athena OS").enabled(false).build(app)?;
            let sep1       = PredefinedMenuItem::separator(app)?;
            let open_item  = MenuItemBuilder::with_id("open", "Apri Athena").build(app)?;
            let chat_item  = MenuItemBuilder::with_id("new_chat", "Nuova conversazione").build(app)?;
            let sep2       = PredefinedMenuItem::separator(app)?;
            let quit_item  = MenuItemBuilder::with_id("quit", "Esci").build(app)?;

            let menu = MenuBuilder::new(app)
                .item(&title_item).item(&sep1)
                .item(&open_item).item(&chat_item)
                .item(&sep2).item(&quit_item)
                .build()?;

            let _tray = TrayIconBuilder::new()
                .icon(tray_icon)
                .icon_as_template(true)
                .tooltip("Athena")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| {
                    match event.id.0.as_str() {
                        "open" => {
                            if let Some(win) = app.get_webview_window("main") {
                                let _ = win.show();
                                let _ = win.set_focus();
                                #[cfg(target_os = "macos")]
                                let _ = app.set_activation_policy(tauri::ActivationPolicy::Regular);
                            }
                        }
                        "new_chat" => {
                            if let Some(win) = app.get_webview_window("main") {
                                let _ = win.show();
                                let _ = win.set_focus();
                                let _ = win.eval("clearChat()");
                                #[cfg(target_os = "macos")]
                                let _ = app.set_activation_policy(tauri::ActivationPolicy::Regular);
                            }
                        }
                        "quit" => std::process::exit(0),
                        _ => {}
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(win) = app.get_webview_window("main") {
                            if win.is_visible().unwrap_or(false) {
                                let _ = win.hide();
                                #[cfg(target_os = "macos")]
                                let _ = app.set_activation_policy(tauri::ActivationPolicy::Accessory);
                            } else {
                                let _ = win.show();
                                let _ = win.set_focus();
                                #[cfg(target_os = "macos")]
                                let _ = app.set_activation_policy(tauri::ActivationPolicy::Regular);
                            }
                        }
                    }
                })
                .build(app)?;

            Ok(())
        })
        .on_window_event(|win, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                let _ = win.hide();
                api.prevent_close();
                #[cfg(target_os = "macos")]
                let _ = win.app_handle().set_activation_policy(tauri::ActivationPolicy::Accessory);
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Athena");
}
