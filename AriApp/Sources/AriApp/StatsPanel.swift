import AppKit

final class StatsPanel {
    static let shared = StatsPanel()

    private var panel: AriPanel?

    // Righe metriche — ordine di visualizzazione
    private var rows: [String: StatRow] = [:]
    private let rowOrder: [(key: String, label: String, unit: String)] = [
        ("cpu_pct",       "CPU",       "%"),
        ("mem",           "MEMORIA",   ""),
        ("disk_used_pct", "DISCO USO", "%"),
        ("disk_write",    "DISCO ↑",   ""),
        ("disk_read",     "DISCO ↓",   ""),
        ("net_up",        "RETE ↑",    ""),
        ("net_down",      "RETE ↓",    ""),
        ("temp_c",        "CPU TEMP",  "°C"),
    ]

    // MARK: - Show / toggle

    var isVisible: Bool { panel?.isVisible == true }

    func show() {
        if panel == nil { buildPanel() }
        panel?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        wireStats()
    }

    func toggle() {
        guard let p = panel else { show(); return }
        if p.isVisible {
            p.orderOut(nil)
        } else {
            p.makeKeyAndOrderFront(nil)
            wireStats()
        }
    }

    // MARK: - Build

    private func buildPanel() {
        let w: CGFloat = 300
        let rowH: CGFloat = 28
        let headerH: CGFloat = 36
        let footerH: CGFloat = 8
        let h: CGFloat = headerH + CGFloat(rowOrder.count) * rowH + footerH

        let p = AriPanel(
            contentRect: NSRect(x: 0, y: 0, width: w, height: h),
            styleMask:   [.titled, .closable, .fullSizeContentView, .nonactivatingPanel],
            backing:     .buffered,
            defer:       false
        )
        p.title                       = "Sistema · Ari"
        p.titlebarAppearsTransparent  = true
        p.titleVisibility             = .visible
        p.backgroundColor             = NSColor(red: 0.06, green: 0.06, blue: 0.10, alpha: 0.97)
        p.isOpaque                    = false
        p.hasShadow                   = true
        p.isFloatingPanel             = true
        p.level                       = .floating
        p.hidesOnDeactivate           = false
        p.collectionBehavior          = [.canJoinAllSpaces, .fullScreenAuxiliary]
        p.isMovableByWindowBackground = true
        p.standardWindowButton(.miniaturizeButton)?.isHidden = true
        p.standardWindowButton(.zoomButton)?.isHidden        = true

        let container = NSView(frame: NSRect(x: 0, y: 0, width: w, height: h))
        container.autoresizingMask = [.width, .height]
        p.contentView = container

        // Header
        let hdr = NSTextField(labelWithString: "SISTEMA")
        hdr.font      = .monospacedSystemFont(ofSize: 10, weight: .bold)
        hdr.textColor = NSColor(red: 0, green: 0.85, blue: 1, alpha: 0.8)
        hdr.frame     = NSRect(x: 12, y: h - 26, width: 160, height: 16)
        container.addSubview(hdr)

        // Separatore
        let sep = NSBox(frame: NSRect(x: 0, y: h - headerH, width: w, height: 1))
        sep.boxType = .separator
        container.addSubview(sep)

        // Righe metriche (dal basso verso l'alto — NSView origin in basso a sinistra)
        for (i, entry) in rowOrder.enumerated() {
            let y = footerH + CGFloat(rowOrder.count - 1 - i) * rowH
            let row = StatRow(frame: NSRect(x: 0, y: y, width: w, height: rowH),
                              label: entry.label, unit: entry.unit)
            container.addSubview(row)
            rows[entry.key] = row
        }

        // Right-click
        p.onRightClick = { [weak p] event in
            guard let p, let cv = p.contentView else { return }
            let menu = NSMenu()
            let hide = NSMenuItem(title: "Nascondi", action: #selector(NSWindow.orderOut(_:)), keyEquivalent: "")
            hide.target = p
            menu.addItem(hide)
            NSMenu.popUpContextMenu(menu, with: event, for: cv)
        }

        if let screen = NSScreen.main {
            let sf = screen.visibleFrame
            p.setFrameOrigin(NSPoint(x: sf.maxX - w - 40, y: sf.maxY - h - 40))
        }

        panel = p
        SnapManager.shared.registerExtra(p)
    }

    // MARK: - Stats wiring

    private func wireStats() {
        WebSocketManager.shared.onStatsUpdate = { [weak self] payload in
            self?.applyStats(payload)
        }
    }

    private func applyStats(_ d: [String: Any]) {
        // CPU
        if let v = d["cpu_pct"] as? Double {
            rows["cpu_pct"]?.update(value: "\(v)", bar: v / 100)
        }

        // Memoria
        if let used  = d["mem_used_gb"]  as? Double,
           let total = d["mem_total_gb"] as? Double,
           let pct   = d["mem_pct"]      as? Double {
            let label = String(format: "%.1f / %.1f GB", used, total)
            rows["mem"]?.update(value: label, bar: pct / 100)
        }

        // Disco utilizzo
        if let v = d["disk_used_pct"] as? Double {
            rows["disk_used_pct"]?.update(value: "\(v)", bar: v / 100)
        }

        // Disco I/O
        if let v = d["disk_read"]  as? String { rows["disk_read"]?.update(value: v, bar: nil) }
        if let v = d["disk_write"] as? String { rows["disk_write"]?.update(value: v, bar: nil) }

        // Rete
        if let v = d["net_down"] as? String { rows["net_down"]?.update(value: v, bar: nil) }
        if let v = d["net_up"]   as? String { rows["net_up"]?.update(value: v, bar: nil) }

        // Temperatura
        if let v = d["temp_c"] as? Double {
            rows["temp_c"]?.update(value: "\(v)", bar: min(v / 100, 1))
        } else {
            rows["temp_c"]?.update(value: "—", bar: nil)
        }
    }
}

// MARK: - StatRow

private final class StatRow: NSView {
    private let labelField = NSTextField(labelWithString: "")
    private let valueField = NSTextField(labelWithString: "—")
    private let barBack    = NSView()
    private let barFill    = NSView()
    private let unit: String

