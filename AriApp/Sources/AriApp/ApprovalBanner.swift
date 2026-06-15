import AppKit

/// Banner flottante che appare quando Ari propone una modifica al proprio codice.
/// Mostra descrizione + [Applica] [Annulla].
final class ApprovalBanner {
    static let shared = ApprovalBanner()

    private var panel: AriPanel?

    func show(description: String) {
        DispatchQueue.main.async { [weak self] in
            self?.buildAndShow(description: description)
        }
    }

    func dismiss() {
        DispatchQueue.main.async { [weak self] in
            self?.panel?.orderOut(nil)
            self?.panel = nil
        }
    }

    private func buildAndShow(description: String) {
        panel?.orderOut(nil)

        let w: CGFloat = 440
        let h: CGFloat = 72

        let p = AriPanel(
            contentRect: NSRect(x: 0, y: 0, width: w, height: h),
            styleMask:   [.borderless, .nonactivatingPanel],
            backing:     .buffered,
            defer:       false
        )
        p.backgroundColor            = NSColor(red: 0.08, green: 0.08, blue: 0.13, alpha: 0.97)
        p.isOpaque                   = false
        p.hasShadow                  = true
        p.isFloatingPanel            = true
        p.level                      = NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.floatingWindow)) + 1)
        p.collectionBehavior         = [.fullScreenAuxiliary]
        p.isMovableByWindowBackground = true

        p.contentView?.wantsLayer    = true
        p.contentView?.layer?.cornerRadius = 12
        p.contentView?.layer?.masksToBounds = true

        // Bordo accent
        p.contentView?.layer?.borderColor = NSColor(red: 0, green: 0.85, blue: 1, alpha: 0.4).cgColor
        p.contentView?.layer?.borderWidth = 1

        let container = p.contentView!

        // Icona
        let icon = NSTextField(labelWithString: "⚡")
        icon.font  = .systemFont(ofSize: 20)
        icon.frame = NSRect(x: 14, y: (h - 26) / 2, width: 26, height: 26)
        container.addSubview(icon)

        // Descrizione
        let lbl = NSTextField(labelWithString: description)
        lbl.font      = .systemFont(ofSize: 12, weight: .medium)
        lbl.textColor = .white
        lbl.lineBreakMode = .byTruncatingTail
        lbl.frame = NSRect(x: 46, y: (h - 16) / 2, width: w - 46 - 190, height: 16)
        container.addSubview(lbl)

        // [Annulla]
        let cancelBtn = makeButton("Annulla", x: w - 180, h: h,
                                   color: NSColor.white.withAlphaComponent(0.15),
                                   action: #selector(onCancel))
        container.addSubview(cancelBtn)

        // [Applica]
        let applyBtn = makeButton("Applica", x: w - 90, h: h,
                                  color: NSColor(red: 0, green: 0.75, blue: 0.4, alpha: 1),
                                  action: #selector(onApply))
        container.addSubview(applyBtn)

        // Posizione: in alto al centro dello schermo
        if let screen = NSScreen.main {
            let sf = screen.visibleFrame
            p.setFrameOrigin(NSPoint(x: sf.midX - w / 2, y: sf.maxY - h - 16))
        }

        panel = p
        p.makeKeyAndOrderFront(nil)
    }

    private func makeButton(_ title: String, x: CGFloat, h: CGFloat,
                             color: NSColor, action: Selector) -> NSButton {
        let btn = NSButton(frame: NSRect(x: x, y: (h - 28) / 2, width: 80, height: 28))
        btn.title      = title
        btn.bezelStyle = .rounded
        btn.wantsLayer = true
        btn.layer?.backgroundColor = color.cgColor
        btn.layer?.cornerRadius    = 6
        btn.font       = .systemFont(ofSize: 12, weight: .semibold)
        btn.isBordered = false
        btn.contentTintColor = .white
        btn.target     = self
        btn.action     = action
        return btn
    }

    @objc private func onApply() {
        dismiss()
        WebSocketManager.shared.sendJSON(["type": "apply_patch"])
    }

    @objc private func onCancel() {
        dismiss()
        WebSocketManager.shared.sendJSON(["type": "reject_patch"])
    }
}
