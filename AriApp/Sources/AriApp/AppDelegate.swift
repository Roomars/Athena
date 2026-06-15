import AppKit
import ServiceManagement

final class AppDelegate: NSObject, NSApplicationDelegate {
    let menuBar = MenuBarManager()

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Nascondi icona dal Dock — siamo solo menu bar
        NSApp.setActivationPolicy(.accessory)

        SettingsManager.shared.load()

        menuBar.setup()

        DaemonManager.shared.start()

        HotkeyManager.shared.onActivate = { [weak self] in
            self?.menuBar.activateVoiceHotkey()
        }
        HotkeyManager.shared.start()

        registerLoginItem()
    }

    func applicationWillTerminate(_ notification: Notification) {
        DaemonManager.shared.stop()
        WebSocketManager.shared.disconnect()
    }

    private func registerLoginItem() {
        // SMAppService richiede che l'app sia firmata e nel bundle.
        // In sviluppo (non firmata) questa chiamata viene ignorata silenziosamente.
        if #available(macOS 13.0, *) {
            try? SMAppService.mainApp.register()
        }
    }
}
