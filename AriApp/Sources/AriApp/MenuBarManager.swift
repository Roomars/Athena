import AppKit
import SwiftUI

// Tre finestre indipendenti:
//   orbPanel      — orb animato, trasparente
//   responsePanel — testo risposta, ridimensionabile
//   inputPanel    — campo input, ridimensionabile in larghezza

final class MenuBarManager: NSObject, NSTextFieldDelegate, NSWindowDelegate {

    private var statusItem:       NSStatusItem?
    private var orbPanel:         AriPanel?
    private var responsePanel:    AriPanel?
    private var inputPanel:       AriPanel?
    private var responseTextView: NSTextView?
    private var inputField:       NSTextField?
    private var micButton:        HoldMicButton?

    func setup() {
        buildStatusItem()
        buildOrbPanel()
        buildResponsePanel()
        buildInputPanel()
        wireCallbacks()
        wireSnapManager()
        NotificationManager.shared.setup()
        // Riattiva wake systems se erano abilitati
        let s = SettingsManager.shared.settings
        if s.clapWakeEnabled { ClapWakeManager.shared.start() }
    }

    // MARK: - Status item

    private func buildStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        guard let btn = statusItem?.button else { return }
        btn.image = NSImage(systemSymbolName: "sparkle", accessibilityDescription: "Ari")
        btn.action = #selector(handleClick)
        btn.target = self
        btn.sendAction(on: [.leftMouseUp, .rightMouseUp])
    }

    @objc private func handleClick() {
        NSApp.currentEvent?.type == .rightMouseUp ? showContextMenu() : toggleInput()
    }

    private func showContextMenu() {
        let menu = NSMenu()

        // Visualizza ▶ (submenu pannelli)
        let visualizzaItem = NSMenuItem(title: "Visualizza", action: nil, keyEquivalent: "")
        let sub = NSMenu()
        sub.addItem(menuItem("Orb",      visible: orbPanel?.isVisible,         action: #selector(toggleOrb)))
        sub.addItem(menuItem("Risposta", visible: responsePanel?.isVisible,    action: #selector(toggleResponse)))
        sub.addItem(menuItem("Input",    visible: inputPanel?.isVisible,       action: #selector(toggleInput)))
        sub.addItem(menuItem("Memoria",  visible: MemoryPanel.shared.isVisible,  action: #selector(toggleMemory)))
        sub.addItem(menuItem("Sistema",  visible: StatsPanel.shared.isVisible,  action: #selector(toggleStats)))
        visualizzaItem.submenu = sub
        menu.addItem(visualizzaItem)

        // Impostazioni
        let settingsItem = NSMenuItem(title: "Impostazioni", action: #selector(openSettings), keyEquivalent: ",")
        settingsItem.target = self
        menu.addItem(settingsItem)

        menu.addItem(.separator())

        let q = NSMenuItem(title: "Chiudi Ari", action: #selector(quitAri), keyEquivalent: "q")
        q.target = self
        menu.addItem(q)

        statusItem?.menu = menu
        statusItem?.button?.performClick(nil)
        statusItem?.menu = nil
    }

    @objc private func openSettings() {
        SettingsWindowController.shared.show()
    }

    private func menuItem(_ title: String, visible: Bool?, action: Selector) -> NSMenuItem {
        let check = visible == true ? "✓ " : "    "
        let item  = NSMenuItem(title: check + title, action: action, keyEquivalent: "")
        item.target = self
        return item
    }

    @objc private func quitAri() { NSApp.terminate(nil) }

    // MARK: - Snap Manager

    private func wireSnapManager() {
        let panels = [orbPanel, responsePanel, inputPanel].compactMap { $0 }
        SnapManager.shared.register(panels)
        for panel in panels {
            panel.onRightClick = { [weak self, weak panel] event in
                guard let self, let panel else { return }
                self.showPanelContextMenu(for: panel, event: event)
            }
        }
    }

    private func showPanelContextMenu(for panel: AriPanel, event: NSEvent) {
        let menu = NSMenu()

        if SnapManager.shared.isInGroup(panel) {
            let sep = NSMenuItem(title: "Separa widget", action: #selector(separatePanel(_:)), keyEquivalent: "")
            sep.target = self
            sep.representedObject = panel
            menu.addItem(sep)
            menu.addItem(.separator())
        }

        let hide = NSMenuItem(title: "Nascondi", action: #selector(hidePanelItem(_:)), keyEquivalent: "")
        hide.target = self
        hide.representedObject = panel
        menu.addItem(hide)

        guard let cv = panel.contentView else { return }
        NSMenu.popUpContextMenu(menu, with: event, for: cv)
    }

    @objc private func separatePanel(_ item: NSMenuItem) {
        guard let panel = item.representedObject as? AriPanel else { return }
        SnapManager.shared.separate(panel)
    }

    @objc private func hidePanelItem(_ item: NSMenuItem) {
        guard let panel = item.representedObject as? AriPanel else { return }
        panel.orderOut(nil)
    }

    // MARK: - Orb (solido, no chrome)

    private func buildOrbPanel() {
        let w: CGFloat = 224
        let h: CGFloat = 224

        let p = makePanel(w: w, h: h, resizable: false, chrome: false)
        p.isMovableByWindowBackground = true
        p.backgroundColor = .clear
        p.isOpaque        = false
        p.hasShadow       = false   // ombra rettangolare rimossa

        let hosting = NSHostingController(rootView: OrbView())
        hosting.view.frame = NSRect(x: 0, y: 0, width: w, height: h)
        hosting.view.wantsLayer           = true
        hosting.view.layer?.backgroundColor = CGColor.clear  // nessun quadrato
        p.contentView = hosting.view

        place(p, corner: .topLeft, offset: NSPoint(x: 40, y: 40))
        orbPanel = p
        p.makeKeyAndOrderFront(nil)
    }

    // MARK: - Response (ridimensionabile)

    private func buildResponsePanel() {
        let w: CGFloat = 340
        let h: CGFloat = 260

        let p = makePanel(w: w, h: h, resizable: true, chrome: true)
        p.minSize   = NSSize(width: 200, height: 100)
        p.delegate  = self

        let container = NSView(frame: NSRect(x: 0, y: 0, width: w, height: h))
        container.autoresizingMask = [.width, .height]
        p.contentView = container

        let pad: CGFloat = 8
        let sv = NSScrollView(frame: NSRect(x: pad, y: pad, width: w - pad*2, height: h - pad*2))
        sv.autoresizingMask    = [.width, .height]
        sv.hasVerticalScroller = true
        sv.autohidesScrollers  = true
        sv.drawsBackground     = false
        container.addSubview(sv)

        let tv = NSTextView(frame: NSRect(x: 0, y: 0, width: w - pad*2, height: h - pad*2))
        tv.autoresizingMask    = [.width]
        tv.isEditable          = false
        tv.isSelectable        = true
        tv.drawsBackground     = false
        tv.textColor           = .white
        tv.font                = .systemFont(ofSize: 13)
        tv.textContainerInset  = NSSize(width: 8, height: 8)
        tv.isAutomaticLinkDetectionEnabled = false
        sv.documentView        = tv
        responseTextView       = tv

        place(p, corner: .topRight, offset: NSPoint(x: 40, y: 40))
        responsePanel = p
        // parte nascosta
    }

    // MARK: - Input

    private func buildInputPanel() {
        let w: CGFloat = 340
        let h: CGFloat = 46

        let p = makePanel(w: w, h: h, resizable: true, chrome: true)
        p.minSize = NSSize(width: 200, height: h)
        p.maxSize = NSSize(width: 9999, height: h)

        let container = NSView(frame: NSRect(x: 0, y: 0, width: w, height: h))
        container.autoresizingMask = [.width, .height]
        p.contentView = container

        let pad: CGFloat   = 8
        let btnSz: CGFloat = 26

        // Bottone invia (destra)
        let sendX = w - pad - btnSz - 4
        let sendBtn = NSButton(frame: NSRect(x: sendX, y: (h-btnSz)/2, width: btnSz, height: btnSz))
        sendBtn.bezelStyle       = .circular
        sendBtn.isBordered       = false
        sendBtn.image            = NSImage(systemSymbolName: "arrow.up.circle.fill",
                                           accessibilityDescription: "Invia")
        sendBtn.contentTintColor = NSColor(red: 0, green: 0.85, blue: 1.0, alpha: 1.0)
        sendBtn.autoresizingMask = [.minXMargin]
        sendBtn.target = self
        sendBtn.action = #selector(sendMessage)
        container.addSubview(sendBtn)

        // Bottone camera (seconda posizione da sinistra) — cattura schermo
        let camX   = pad + btnSz + 4
        let camBtn = NSButton(frame: NSRect(x: camX, y: (h-btnSz)/2, width: btnSz, height: btnSz))
        camBtn.bezelStyle       = .circular
        camBtn.isBordered       = false
        camBtn.image            = NSImage(systemSymbolName: "camera.viewfinder",
                                          accessibilityDescription: "Schermo")
        camBtn.contentTintColor = NSColor.white.withAlphaComponent(0.4)
        camBtn.autoresizingMask = []
        camBtn.target           = self
        camBtn.action           = #selector(captureScreen)
        container.addSubview(camBtn)

        // Bottone microfono (sinistra) — hold-to-talk
        let micBtn = HoldMicButton(frame: NSRect(x: pad, y: (h-btnSz)/2, width: btnSz, height: btnSz))
        micBtn.bezelStyle       = .circular
        micBtn.isBordered       = false
        micBtn.image            = NSImage(systemSymbolName: "mic.circle.fill",
                                          accessibilityDescription: "Voce")
        micBtn.contentTintColor = NSColor.white.withAlphaComponent(0.4)
        micBtn.onPress   = { [weak self] in self?.voicePressed() }
        micBtn.onRelease = { [weak self] in self?.voiceReleased() }
        container.addSubview(micBtn)
        micButton = micBtn

        // Campo testo (dopo mic + camera)
        let fieldX = pad + btnSz + 4 + btnSz + 6
        let fieldW = sendX - fieldX - 4
        let field = NSTextField(frame: NSRect(x: fieldX, y: (h-22)/2, width: fieldW, height: 22))
        field.placeholderString = "Scrivi ad Ari..."
        field.isBordered        = false
        field.drawsBackground   = false
        field.textColor         = .white
        field.font              = .systemFont(ofSize: 13)
        field.focusRingType     = .none
        field.autoresizingMask  = [.width]
        field.delegate          = self
        container.addSubview(field)
        inputField = field

        place(p, corner: .bottomRight, offset: NSPoint(x: 40, y: 40))
        inputPanel = p
        p.makeKeyAndOrderFront(nil)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            p.makeFirstResponder(self.inputField)
        }
    }

    // MARK: - Helpers costruzione panel

    private func makePanel(w: CGFloat, h: CGFloat, resizable: Bool, chrome: Bool) -> AriPanel {
        var mask: NSWindow.StyleMask = [.nonactivatingPanel]
        if chrome {
            mask.insert(.titled)
            mask.insert(.fullSizeContentView)
            if resizable { mask.insert(.resizable) }
        } else {
            mask.insert(.borderless)
        }

        let p = AriPanel(
            contentRect: NSRect(x: 0, y: 0, width: w, height: h),
            styleMask:   mask,
            backing:     .buffered,
            defer:       false
        )
        p.isFloatingPanel             = true
        p.level                       = .floating
        p.hidesOnDeactivate           = false
        p.collectionBehavior          = [.fullScreenAuxiliary]
        p.isMovableByWindowBackground = true

        if chrome {
            p.titlebarAppearsTransparent = true
            p.titleVisibility            = .hidden
            p.backgroundColor = NSColor(red: 0.07, green: 0.07, blue: 0.11, alpha: 0.92)
            p.isOpaque        = false
            p.hasShadow       = true
            // Rimuove i tre pallini (close/miniaturize/zoom)
            p.standardWindowButton(.closeButton)?.isHidden    = true
            p.standardWindowButton(.miniaturizeButton)?.isHidden = true
            p.standardWindowButton(.zoomButton)?.isHidden     = true
        } else {
            p.backgroundColor = .clear
            p.isOpaque        = false
            p.hasShadow       = false
        }
        return p
    }

    private enum Corner { case topLeft, topRight, bottomLeft, bottomRight }

    private func place(_ p: NSPanel, corner: Corner, offset: NSPoint) {
        guard let screen = NSScreen.main else { return }
        let f = screen.visibleFrame
        let pw = p.frame.width
        let ph = p.frame.height
        let x: CGFloat
        let y: CGFloat
        switch corner {
        case .topLeft:     x = f.minX + offset.x;        y = f.maxY - ph - offset.y
        case .topRight:    x = f.maxX - pw - offset.x;   y = f.maxY - ph - offset.y
        case .bottomLeft:  x = f.minX + offset.x;        y = f.minY + offset.y
        case .bottomRight: x = f.maxX - pw - offset.x;   y = f.minY + offset.y
        }
        p.setFrameOrigin(NSPoint(x: x, y: y))
    }

    // MARK: - NSWindowDelegate (resize risposta)

    func windowDidResize(_ notification: Notification) {
        guard let tv = responseTextView,
              let sv = tv.enclosingScrollView else { return }
        let w = sv.contentSize.width
        let h = max(sv.contentSize.height, 80)
        tv.frame = NSRect(x: 0, y: 0, width: w, height: h)
    }

    // MARK: - Callbacks WebSocket

    private func wireCallbacks() {
        let wm = WebSocketManager.shared
        wm.onTextChunk    = { [weak self] text in self?.setResponse(text) }
        wm.onResponseDone = { [weak self] text in self?.setResponse(text) }

        // STT — SFSpeechRecognizer
        let vm = VoiceManager.shared
        vm.requestPermissions()

        vm.onError = { [weak self] _ in
            self?.resetMicButton()
            let s = SettingsManager.shared.settings
            if s.wakeWordEnabled { WakeWordManager.shared.start() }
            if s.clapWakeEnabled { ClapWakeManager.shared.start() }
        }

        // Risultato STT da Python (Whisper) — mostra testo e invia ad Ari
        wm.onSTTResult = { [weak self] text in
            guard let self, !text.isEmpty else { return }
            self.inputField?.stringValue = text
            self.resetMicButton()
            // Python chiama già _respond internamente — non serve sendMessage()
            // Mostriamo solo il testo nell'input field per feedback visivo
        }

        // TTS done → riavvia wake DOPO che Ari ha finito di parlare (evita il loop)
        WebSocketManager.shared.onTTSDone = { [weak self] in
            guard self != nil else { return }
            let s = SettingsManager.shared.settings
            guard s.wakeWordEnabled || s.clapWakeEnabled else { return }
            // Breve delay per evitare che il microfono catturi la coda audio del TTS
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) {
                guard !VoiceManager.shared.isRecording else { return }
                if s.wakeWordEnabled { WakeWordManager.shared.start() }
                if s.clapWakeEnabled { ClapWakeManager.shared.start() }
            }
        }

        // Vision — cattura schermo su richiesta di Python
        WebSocketManager.shared.onCaptureScreen = { prompt in
            VisionCapture.captureAndSend(prompt: prompt)
        }

        // Self-modify — mostra banner di approvazione
        WebSocketManager.shared.onDiffProposal = { description in
            ApprovalBanner.shared.show(description: description)
        }

        // Notifiche proattive — mostra banner macOS e aggiorna il pannello risposta
        WebSocketManager.shared.onProactiveNotification = { [weak self] title, body in
            NotificationManager.shared.show(title: title, body: body)
            self?.setResponse("[\(title)]\n\(body)")
            if self?.responsePanel?.isVisible == false {
                self?.responsePanel?.makeKeyAndOrderFront(nil)
            }
        }

        // Wake word — "ehi ari"
        WakeWordManager.shared.onWakeDetected = { [weak self] in
            guard let self else { return }
            ClapWakeManager.shared.stop()
            self.micButton?.contentTintColor = NSColor(red: 1.0, green: 0.25, blue: 0.25, alpha: 1.0)
            self.micButton?.image = NSImage(systemSymbolName: "mic.fill", accessibilityDescription: "Registra")
            self.inputField?.placeholderString = "⏺ ascolto..."
            VoiceManager.shared.startRecording(useVAD: true)
        }

        // Doppio battito — stile Iron Man
        ClapWakeManager.shared.onWakeDetected = { [weak self] in
            guard let self else { return }
            WakeWordManager.shared.stop()
            self.micButton?.contentTintColor = NSColor(red: 1.0, green: 0.25, blue: 0.25, alpha: 1.0)
            self.micButton?.image = NSImage(systemSymbolName: "mic.fill", accessibilityDescription: "Registra")
            self.inputField?.placeholderString = "⏺ ascolto..."
            VoiceManager.shared.startRecording(useVAD: true)
        }
    }

    private func resetMicButton() {
        micButton?.contentTintColor = NSColor.white.withAlphaComponent(0.4)
        micButton?.image = NSImage(systemSymbolName: "mic.circle.fill",
                                   accessibilityDescription: "Voce")
        inputField?.placeholderString = "Scrivi ad Ari..."
    }

    private func setResponse(_ text: String) {
        guard let tv = responseTextView else { return }
        tv.string = text
        tv.scrollToEndOfDocument(nil)
        if responsePanel?.isVisible == false {
            responsePanel?.makeKeyAndOrderFront(nil)
        }
    }

    // MARK: - Voce (hold-to-talk)

    private func voicePressed() {
        WakeWordManager.shared.stop()
        micButton?.contentTintColor = NSColor(red: 1.0, green: 0.25, blue: 0.25, alpha: 1.0)
        micButton?.image = NSImage(systemSymbolName: "mic.fill", accessibilityDescription: "Registra")
        inputField?.stringValue = ""
        inputField?.placeholderString = "⏺ ascolto..."
        VoiceManager.shared.startRecording(useVAD: false)
    }

    private func voiceReleased() {
        VoiceManager.shared.stopRecording()
        // Il mic button torna bianco quando arriva onFinalResult
        // (brevissimo ritardo mentre whisper finalizza)
    }

    // MARK: - Input

    @objc private func sendMessage() {
        guard let text = inputField?.stringValue.trimmingCharacters(in: .whitespaces),
              !text.isEmpty else { return }
        inputField?.stringValue = ""
        let lower = text.lowercased()
        if lower == "applica" {
            ApprovalBanner.shared.dismiss()
            WebSocketManager.shared.sendJSON(["type": "apply_patch"])
        } else if lower == "annulla" {
            ApprovalBanner.shared.dismiss()
            WebSocketManager.shared.sendJSON(["type": "reject_patch"])
        } else if lower == "stop" || lower == "basta" || lower == "silenzio"
               || lower == "ferma" || lower == "ari stop" || lower == "ari ferma"
               || lower.hasSuffix(" stop") || lower.hasSuffix(" ferma") {
            WebSocketManager.shared.sendJSON(["type": "tts_stop"])
        } else {
            WebSocketManager.shared.send(content: text)
        }
    }

    func control(_ control: NSControl, textView tv: NSTextView,
                 doCommandBy sel: Selector) -> Bool {
        if sel == #selector(NSResponder.insertNewline(_:)) { sendMessage(); return true }
        return false
    }

    // MARK: - Toggle

    @objc func toggleOrb() {
        guard let p = orbPanel else { return }
        p.isVisible ? p.orderOut(nil) : p.makeKeyAndOrderFront(nil)
    }

    @objc func toggleResponse() {
        guard let p = responsePanel else { return }
        p.isVisible ? p.orderOut(nil) : p.makeKeyAndOrderFront(nil)
    }

    @objc func toggleInput() {
        guard let p = inputPanel else { return }
        if p.isVisible {
            p.orderOut(nil)
        } else {
            p.makeKeyAndOrderFront(nil)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) {
                p.makeFirstResponder(self.inputField)
            }
        }
    }

    func toggleOrbVisibility() { toggleOrb() }

    @objc func toggleMemory() { MemoryPanel.shared.toggle() }
    @objc func toggleStats()  { StatsPanel.shared.toggle() }

    @objc private func captureScreen() {
        let prompt = inputField?.stringValue.trimmingCharacters(in: .whitespaces) ?? ""
        let effectivePrompt = prompt.isEmpty
            ? "Descrivi cosa vedi in questo screenshot macOS."
            : prompt
        inputField?.stringValue = ""
        VisionCapture.captureAndSend(prompt: effectivePrompt)
    }

    /// Chiamato dall'hotkey globale — toggle registrazione voce
    func activateVoiceHotkey() {
        if VoiceManager.shared.isRecording {
            voiceReleased()
            resetMicButton()
        } else {
            voicePressed()
        }
    }
}
