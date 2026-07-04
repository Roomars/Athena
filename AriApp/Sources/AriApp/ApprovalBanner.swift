import AppKit

/// Banner flottante a 3 livelli (ispirato a PikoChan).
/// Modo .patch (self_modify): Nega | Applica
/// Modo .tool  (computer_control, code_runner): Nega | Consenti | Consenti sempre
final class ApprovalBanner {
    static let shared = ApprovalBanner()

    enum Mode {
        case patch                  // self_modify — revisione codice
        case tool(type: String)     // azione tool pericolosa
    }

    private var panel:    AriPanel?
    private var mode:     Mode = .patch

    // MARK: - Show

    func show(description: String, mode: Mode = .patch) {
        self.mode = mode
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

    // MARK: - Build

    private func buildAndShow(description: String) {
        panel?.orderOut(nil)

        let isThreeButton: Bool
        if case .tool = mode { isThreeButton = true } else { isThreeButton = false }

        let w: CGFloat = isThreeButton ? 540 : 440
        let h: CGFloat = 72

        let p = AriPanel(
            contentRect: NSRect(x: 0, y: 0, width: w, height: h),
            styleMask:   [.borderless, .nonactivatingPanel],
            backing:     .buffered,
            defer:       false
        )
        p.backgroundColor             = NSColor(red: 0.08, green: 0.08, blue: 0.13, alpha: 0.97)
        p.isOpaque                    = false
        p.hasShadow                   = true
        p.isFloatingPanel             = true
        p.level                       = NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.floatingWindow)) + 1)
        p.collectionBehavior          = [.fullScreenAuxiliary]
        p.isMovableByWindowBackground = true

        let cv = p.contentView!
        cv.wantsLayer                 = true
        cv.layer?.cornerRadius        = 12
        cv.layer?.masksToBounds       = true
        cv.layer?.borderColor         = accentBorderColor(isThreeButton).cgColor
        cv.layer?.borderWidth         = 1

        // Icona
        let icon = NSTextField(labelWithString: isThreeButton ? "🛡️" : "⚡")
        icon.font  = .systemFont(ofSize: 20)
        icon.frame = NSRect(x: 14, y: (h - 26) / 2, width: 26, height: 26)
        cv.addSubview(icon)

        // Etichetta tipo (solo tool mode)
        var labelX: CGFloat = 46
        if isThreeButton, case .tool(let actionType) = mode {
            let typeLbl = NSTextField(labelWithString: actionType.uppercased())
            typeLbl.font      = .monospacedSystemFont(ofSize: 9, weight: .bold)
            typeLbl.textColor = NSColor(red: 1, green: 0.6, blue: 0.2, alpha: 1)
            typeLbl.frame     = NSRect(x: 46, y: h - 22, width: 100, height: 12)
            cv.addSubview(typeLbl)
            labelX = 46
        }

        // Descrizione
        let btnZoneW: CGFloat = isThreeButton ? 290 : 185
        let lbl = NSTextField(labelWithString: description)
        lbl.font          = .systemFont(ofSize: 12, weight: .medium)
        lbl.textColor     = .white
        lbl.lineBreakMode = .byTruncatingTail
        lbl.frame         = NSRect(x: labelX, y: (h - 16) / 2 - (isThreeButton ? 4 : 0),
                                   width: w - labelX - btnZoneW, height: 16)
        cv.addSubview(lbl)

        // Bottoni — layout da destra a sinistra
        if isThreeButton {
            // [Consenti sempre] — verde pieno
            let alwaysBtn = makeButton("Consenti sempre", x: w - 170, h: h, width: 160,
                                       color: NSColor(red: 0, green: 0.65, blue: 0.35, alpha: 1),
                                       action: #selector(onAlwaysAllow))
            cv.addSubview(alwaysBtn)
            // [Consenti] — ciano
            let allowBtn = makeButton("Consenti", x: w - 250, h: h, width: 74,
                                      color: NSColor(red: 0, green: 0.65, blue: 0.85, alpha: 0.85),
                                      action: #selector(onAllow))
            cv.addSubview(allowBtn)
            // [Nega] — grigio
            let denyBtn = makeButton("Nega", x: w - 330, h: h, width: 74,
                                     color: NSColor.white.withAlphaComponent(0.15),
                                     action: #selector(onCancel))
            cv.addSubview(denyBtn)
        } else {
            // [Annulla]
            let cancelBtn = makeButton("Annulla", x: w - 180, h: h, width: 80,
                                       color: NSColor.white.withAlphaComponent(0.15),
                                       action: #selector(onCancel))
            cv.addSubview(cancelBtn)
            // [Applica]
            let applyBtn = makeButton("Applica", x: w - 90, h: h, width: 80,
                                      color: NSColor(red: 0, green: 0.75, blue: 0.4, alpha: 1),
                                      action: #selector(onApply))
            cv.addSubview(applyBtn)
        }

        // Posizione centrata in alto
        if let screen = NSScreen.main {
            let sf = screen.visibleFrame
            p.setFrameOrigin(NSPoint(x: sf.midX - w / 2, y: sf.maxY - h - 16))
        }

        panel = p
        p.makeKeyAndOrderFront(nil)
    }

    // MARK: - Helpers

    private func accentBorderColor(_ isThree: Bool) -> NSColor {
        isThree
            ? NSColor(red: 1, green: 0.6, blue: 0.2, alpha: 0.5)   // arancio per tool
            : NSColor(red: 0, green: 0.85, blue: 1,  alpha: 0.4)   // ciano per patch
    }

    private func makeButton(_ title: String, x: CGFloat, h: CGFloat, width: CGFloat,
                             color: NSColor, action: Selector) -> NSButton {
        let btn = NSButton(frame: NSRect(x: x, y: (h - 28) / 2, width: width, height: 28))
        btn.title            = title
        btn.bezelStyle       = .rounded
        btn.wantsLayer       = true
        btn.layer?.backgroundColor = color.cgColor
        btn.layer?.cornerRadius    = 6
        btn.font             = .systemFont(ofSize: 11, weight: .semibold)
        btn.isBordered       = false
        btn.contentTintColor = .white
        btn.target           = self
        btn.action           = action
        return btn
    }

    // MARK: - Actions — Patch mode

    @objc private func onApply() {
        dismiss()
        WebSocketManager.shared.sendJSON(["type": "apply_patch"])
    }

    @objc private func onCancel() {
        dismiss()
        if case .tool = mode {
            WebSocketManager.shared.sendJSON(["type": "tool_denied"])
        } else {
            WebSocketManager.shared.sendJSON(["type": "reject_patch"])
        }
    }

    // MARK: - Actions — Tool mode

    @objc private func onAllow() {
        dismiss()
        WebSocketManager.shared.sendJSON(["type": "tool_approved"])
    }

    @objc private func onAlwaysAllow() {
        dismiss()
        var actionType = ""
        if case .tool(let t) = mode { actionType = t }
        SettingsManager.shared.settings.alwaysAllowed[actionType] = true
        SettingsManager.shared.save()
        WebSocketManager.shared.sendJSON([
            "type":        "tool_always_allowed",
            "action_type": actionType,
        ])
    }
}