    init(frame: NSRect, label: String, unit: String) {
        self.unit = unit
        super.init(frame: frame)

        wantsLayer = true
        layer?.backgroundColor = NSColor.clear.cgColor

        let accent = NSColor(red: 0, green: 0.85, blue: 1, alpha: 1)

        // Label sinistra
        labelField.frame     = NSRect(x: 12, y: 6, width: 90, height: 16)
        labelField.font      = .monospacedSystemFont(ofSize: 10, weight: .medium)
        labelField.textColor = NSColor.white.withAlphaComponent(0.45)
        labelField.stringValue = label
        addSubview(labelField)

        // Barra di sfondo (opzionale)
        barBack.frame           = NSRect(x: 108, y: 12, width: 100, height: 4)
        barBack.wantsLayer      = true
        barBack.layer?.backgroundColor = NSColor.white.withAlphaComponent(0.1).cgColor
        barBack.layer?.cornerRadius    = 2
        addSubview(barBack)

        // Barra di riempimento
        barFill.frame           = NSRect(x: 108, y: 12, width: 0, height: 4)
        barFill.wantsLayer      = true
        barFill.layer?.backgroundColor = accent.cgColor
        barFill.layer?.cornerRadius    = 2
        addSubview(barFill)

        // Valore destra
        valueField.frame      = NSRect(x: 108, y: 6, width: 180, height: 16)
        valueField.font       = .monospacedSystemFont(ofSize: 11, weight: .semibold)
        valueField.textColor  = accent
        valueField.alignment  = .left
        addSubview(valueField)

        // Separatore inferiore
        let sep = NSView(frame: NSRect(x: 12, y: 0, width: frame.width - 24, height: 1))
        sep.wantsLayer = true
        sep.layer?.backgroundColor = NSColor.white.withAlphaComponent(0.05).cgColor
        addSubview(sep)
    }

    required init?(coder: NSCoder) { fatalError() }

    func update(value: String, bar: Double?) {
        DispatchQueue.main.async { [weak self] in
            guard let self else { return }
            let display = self.unit.isEmpty ? value : "\(value) \(self.unit)"
            self.valueField.stringValue = display

            if let ratio = bar {
                self.barBack.isHidden = false
                let w = self.barBack.frame.width * CGFloat(max(0, min(ratio, 1)))
                self.barFill.frame.size.width = w
                // Colore in base al valore: verde → giallo → rosso
                let color: NSColor
                switch ratio {
                case ..<0.6:  color = NSColor(red: 0,    green: 0.85, blue: 1,    alpha: 1)
                case ..<0.8:  color = NSColor(red: 1,    green: 0.8,  blue: 0,    alpha: 1)
                default:      color = NSColor(red: 1,    green: 0.3,  blue: 0.2,  alpha: 1)
                }
                self.barFill.layer?.backgroundColor = color.cgColor
                self.valueField.textColor = color

                // Con barra: sposta il testo sotto la barra
                self.valueField.frame.origin.y = 17
                self.barBack.isHidden = false
            } else {
                self.barBack.isHidden = true
                self.barFill.frame.size.width = 0
                self.valueField.frame.origin.y = 6
                self.valueField.textColor = NSColor(red: 0, green: 0.85, blue: 1, alpha: 1)
            }
        }
    }
}
