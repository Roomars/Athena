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
    }

    func applicationWillTerminate(_ notification: Notification) {
        DaemonManager.shared.stop()
        WebSocketManager.shared.disconnect()
    }
}
