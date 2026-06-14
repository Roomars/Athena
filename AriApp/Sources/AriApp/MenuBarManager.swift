import AppKit
import SwiftUI

final class MenuBarManager: NSObject {
    private var statusItem: NSStatusItem?
    private var popover: NSPopover?
    private var isPrivacyMode = false

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
        popover?.behavior = .transient
        popover?.animates = true

        buildMenu()
    }

    @objc func togglePopover() {
        guard let button = statusItem?.button, let pop = popover else { return }
        if pop.isShown { pop.performClose(nil) }
        else { pop.show(relativeTo: button.bounds, of: button, preferredEdge: .minY) }
    }

    func toggleOrbVisibility() {
        togglePopover()
    }

    private func buildMenu() {
        // Right-click menu
        let menu = NSMenu()
        menu.addItem(NSMenuItem(title: "Mostra Ari", action: #selector(togglePopover), keyEquivalent: ""))
        menu.addItem(.separator())

        let privacyItem = NSMenuItem(title: "Privacy Mode", action: #selector(togglePrivacy), keyEquivalent: "")
        privacyItem.target = self
        menu.addItem(privacyItem)
        menu.addItem(.separator())

        let quit = NSMenuItem(title: "Esci", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        menu.addItem(quit)

        statusItem?.menu = menu
        // Rimuovi menu per rendere il click sinistro funzionale
        statusItem?.menu = nil
    }

    @objc private func togglePrivacy() {
        isPrivacyMode.toggle()
        updateStatusIcon()
        WebSocketManager.shared.sendPrivacyMode(enabled: isPrivacyMode)
        if isPrivacyMode, popover?.isShown == true {
            popover?.performClose(nil)
        }
    }

    private func updateStatusIcon() {
        let name = isPrivacyMode ? "pause.circle" : "sparkle"
        statusItem?.button?.image = NSImage(systemSymbolName: name, accessibilityDescription: "Ari")
    }
}
