import AppKit

// MemoryPanel v2 — pannello grande dedicato alla memoria di Ari.
// Layout: header (search + stats) | colonna sinistra (fatti) | colonna destra (episodi)
// Fatti mostrati come card con key, value, tags, confidence bar, relazioni.

final class MemoryPanel {
    static let shared = MemoryPanel()

    private var panel:         AriPanel?
    private var factsView:     NSTextView?
    private var episodesView:  NSTextView?
    private var searchField:   NSTextField?
    private var statsLabel:    NSTextField?

    // Dati correnti
    private var allFacts:    [[String: Any]] = []
    private var allRelations:[[String: Any]] = []
    private var allEpisodes: [[String: Any]] = []

    // MARK: - Show / toggle

    var isVisible: Bool { panel?.isVisible == true }

    func show() {
        if panel == nil { buildPanel() }
        panel?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        requestRefresh()
    }

    func toggle() {
        guard let p = panel else { show(); return }
        p.isVisible ? p.orderOut(nil) : show()
    }

    // MARK: - Build

    private func buildPanel() {
        let W: CGFloat = 820
        let H: CGFloat = 640

        let p = AriPanel(
            contentRect: NSRect(x: 0, y: 0, width: W, height: H),
            styleMask:   [.titled, .closable, .resizable, .fullSizeContentView, .nonactivatingPanel],
            backing: .buffered, defer: false
        )
        p.title                       = "Memoria · Ari"
        p.titlebarAppearsTransparent  = true
        p.titleVisibility             = .hidden
        p.backgroundColor             = NSColor(red: 0.05, green: 0.05, blue: 0.08, alpha: 0.98)
        p.isOpaque                    = false
        p.hasShadow                   = true
        p.isFloatingPanel             = true
        p.level                       = .floating
        p.hidesOnDeactivate           = false
        p.collectionBehavior          = [.fullScreenAuxiliary]
        p.isMovableByWindowBackground = true
        p.minSize = NSSize(width: 540, height: 360)
        p.standardWindowButton(.miniaturizeButton)?.isHidden = true
        p.standardWindowButton(.zoomButton)?.isHidden        = true

        let root = NSView(frame: NSRect(x: 0, y: 0, width: W, height: H))
        root.autoresizingMask = [.width, .height]
        p.contentView = root

        // ── Header ───────────────────────────────────────────────────────────
        let headerH: CGFloat = 44
        let header = buildHeader(width: W, height: headerH)
        header.frame.origin.y = H - headerH
        root.addSubview(header)

        // ── Divisore verticale ───────────────────────────────────────────────
        let divX: CGFloat  = W * 0.62
        let bodyH: CGFloat = H - headerH - 28  // 28 = footer
        let divider = NSView(frame: NSRect(x: divX, y: 28, width: 1, height: bodyH))
        divider.autoresizingMask = [.height, .maxXMargin]
        divider.wantsLayer = true
        divider.layer?.backgroundColor = NSColor.white.withAlphaComponent(0.07).cgColor
        root.addSubview(divider)

        // ── Colonna sinistra — Fatti ─────────────────────────────────────────
        let leftTV = buildScrollableTextView(
            frame: NSRect(x: 0, y: 28, width: divX, height: bodyH)
        )
        leftTV.enclosingScrollView?.autoresizingMask = [.width, .height]
        root.addSubview(leftTV.enclosingScrollView!)
        factsView = leftTV

        // ── Colonna destra — Episodi ─────────────────────────────────────────
        let rightTV = buildScrollableTextView(
            frame: NSRect(x: divX + 1, y: 28, width: W - divX - 1, height: bodyH)
        )
        rightTV.enclosingScrollView?.autoresizingMask = [.width, .height, .minXMargin]
        root.addSubview(rightTV.enclosingScrollView!)
        episodesView = rightTV

        // ── Footer ───────────────────────────────────────────────────────────
        let footer = buildFooter(width: W)
        root.addSubview(footer)

        // ── Centra sullo schermo ─────────────────────────────────────────────
        if let screen = NSScreen.main {
            let sf = screen.visibleFrame
            p.setFrameOrigin(NSPoint(x: sf.midX - W / 2, y: sf.midY - H / 2))
        }

        p.onRightClick = { [weak p] event in
            guard let p, let cv = p.contentView else { return }
            let menu = NSMenu()
            let hide = NSMenuItem(title: "Nascondi", action: #selector(NSWindow.orderOut(_:)), keyEquivalent: "")
            hide.target = p
            menu.addItem(hide)
            NSMenu.popUpContextMenu(menu, with: event, for: cv)
        }

        panel = p
        SnapManager.shared.registerExtra(p)
    }

    private func buildHeader(width: CGFloat, height: CGFloat) -> NSView {
        let bar = NSView(frame: NSRect(x: 0, y: 0, width: width, height: height))
        bar.autoresizingMask = [.width]
        bar.wantsLayer = true
        bar.layer?.backgroundColor = NSColor(red: 0.07, green: 0.07, blue: 0.11, alpha: 1).cgColor

        // Titolo
        let title = NSTextField(labelWithString: "MEMORIA")
        title.font      = .monospacedSystemFont(ofSize: 11, weight: .bold)
        title.textColor = NSColor(red: 0, green: 0.85, blue: 1, alpha: 0.9)
        title.frame     = NSRect(x: 14, y: (height - 16) / 2, width: 90, height: 16)
        bar.addSubview(title)

        // Search field
        let sf = NSSearchField(frame: NSRect(x: 110, y: (height - 24) / 2, width: 280, height: 24))
        sf.placeholderString = "Cerca nella memoria..."
        sf.font    = .systemFont(ofSize: 12)
        sf.autoresizingMask = [.width]
        sf.target  = self
        sf.action  = #selector(searchChanged(_:))
        bar.addSubview(sf)
        searchField = sf

        // Stats label
        let stats = NSTextField(labelWithString: "")
        stats.font      = .monospacedSystemFont(ofSize: 9, weight: .regular)
        stats.textColor = NSColor.white.withAlphaComponent(0.35)
        stats.alignment = .right
        stats.frame     = NSRect(x: width - 240, y: (height - 14) / 2, width: 160, height: 14)
        stats.autoresizingMask = [.minXMargin]
        bar.addSubview(stats)
        statsLabel = stats

        // Refresh button
        let btn = NSButton(frame: NSRect(x: width - 76, y: (height - 24) / 2, width: 70, height: 24))
        btn.title      = "Aggiorna"
        btn.bezelStyle = .rounded
        btn.font       = .systemFont(ofSize: 11)
        btn.autoresizingMask = [.minXMargin]
        btn.target = self
        btn.action = #selector(refresh)
        bar.addSubview(btn)

        // Separatore inferiore
        let sep = NSView(frame: NSRect(x: 0, y: 0, width: width, height: 1))
        sep.autoresizingMask = [.width]
        sep.wantsLayer = true
        sep.layer?.backgroundColor = NSColor.white.withAlphaComponent(0.06).cgColor
        bar.addSubview(sep)

        return bar
    }

    private func buildFooter(width: CGFloat) -> NSView {
        let bar = NSView(frame: NSRect(x: 0, y: 0, width: width, height: 28))
        bar.autoresizingMask = [.width]
        bar.wantsLayer = true
        bar.layer?.backgroundColor = NSColor(red: 0.04, green: 0.04, blue: 0.07, alpha: 1).cgColor

        let sep = NSView(frame: NSRect(x: 0, y: 27, width: width, height: 1))
        sep.autoresizingMask = [.width]
        sep.wantsLayer = true
        sep.layer?.backgroundColor = NSColor.white.withAlphaComponent(0.06).cgColor
        bar.addSubview(sep)

        let lbl = NSTextField(labelWithString: "")
        lbl.tag  = 99
        lbl.font = .monospacedSystemFont(ofSize: 9, weight: .regular)
        lbl.textColor  = NSColor.white.withAlphaComponent(0.25)
        lbl.frame      = NSRect(x: 14, y: 7, width: width - 28, height: 14)
        lbl.autoresizingMask = [.width]
        bar.addSubview(lbl)

        return bar
    }

    private func buildScrollableTextView(frame: NSRect) -> NSTextView {
        let sv = NSScrollView(frame: frame)
        sv.hasVerticalScroller = true
        sv.autohidesScrollers  = true
        sv.drawsBackground     = false
        sv.autoresizingMask    = [.width, .height]

        let tv = NSTextView(frame: NSRect(x: 0, y: 0, width: frame.width, height: frame.height))
        tv.autoresizingMask   = [.width]
        tv.isEditable         = false
        tv.isSelectable       = true
        tv.drawsBackground    = false
        tv.textContainerInset = NSSize(width: 10, height: 10)
        sv.documentView       = tv
        return tv
    }

    // MARK: - Data

    @objc func refresh() {
        renderFacts(filter: searchField?.stringValue ?? "")
        renderEpisodes()
        WebSocketManager.shared.onMemoryDump = { [weak self] facts, relations, episodes in
            guard let self else { return }
            self.allFacts     = facts
            self.allRelations = relations
            self.allEpisodes  = episodes
            DispatchQueue.main.async {
                self.renderFacts(filter: self.searchField?.stringValue ?? "")
                self.renderEpisodes()
                self.updateStats()
            }
        }
        WebSocketManager.shared.requestMemoryDump()
    }

    private func requestRefresh() { refresh() }

    @objc private func searchChanged(_ sender: NSSearchField) {
        renderFacts(filter: sender.stringValue)
    }

    // MARK: - Render fatti

    private func renderFacts(filter: String) {
        guard let tv = factsView else { return }

        let filtered = filter.isEmpty ? allFacts : allFacts.filter { fact in
            let key = (fact["key"]   as? String ?? "").lowercased()
            let val = (fact["value"] as? String ?? "").lowercased()
            let tag = (fact["tags"]  as? String ?? "").lowercased()
            let q   = filter.lowercased()
            return key.contains(q) || val.contains(q) || tag.contains(q)
        }

        let attr = NSMutableAttributedString()

        // Intestazione colonna
        attr.append(header("FATTI  (\(filtered.count))", color: cyan))
        attr.append(sep())

        if filtered.isEmpty {
            attr.append(dim(filter.isEmpty ? "  nessun fatto memorizzato\n" : "  nessun risultato per '\(filter)'\n"))
        } else {
            let df = DateFormatter(); df.dateFormat = "dd/MM HH:mm"
            let rels = buildRelIndex()

            for fact in filtered {
                let key    = fact["key"]        as? String ?? ""
                let value  = fact["value"]      as? String ?? ""
                let conf   = fact["confidence"] as? Double ?? 1.0
                let tagsRaw = fact["tags"]      as? String ?? "[]"
                let ts     = fact["updated_at"] as? Double ?? 0
                let tags   = parseTags(tagsRaw)
                let date   = ts > 0 ? df.string(from: Date(timeIntervalSince1970: ts)) : ""

                // Key
                attr.append(bright("  \(key)", color: cyan))
                attr.append(dim("  \(date)\n"))

                // Value
                attr.append(body("  \(value)\n"))

                // Confidence bar
                if conf < 1.0 {
                    let bars = Int(conf * 10)
                    let bar  = String(repeating: "▪", count: bars) +
                               String(repeating: "·", count: 10 - bars)
                    attr.append(dim("  conf [\(bar)] \(Int(conf*100))%\n"))
                }

                // Tags
                if !tags.isEmpty {
                    attr.append(tag("  " + tags.map { "#\($0)" }.joined(separator: " ") + "\n"))
                }

                // Relazioni uscenti da questo fatto
                if let outgoing = rels[key] {
                    for (rtype, target) in outgoing {
                        attr.append(rel("  → \(rtype): \(target)\n"))
                    }
                }

                attr.append(dim(String(repeating: "·", count: 44) + "\n"))
            }
        }

        DispatchQueue.main.async {
            tv.textStorage?.setAttributedString(attr)
        }
    }

    // MARK: - Render episodi

    private func renderEpisodes() {
        guard let tv = episodesView else { return }
        let attr = NSMutableAttributedString()

        attr.append(header("EPISODI  (\(allEpisodes.count))", color: orange))
        attr.append(sep())

        if allEpisodes.isEmpty {
            attr.append(dim("  nessun episodio\n"))
        } else {
            let df = DateFormatter(); df.dateFormat = "dd/MM/yy\nHH:mm"
            for ep in allEpisodes {
                let summary = ep["summary"]       as? String ?? ""
                let ts      = ep["timestamp"]     as? Double ?? 0
                let nMsg    = ep["message_count"] as? Int    ?? 0
                let date    = ts > 0 ? df.string(from: Date(timeIntervalSince1970: ts)) : "??"

                attr.append(bright("  \(date)\n", color: orange))
                attr.append(body("  \(summary)\n"))
                attr.append(dim("  \(nMsg) msg\n"))
                attr.append(dim(String(repeating: "·", count: 28) + "\n"))
            }
        }

        DispatchQueue.main.async {
            tv.textStorage?.setAttributedString(attr)
        }
    }

    // MARK: - Stats

    private func updateStats() {
        let nFacts = allFacts.count
        let nRels  = allRelations.count
        let nEps   = allEpisodes.count
        statsLabel?.stringValue = "\(nFacts) fatti  ·  \(nRels) relazioni  ·  \(nEps) episodi"

        // Footer
        let ts = DateFormatter()
        ts.dateFormat = "HH:mm:ss"
        let timeStr = ts.string(from: Date())
        if let footer = panel?.contentView?.subviews.first(where: { $0.frame.height == 28 }),
           let lbl = footer.viewWithTag(99) as? NSTextField {
            lbl.stringValue = "sync \(timeStr)  ·  memoria v2 BM25 + relazioni"
        }
    }

    // MARK: - Helpers di stile

    private let cyan   = NSColor(red: 0.0,  green: 0.85, blue: 1.0,  alpha: 1)
    private let orange = NSColor(red: 1.0,  green: 0.60, blue: 0.1,  alpha: 1)
    private let green  = NSColor(red: 0.2,  green: 1.0,  blue: 0.4,  alpha: 1)
    private let purple = NSColor(red: 0.55, green: 0.18, blue: 1.0,  alpha: 1)

    private func header(_ text: String, color: NSColor) -> NSAttributedString {
        NSAttributedString(string: "\(text)\n", attributes: [
            .font: NSFont.monospacedSystemFont(ofSize: 10, weight: .bold),
            .foregroundColor: color,
        ])
    }
    private func sep() -> NSAttributedString {
        NSAttributedString(string: String(repeating: "─", count: 44) + "\n", attributes: [
            .font: NSFont.monospacedSystemFont(ofSize: 9, weight: .regular),
            .foregroundColor: NSColor.white.withAlphaComponent(0.12),
        ])
    }
    private func bright(_ text: String, color: NSColor) -> NSAttributedString {
        NSAttributedString(string: text, attributes: [
            .font: NSFont.monospacedSystemFont(ofSize: 11, weight: .semibold),
            .foregroundColor: color,
        ])
    }
    private func body(_ text: String) -> NSAttributedString {
        NSAttributedString(string: text, attributes: [
            .font: NSFont.systemFont(ofSize: 12, weight: .regular),
            .foregroundColor: NSColor.white.withAlphaComponent(0.85),
        ])
    }
    private func dim(_ text: String) -> NSAttributedString {
        NSAttributedString(string: text, attributes: [
            .font: NSFont.monospacedSystemFont(ofSize: 9, weight: .regular),
            .foregroundColor: NSColor.white.withAlphaComponent(0.25),
        ])
    }
    private func tag(_ text: String) -> NSAttributedString {
        NSAttributedString(string: text, attributes: [
            .font: NSFont.monospacedSystemFont(ofSize: 9, weight: .medium),
            .foregroundColor: green.withAlphaComponent(0.70),
        ])
    }
    private func rel(_ text: String) -> NSAttributedString {
        NSAttributedString(string: text, attributes: [
            .font: NSFont.monospacedSystemFont(ofSize: 9, weight: .regular),
            .foregroundColor: purple.withAlphaComponent(0.70),
        ])
    }

    // MARK: - Utilities

    private func parseTags(_ raw: String) -> [String] {
        guard let data = raw.data(using: .utf8),
              let arr  = try? JSONSerialization.jsonObject(with: data) as? [String]
        else { return [] }
        return arr
    }

    private func buildRelIndex() -> [String: [(String, String)]] {
        var idx: [String: [(String, String)]] = [:]
        for r in allRelations {
            let from = r["from_key"] as? String ?? ""
            let to   = r["to_key"]   as? String ?? ""
            let type = r["rel_type"] as? String ?? ""
            if !from.isEmpty && from != to {
                idx[from, default: []].append((type, to))
            }
        }
        return idx
    }
}
