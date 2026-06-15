import AppKit

final class SettingsWindowController: NSWindowController {
    static let shared = SettingsWindowController()

    private var sidebar:     NSStackView!
    private var contentArea: NSView!
    private var currentSection: NSView?

    // Sezione Voce
    private var ttsSwitch:     NSSwitch!
    private var wakeSwitch:    NSSwitch!
    private var clapSwitch:    NSSwitch!
    private var hotkeyLabel:   NSTextField!
    private var recordingMode  = false
    private var localMonitor:  Any?

    private init() {
        let w: CGFloat = 540
        let h: CGFloat = 360
        let win = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: w, height: h),
            styleMask:   [.titled, .closable, .fullSizeContentView],
            backing:     .buffered,
            defer:       false
        )
        win.title                    = "Impostazioni Ari"
        win.titlebarAppearsTransparent = false
        win.isMovableByWindowBackground = true
        win.backgroundColor          = NSColor(red: 0.10, green: 0.10, blue: 0.14, alpha: 1)
        win.center()
        super.init(window: win)
        buildUI(w: w, h: h)
    }

    required init?(coder: NSCoder) { fatalError() }

    func show() {
        refresh()
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    // MARK: - Layout

    private func buildUI(w: CGFloat, h: CGFloat) {
        guard let content = window?.contentView else { return }

        let sideW: CGFloat = 140

        // Sidebar
        let sideBack = NSView(frame: NSRect(x: 0, y: 0, width: sideW, height: h))
        sideBack.wantsLayer = true
        sideBack.layer?.backgroundColor = NSColor(white: 0.08, alpha: 1).cgColor
        content.addSubview(sideBack)

        sidebar = NSStackView(frame: NSRect(x: 0, y: 0, width: sideW, height: h))
        sidebar.orientation  = .vertical
        sidebar.alignment    = .leading
        sidebar.spacing      = 2
        sidebar.edgeInsets   = NSEdgeInsets(top: 48, left: 8, bottom: 8, right: 8)
        sideBack.addSubview(sidebar)

        // Content area
        contentArea = NSView(frame: NSRect(x: sideW, y: 0, width: w - sideW, height: h))
        content.addSubview(contentArea)

        // Separatore verticale
        let sep = NSBox(frame: NSRect(x: sideW, y: 0, width: 1, height: h))
        sep.boxType = .separator
        content.addSubview(sep)

        // Sezioni sidebar
        addSidebarItem("Voce",      tag: 0)
        addSidebarItem("Aspetto",   tag: 1)
        addSidebarItem("Avanzate",  tag: 2)

        showSection(0)
    }

    private func addSidebarItem(_ title: String, tag: Int) {
        let btn = NSButton(frame: .zero)
        btn.title            = title
        btn.bezelStyle       = .rounded
        btn.isBordered       = false
        btn.alignment        = .left
        btn.font             = .systemFont(ofSize: 13)
        btn.contentTintColor = .white
        btn.tag              = tag
        btn.target           = self
        btn.action           = #selector(sidebarTapped(_:))
        btn.translatesAutoresizingMaskIntoConstraints = false
        btn.widthAnchor.constraint(equalToConstant: 124).isActive = true
        btn.heightAnchor.constraint(equalToConstant: 30).isActive = true
        sidebar.addArrangedSubview(btn)
    }

    @objc private func sidebarTapped(_ btn: NSButton) {
        showSection(btn.tag)
        // Evidenzia il pulsante selezionato
        sidebar.arrangedSubviews.compactMap { $0 as? NSButton }.forEach {
            $0.contentTintColor = $0.tag == btn.tag
                ? NSColor(red: 0, green: 0.85, blue: 1, alpha: 1)
                : .white
        }
    }

    private func showSection(_ tag: Int) {
        currentSection?.removeFromSuperview()
        let view: NSView
        switch tag {
        case 0:  view = buildVoiceSection()
        case 1:  view = buildPlaceholder("Aspetto — prossimamente")
        default: view = buildPlaceholder("Avanzate — prossimamente")
        }
        view.frame = contentArea.bounds
        contentArea.addSubview(view)
        currentSection = view
        // Evidenzia voce per default
        (sidebar.arrangedSubviews[safe: tag] as? NSButton)?.contentTintColor =
            NSColor(red: 0, green: 0.85, blue: 1, alpha: 1)
    }

    // MARK: - Sezione Voce

    private func buildVoiceSection() -> NSView {
        let view = NSView()
        let pad: CGFloat = 24

        func label(_ text: String, size: CGFloat = 11, bold: Bool = false) -> NSTextField {
            let f = NSTextField(labelWithString: text)
            f.font      = bold ? .boldSystemFont(ofSize: size) : .systemFont(ofSize: size)
            f.textColor = bold ? .white : NSColor.white.withAlphaComponent(0.55)
            return f
        }

        // — AUDIO —
        let hdr1 = label("AUDIO", bold: true)
        hdr1.frame = NSRect(x: pad, y: 270, width: 200, height: 16)
        view.addSubview(hdr1)

        let ttsLbl = label("Voce di risposta (TTS)", size: 13)
        ttsLbl.frame = NSRect(x: pad, y: 238, width: 220, height: 20)
        view.addSubview(ttsLbl)

        ttsSwitch = NSSwitch(frame: NSRect(x: 300, y: 234, width: 60, height: 28))
        ttsSwitch.target = self
        ttsSwitch.action = #selector(ttsChanged)
        view.addSubview(ttsSwitch)

        let wakeLbl = label("Wake Word (\"ehi Ari\")", size: 13)
        wakeLbl.frame = NSRect(x: pad, y: 204, width: 220, height: 20)
        view.addSubview(wakeLbl)

        wakeSwitch = NSSwitch(frame: NSRect(x: 300, y: 200, width: 60, height: 28))
        wakeSwitch.target = self
        wakeSwitch.action = #selector(wakeChanged)
        view.addSubview(wakeSwitch)

        let clapLbl = label("Doppio battito (Iron Man)", size: 13)
        clapLbl.frame = NSRect(x: pad, y: 170, width: 220, height: 20)
        view.addSubview(clapLbl)

        clapSwitch = NSSwitch(frame: NSRect(x: 300, y: 166, width: 60, height: 28))
        clapSwitch.target = self
        clapSwitch.action = #selector(clapChanged)
        view.addSubview(clapSwitch)

        let sep1 = NSBox(frame: NSRect(x: pad, y: 150, width: 340, height: 1))
        sep1.boxType = .separator
        view.addSubview(sep1)

        // — SCORCIATOIA —
        let hdr2 = label("SCORCIATOIA TASTIERA", bold: true)
        hdr2.frame = NSRect(x: pad, y: 126, width: 280, height: 16)
        view.addSubview(hdr2)

        let sub = label("Attiva / disattiva la registrazione vocale", size: 11)
        sub.frame = NSRect(x: pad, y: 106, width: 300, height: 16)
        view.addSubview(sub)

        hotkeyLabel = NSTextField(labelWithString: currentHotkeyString())
        hotkeyLabel.font      = .monospacedSystemFont(ofSize: 20, weight: .semibold)
        hotkeyLabel.textColor = NSColor(red: 0, green: 0.85, blue: 1, alpha: 1)
        hotkeyLabel.frame     = NSRect(x: pad, y: 66, width: 160, height: 30)
        view.addSubview(hotkeyLabel)

        let editBtn = NSButton(frame: NSRect(x: 200, y: 66, width: 120, height: 28))
        editBtn.title      = "Modifica"
        editBtn.bezelStyle = .rounded
        editBtn.target     = self
        editBtn.action     = #selector(startRecording)
        view.addSubview(editBtn)

        return view
    }

    private func buildPlaceholder(_ text: String) -> NSView {
        let v = NSView()
        let lbl = NSTextField(labelWithString: text)
        lbl.textColor = NSColor.white.withAlphaComponent(0.3)
        lbl.font      = .systemFont(ofSize: 13)
        lbl.frame     = NSRect(x: 24, y: 150, width: 300, height: 20)
        v.addSubview(lbl)
        return v
    }

    // MARK: - Actions

    @objc private func ttsChanged() {
        let on = ttsSwitch.state == .on
        SettingsManager.shared.settings.ttsEnabled = on
        SettingsManager.shared.save()
        WebSocketManager.shared.setTTSEnabled(on)
    }

    @objc private func wakeChanged() {
        let on = wakeSwitch.state == .on
        SettingsManager.shared.settings.wakeWordEnabled = on
        SettingsManager.shared.save()
        if on { WakeWordManager.shared.start() } else { WakeWordManager.shared.stop() }
    }

    @objc private func clapChanged() {
        let on = clapSwitch.state == .on
        SettingsManager.shared.settings.clapWakeEnabled = on
        SettingsManager.shared.save()
        if on { ClapWakeManager.shared.start() } else { ClapWakeManager.shared.stop() }
    }

    // MARK: - Hotkey recorder

    @objc private func startRecording() {
        guard !recordingMode else { return }
        recordingMode       = true
        hotkeyLabel.stringValue = "⌨ Premi..."
        hotkeyLabel.textColor   = NSColor.systemYellow

        localMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            self?.captureHotkey(event: event)
            return nil   // consuma l'evento
        }
    }

    private func captureHotkey(event: NSEvent) {
        defer {
            recordingMode = false
            if let m = localMonitor { NSEvent.removeMonitor(m); localMonitor = nil }
        }
        guard event.keyCode != 53 else {  // ESC = annulla
            hotkeyLabel.stringValue = currentHotkeyString()
            hotkeyLabel.textColor   = NSColor(red: 0, green: 0.85, blue: 1, alpha: 1)
            return
        }

        var modRaw: UInt64 = 0
        let m = event.modifierFlags
        if m.contains(.command) { modRaw |= CGEventFlags.maskCommand.rawValue   }
        if m.contains(.shift)   { modRaw |= CGEventFlags.maskShift.rawValue     }
        if m.contains(.option)  { modRaw |= CGEventFlags.maskAlternate.rawValue }
        if m.contains(.control) { modRaw |= CGEventFlags.maskControl.rawValue   }

        SettingsManager.shared.settings.hotkeyKeyCode  = Int(event.keyCode)
        SettingsManager.shared.settings.hotkeyModifiers = modRaw
        SettingsManager.shared.save()

        hotkeyLabel.stringValue = currentHotkeyString()
        hotkeyLabel.textColor   = NSColor(red: 0, green: 0.85, blue: 1, alpha: 1)
        HotkeyManager.shared.updateFromSettings()
    }

    // MARK: - Sync

    private func refresh() {
        let s = SettingsManager.shared.settings
        ttsSwitch?.state  = s.ttsEnabled      ? .on : .off
        wakeSwitch?.state = s.wakeWordEnabled  ? .on : .off
        clapSwitch?.state = s.clapWakeEnabled  ? .on : .off
        hotkeyLabel?.stringValue = currentHotkeyString()
    }

    private func currentHotkeyString() -> String {
        let s = SettingsManager.shared.settings
        return HotkeyManager.formatHotkey(keyCode: s.hotkeyKeyCode, modifiers: s.hotkeyModifiers)
    }
}

// MARK: - Helpers

private extension Array {
    subscript(safe index: Int) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}
