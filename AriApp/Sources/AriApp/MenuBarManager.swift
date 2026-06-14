import AppKit
import SwiftUI

final class MenuBarManager: NSObject {
    private var statusItem: NSStatusItem?
    private var popover: NSPopover?
    private var isPrivacyMode = false
    private var eventMonitor: Any?

    func setup() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        if let button = statusItem?.button {
            button.image = NSImage(systemSymbolName: "sparkle", accessibilityDescription: "Ari")
            button.action = #selector(togglePopover)
            button.target = self
        }

        let orb = OrbView()
        let hosting = NSHostingController(rootView: orb)

        popover = NSPopover()
        popover?.contentViewController = hosting
        popover?.behavior = .applicationDefined  // rimane aperto finché non chiudiamo noi
        popover?.animates = true

        // Chiude il popover con click fuori da esso
        eventMonitor = NSEvent.addGlobalMonitorForEvents(matching: [.leftMouseDown, .rightMouseDown]) { [weak self] _ in
            guard let self, self.popover?.isShown == true else { return }
            self.popover?.performClose(nil)
        }
    }

    @objc func togglePopover() {
        guard let button = statusItem?.button, let pop = popover else { return }
        if pop.isShown {
            pop.performClose(nil)
        } else {
            pop.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) {
                pop.contentViewController?.view.window?.makeKey()
            }
        }
    }

    func toggleOrbVisibility() {
        togglePopover()
    }

    @objc private func togglePrivacy() {
        isPrivacyMode.toggle()
        updateStatusIcon()
        WebSocketManager.shared.sendPrivacyMode(enabled: isPrivacyMode)
        if isPrivacyMode { popover?.performClose(nil) }
    }

    private func updateStatusIcon() {
        let name = isPrivacyMode ? "pause.circle" : "sparkle"
        statusItem?.button?.image = NSImage(systemSymbolName: name, accessibilityDescription: "Ari")
    }

    deinit {
        if let m = eventMonitor { NSEvent.removeMonitor(m) }
    }
}
