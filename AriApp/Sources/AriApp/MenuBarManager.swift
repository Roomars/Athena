import AppKit
import SwiftUI

// Finestre indipendenti:
//   orbPanel      — orb animato flottante (modalità floating)
//   notchPanel    — orb nel notch espandibile (modalità notch)
//   responsePanel — testo risposta, ridimensionabile
//   inputPanel    — campo input, ridimensionabile in larghezza

final class MenuBarManager: NSObject, NSTextFieldDelegate, NSWindowDelegate {

    private var statusItem:       NSStatusItem?
    private var orbPanel:         AriPanel?
    private var notchPanel:       NotchPanel?
    private var responsePanel:    AriPanel?
    private var inputPanel:       AriPanel?
    private var responseTextView: NSTextView?
    private var inputField:       NSTextField?
    private var micButton:        HoldMicButton?
    private var sendButton:       NSButton?
    private var autoHideTask:     DispatchWorkItem?

    func setup() {
        buildStatusItem()
        let s = SettingsManager.shared.settings
        if s.orbMode == .notch {
            buildNotchPanel()
        } else {
            buildOrbPanel()
        }
        buildResponsePanel()
        buildInputPanel()
        wireCallbacks()
        wireSnapManager()
        wireSettingsObservers()
        NotificationManager.shared.setup()
        if s.clapWakeEnabled { ClapWakeManager.shared.start() }
    }

    // MARK: - Notch Panel (modalità notch)

    private func buildNotchPanel() {
        notchPanel = NotchPanel.make()
    }

    func switchOrbMode(_ mode: OrbMode) {
        switch mode {
        case .notch:
            orbPanel?.orderOut(nil)
            orbPanel = nil
            if notchPanel == nil { notchPanel = NotchPanel.make() }
        case .floating:
            notchPanel?.orderOut(nil)
            notchPanel = nil
            if orbPanel == nil { buildOrbPanel(); orbPanel?.makeKeyAndOrderFront(nil) }
        }
        SettingsManager.shared.settings.orbMode = mode
        SettingsManager.shared.save()
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
        let w: CGFloat = 260
        let h: CGFloat = 260

        let p = makePanel(w: w, h: h, resizable: true, chrome: false)
        p.isMovableByWindowBackground = true
        p.backgroundColor = .clear
        p.isOpaque        = false
        p.hasShadow       = false
        p.minSize         = NSSize(width: 120, height: 120)
        p.delegate        = self

        let hosting = NSHostingController(rootView: OrbView())
        hosting.view.frame            = NSRect(x: 0, y: 0, width: w, height: h)
        hosting.view.autoresizingMask = [.width, .height]
        hosting.view.wantsLayer       = true
        hosting.view.layer?.backgroundColor = CGColor.clear
        p.contentView = hosting.view

        orbPanel = p
        restoreFrame(p) { self.place(p, corner: .topLeft, offset: NSPoint(x: 40, y: 40)) }
        p.makeKeyAndOrderFront(nil)
    }

    // MARK: - Response (ridimensionabile)

    private func buildResponsePanel() {
        let w: CGFloat = 340
        let h: CGFloat = 260

        let p = makePanel(w: w, h: h, resizable: true, chrome: true)
        p.minSize   = NSSize(width: 200, height: 100)
        p.delegate  = self

        let vibrancy = makeVibrancy(width: w, height: h)
        p.contentView = vibrancy

        let pad: CGFloat = 8
        let sv = NSScrollView(frame: NSRect(x: pad, y: pad, width: w - pad*2, height: h - pad*2))
        sv.autoresizingMask    = [.width, .height]
        sv.hasVerticalScroller = true
        sv.autohidesScrollers  = true
        sv.drawsBackground     = false
        vibrancy.addSubview(sv)

        let fontSize = CGFloat(SettingsManager.shared.settings.responseFontSize)
        let tv = NSTextView(frame: NSRect(x: 0, y: 0, width: w - pad*2, height: h - pad*2))
        tv.autoresizingMask    = [.width]
        tv.isEditable          = false
        tv.isSelectable        = true
        tv.drawsBackground     = false
        tv.textColor           = .white
        tv.font                = .systemFont(ofSize: fontSize)
        tv.textContainerInset  = NSSize(width: 8, height: 8)
        tv.isAutomaticLinkDetectionEnabled = false
        sv.documentView        = tv
        responseTextView       = tv

        responsePanel = p
        restoreFrame(p) { self.place(p, corner: .topRight, offset: NSPoint(x: 40, y: 40)) }
    }

