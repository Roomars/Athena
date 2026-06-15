import AppKit

final class MemoryPanel {
    static let shared = MemoryPanel()

    private var panel:    AriPanel?
    private var textView: NSTextView?

    // MARK: - Show / hide

    func show() {
        if panel == nil { buildPanel() }
        panel?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        refresh()
    }

    func toggle() {
        guard let p = panel else { show(); return }
        if p.isVisible { p.orderOut(nil) } else { show() }
    }

    var isVisible: Bool { panel?.isVisible == true }

    // MARK: - Build

    private func buildPanel() {
        let w: CGFloat = 420
        let h: CGFloat = 500

        let p = AriPanel(
            contentRect: NSRect(x: 0, y: 0, width: w, height: h),
            styleMask:   [.titled, .closable, .resizable, .fullSizeContentView,
                          .nonactivatingPanel],
            backing:     .buffered,
            defer:       false
        )
        p.title                      = "Memoria · Ari"
        p.titlebarAppearsTransparent = true
        p.titleVisibility            = .visible
        p.backgroundColor            = NSColor(red: 0.06, green: 0.06, blue: 0.10, alpha: 0.97)
        p.isOpaque                   = false
        p.hasShadow                  = true
        p.isFloatingPanel            = true
        p.level                      = .floating
        p.hidesOnDeactivate          = false
        p.collectionBehavior         = [.fullScreenAuxiliary]
        p.isMovableByWindowBackground = true
        p.minSize = NSSize(width: 300, height: 200)

        // Nascondi zoom/miniaturize, mantieni close
        p.standardWindowButton(.miniaturizeButton)?.isHidden = true
        p.standardWindowButton(.zoomButton)?.isHidden        = true

        let container = NSView(frame: NSRect(x: 0, y: 0, width: w, height: h))
        container.autoresizingMask = [.width, .height]
        p.contentView = container

        // Toolbar top
        let toolbar = buildToolbar(width: w)
        container.addSubview(toolbar)

        // ScrollView
        let pad: CGFloat   = 8
        let topOff: CGFloat = 36
        let sv = NSScrollView(frame: NSRect(x: pad, y: pad,
                                            width: w - pad * 2,
                                            height: h - topOff - pad))
        sv.autoresizingMask    = [.width, .height]
        sv.hasVerticalScroller = true
        sv.autohidesScrollers  = true
        sv.drawsBackground     = false
        container.addSubview(sv)

        let tv = NSTextView(frame: NSRect(x: 0, y: 0, width: sv.contentSize.width, height: 0))
        tv.autoresizingMask   = [.width]
        tv.isEditable         = false
        tv.isSelectable       = true
        tv.drawsBackground    = false
        tv.textColor          = .white
        tv.font               = .monospacedSystemFont(ofSize: 11, weight: .regular)
        tv.textContainerInset = NSSize(width: 8, height: 8)
        sv.documentView       = tv
        textView = tv

        // Center on screen
        if let screen = NSScreen.main {
            let sf = screen.visibleFrame
            p.setFrameOrigin(NSPoint(
                x: sf.midX - w / 2,
                y: sf.midY - h / 2
            ))
        }

        // Right-click context
        p.onRightClick = { [weak p] event in
            guard let p else { return }
            let menu = NSMenu()
            let hide = NSMenuItem(title: "Nascondi", action: #selector(NSWindow.orderOut(_:)), keyEquivalent: "")
            hide.target = p
            menu.addItem(hide)
            if let cv = p.contentView {
                NSMenu.popUpContextMenu(menu, with: event, for: cv)
            }
        }

        panel = p
        SnapManager.shared.registerExtra(p)
    }

    private func buildToolbar(width: CGFloat) -> NSView {
        let bar = NSView(frame: NSRect(x: 0, y: 0, width: width, height: 36))
        bar.autoresizingMask = [.width]
        bar.wantsLayer       = true
        bar.layer?.backgroundColor = NSColor(white: 0.07, alpha: 1).cgColor

        let lbl = NSTextField(labelWithString: "MEMORIA RAW")
        lbl.font      = .monospacedSystemFont(ofSize: 10, weight: .bold)
        lbl.textColor = NSColor(red: 0, green: 0.85, blue: 1, alpha: 0.8)
        lbl.frame     = NSRect(x: 12, y: 10, width: 160, height: 16)
        bar.addSubview(lbl)

        let refreshBtn = NSButton(frame: NSRect(x: width - 90, y: 6, width: 80, height: 24))
        refreshBtn.title       = "Aggiorna"
        refreshBtn.bezelStyle  = .rounded
        refreshBtn.font        = .systemFont(ofSize: 11)
        refreshBtn.autoresizingMask = [.minXMargin]
        refreshBtn.target      = self
        refreshBtn.action      = #selector(refresh)
        bar.addSubview(refreshBtn)

        return bar
    }

    // MARK: - Data

    @objc func refresh() {
        setText("Caricamento…")
        WebSocketManager.shared.onMemoryDump = { [weak self] facts, episodes in
            self?.render(facts: facts, episodes: episodes)
        }
        WebSocketManager.shared.requestMemoryDump()
    }

    private func render(facts: [String: String], episodes: [[String: Any]]) {
        var lines: [String] = []

        // ── FATTI ─────────────────────────────────────────
        lines.append("── FATTI " + String(repeating: "─", count: 50))
        if facts.isEmpty {
            lines.append("  (nessun fatto memorizzato)")
        } else {
            let sorted = facts.sorted { $0.key < $1.key }
            let maxKey = sorted.map { $0.key.count }.max() ?? 0
            for (k, v) in sorted {
                let pad = String(repeating: " ", count: max(0, maxKey - k.count + 2))
                lines.append("  \(k)\(pad)\(v)")
            }
        }

        lines.append("")

        // ── EPISODI ───────────────────────────────────────
        lines.append("── EPISODI " + String(repeating: "─", count: 48))
        if episodes.isEmpty {
            lines.append("  (nessun episodio registrato)")
        } else {
            let df = DateFormatter()
            df.dateFormat = "dd/MM HH:mm"
            for ep in episodes {
                let summary   = ep["summary"]       as? String ?? ""
                let ts        = ep["timestamp"]     as? Double ?? 0
                let msgCount  = ep["message_count"] as? Int    ?? 0
                let date      = df.string(from: Date(timeIntervalSince1970: ts))
                lines.append("  [\(date)]  \(summary)  (\(msgCount) msg)")
            }
        }

        lines.append("")
        lines.append(String(repeating: "─", count: 59))
        lines.append("  \(facts.count) fatti  ·  \(episodes.count) episodi")

        setText(lines.joined(separator: "\n"))
    }

    private func setText(_ content: String) {
        DispatchQueue.main.async { [weak self] in
            self?.textView?.string = content
        }
    }
}