    // MARK: - Input

    private func buildInputPanel() {
        let w: CGFloat = 340
        let h: CGFloat = 46

        let p = makePanel(w: w, h: h, resizable: true, chrome: true)
        p.minSize = NSSize(width: 200, height: h)
        p.maxSize = NSSize(width: 9999, height: h)

        let vibrancy = makeVibrancy(width: w, height: h, cornerRadius: 23)
        p.contentView = vibrancy

        let pad: CGFloat   = 8
        let btnSz: CGFloat = 26

        // Bottone invia (destra)
        let sendX = w - pad - btnSz - 4
        let sendBtn = NSButton(frame: NSRect(x: sendX, y: (h-btnSz)/2, width: btnSz, height: btnSz))
        sendBtn.bezelStyle       = .circular
        sendBtn.isBordered       = false
        sendBtn.image            = NSImage(systemSymbolName: "arrow.up.circle.fill",
                                           accessibilityDescription: "Invia")
        sendBtn.contentTintColor = ColorManager.shared.accentColor
        sendBtn.autoresizingMask = [.minXMargin]
        sendBtn.target = self
        sendBtn.action = #selector(sendMessage)
        vibrancy.addSubview(sendBtn)
        sendButton = sendBtn

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
        vibrancy.addSubview(camBtn)

        // Bottone microfono (sinistra) — hold-to-talk
        let micBtn = HoldMicButton(frame: NSRect(x: pad, y: (h-btnSz)/2, width: btnSz, height: btnSz))
        micBtn.bezelStyle       = .circular
        micBtn.isBordered       = false
        micBtn.image            = NSImage(systemSymbolName: "mic.circle.fill",
                                          accessibilityDescription: "Voce")
        micBtn.contentTintColor = NSColor.white.withAlphaComponent(0.4)
        micBtn.onPress   = { [weak self] in self?.voicePressed() }
        micBtn.onRelease = { [weak self] in self?.voiceReleased() }
        vibrancy.addSubview(micBtn)
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
        vibrancy.addSubview(field)
        inputField = field

        inputPanel = p
        restoreFrame(p) { self.place(p, corner: .bottomRight, offset: NSPoint(x: 40, y: 40)) }
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
            if resizable { mask.insert(.resizable) }
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
            p.backgroundColor = .clear
            p.isOpaque        = false
            p.hasShadow       = true
            p.standardWindowButton(.closeButton)?.isHidden       = true
            p.standardWindowButton(.miniaturizeButton)?.isHidden = true
            p.standardWindowButton(.zoomButton)?.isHidden        = true
        } else {
            p.backgroundColor = .clear
            p.isOpaque        = false
            p.hasShadow       = false
        }
        return p
    }

    // NSVisualEffectView stile FaceTime — sfondo vetro smerigliato scuro
    private func makeVibrancy(width: CGFloat, height: CGFloat, cornerRadius: CGFloat = 12) -> NSVisualEffectView {
        let v = NSVisualEffectView(frame: NSRect(x: 0, y: 0, width: width, height: height))
        v.material      = .hudWindow
        v.blendingMode  = .behindWindow
        v.state         = .active
        v.appearance    = NSAppearance(named: .darkAqua)
        v.autoresizingMask = [.width, .height]
        v.wantsLayer    = true
        v.layer?.cornerRadius  = cornerRadius
        v.layer?.masksToBounds = true
        return v
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

    // MARK: - Settings observers

    private func wireSettingsObservers() {
        NotificationCenter.default.addObserver(
            self, selector: #selector(onAccentColorChanged(_:)),
            name: ColorManager.accentDidChange, object: nil)
        NotificationCenter.default.addObserver(
            self, selector: #selector(onFontSizeChanged(_:)),
            name: .ariFontSizeChanged, object: nil)
    }

    @objc private func onAccentColorChanged(_ n: Notification) {
        guard let color = n.object as? NSColor else { return }
        sendButton?.contentTintColor = color
    }

    @objc private func onFontSizeChanged(_ n: Notification) {
        guard let size = n.object as? Double else { return }
        responseTextView?.font = .systemFont(ofSize: CGFloat(size))
    }

    // MARK: - NSWindowDelegate

    func windowDidResize(_ notification: Notification) {
        // Adatta il NSTextView alla nuova size del pannello risposta
        if let tv = responseTextView, let sv = tv.enclosingScrollView {
            let w = sv.contentSize.width
            let h = max(sv.contentSize.height, 80)
            tv.frame = NSRect(x: 0, y: 0, width: w, height: h)
        }
        if let panel = notification.object as? AriPanel { saveFrame(panel) }
    }

    func windowDidMove(_ notification: Notification) {
        if let panel = notification.object as? AriPanel { saveFrame(panel) }
    }

    // MARK: - Persistenza posizioni (Pack C)

    private func panelKey(_ panel: AriPanel) -> String? {
        if panel === orbPanel      { return "ari.frame.orb"      }
        if panel === responsePanel { return "ari.frame.response"  }
        if panel === inputPanel    { return "ari.frame.input"     }
        return nil
    }

    private func saveFrame(_ panel: AriPanel) {
        guard let key = panelKey(panel) else { return }
        let f = panel.frame
        UserDefaults.standard.set(
            [f.origin.x, f.origin.y, f.width, f.height],
            forKey: key
        )
    }

    private func restoreFrame(_ panel: AriPanel, fallback: () -> Void) {
        guard let key = panelKey(panel),
              let arr = UserDefaults.standard.array(forKey: key) as? [Double],
              arr.count == 4 else { fallback(); return }
        panel.setFrame(
            NSRect(x: arr[0], y: arr[1], width: arr[2], height: arr[3]),
            display: false
        )
    }

    // MARK: - Auto-resize contenuto risposta (Pack A)

    private func autoResizeResponse() {
        guard let panel = responsePanel,
              let tv    = responseTextView,
              let lm    = tv.layoutManager,
              let tc    = tv.textContainer else { return }

        lm.ensureLayout(for: tc)
        let textH  = lm.usedRect(for: tc).height + tv.textContainerInset.height * 2 + 20
        let screen = panel.screen ?? NSScreen.main
        let maxH   = (screen?.visibleFrame.height ?? 800) * 0.62
        let newH   = max(120, min(textH, maxH))

        guard abs(panel.frame.height - newH) > 6 else { return }

        var f = panel.frame
        f.origin.y  -= (newH - f.height)   // cresce verso l'alto
        f.size.height = newH
        NSAnimationContext.runAnimationGroup { ctx in
            ctx.duration        = 0.18
            ctx.timingFunction  = CAMediaTimingFunction(name: .easeOut)
            panel.animator().setFrame(f, display: true)
        }
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
        if let tv = responseTextView {
            tv.string = text
            tv.scrollToEndOfDocument(nil)
            if responsePanel?.isVisible == false {
                responsePanel?.makeKeyAndOrderFront(nil)
            }
            DispatchQueue.main.async { self.autoResizeResponse() }
        }
        if SettingsManager.shared.settings.orbMode == .notch {
            AriNotchViewModel.shared.setResponse(text)
        }
        scheduleAutoHide()
    }

    private func scheduleAutoHide() {
        autoHideTask?.cancel()
        let s = SettingsManager.shared.settings
        guard s.autoHideResponse else { return }
        let task = DispatchWorkItem { [weak self] in
            self?.responsePanel?.orderOut(nil)
        }
        autoHideTask = task
        DispatchQueue.main.asyncAfter(deadline: .now() + s.autoHideDelay, execute: task)
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
