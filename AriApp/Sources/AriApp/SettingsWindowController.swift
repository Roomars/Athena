import AppKit
import Combine
import ServiceManagement

// Finestra impostazioni con sidebar sinistra — stile openclaw / System Preferences compatto.
// Layout: sidebar 190pt | divisore | contenuto 420pt = 640pt totali

final class SettingsWindowController: NSWindowController, NSWindowDelegate {
    static let shared = SettingsWindowController()

    // MARK: - Struttura sidebar

    private struct SidebarItem {
        let id:    String
        let label: String
        let icon:  String
    }
    private let items: [SidebarItem] = [
        .init(id: "generale",  label: "Generale",  icon: "house.fill"),
        .init(id: "voce",      label: "Voce",      icon: "mic.fill"),
        .init(id: "aspetto",   label: "Aspetto",   icon: "paintbrush.fill"),
        .init(id: "avanzate",  label: "Avanzate",  icon: "gearshape.fill"),
    ]

    // MARK: - Layout constants
    private let sideW:   CGFloat = 190
    private let totalW:  CGFloat = 640
    private let totalH:  CGFloat = 480
    private var contentW: CGFloat { totalW - sideW - 1 }

    // MARK: - Subviews
    private var sidebar:     NSTableView!
    private var contentHost: NSView!            // contenitore destra — swappa i pannelli
    private var panels:      [String: NSView] = [:]
    private var selectedIdx: Int = 0

    // Controls — Voce
    private var ttsSwitch:        NSSwitch!
    private var ttsEngineControl: NSSegmentedControl!
    private var wakeSwitch:       NSSwitch!
    private var clapSwitch:       NSSwitch!
    private var hotkeyLabel:      NSTextField!
    private var recordingMode     = false
    private var localMonitor:     Any?

    // Controls — Generale
    private var proactiveSwitch:  NSSwitch!
    private var cpuThreshSlider:  NSSlider!
    private var ramThreshSlider:  NSSlider!
    private var tempThreshSlider: NSSlider!
    private var cpuThreshLabel:   NSTextField!
    private var ramThreshLabel:   NSTextField!
    private var tempThreshLabel:  NSTextField!
    private var loginSwitch:      NSSwitch!

    // Controls — Modello AI
    private var modelStatusDot:    NSView!
    private var modelStatusLabel:  NSTextField!
    private var backendControl:    NSSegmentedControl!
    private var localModelPopup:   NSPopUpButton!
    private var localModelBox:     NSView!
    private var orModelField:      NSTextField!
    private var orApiKeyField:     NSSecureTextField!
    private var orBox:             NSView!
    private var cancellables       = Set<AnyCancellable>()

    private let localModels = [
        "mlx-community/gemma-4-31b-it-4bit",
        "mlx-community/gemma-4-12b-it-4bit",
        "mlx-community/Qwen3-14B-4bit",
        "mlx-community/Llama-3.2-3B-Instruct-4bit",
        "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
    ]

    // Controls — Aspetto
    private var snapSwitch:           NSSwitch!
    private var orbModeControl:       NSSegmentedControl!
    private var opacitySlider:        NSSlider!
    private var accentColorWell:      NSColorWell!
    private var fontSlider:           NSSlider!
    private var fontSizeLabel:        NSTextField!
    private var autoHideSwitch:       NSSwitch!
    private var autoHideDelayStepper: NSStepper!
    private var autoHideDelayLabel:   NSTextField!

    // MARK: - Init

    private init() {
        let win = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: totalW, height: totalH),
            styleMask:   [.titled, .closable, .fullSizeContentView],
            backing:     .buffered,
            defer:       false
        )
        win.title                    = "Impostazioni Ari"
        win.isReleasedWhenClosed     = false
        win.titlebarAppearsTransparent = true
        win.titleVisibility          = .hidden
        win.center()
        super.init(window: win)
        win.delegate = self
        buildLayout()
    }

    required init?(coder: NSCoder) { fatalError() }

    func show() {
        refresh()
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    // MARK: - Layout

    private func buildLayout() {
        guard let content = window?.contentView else { return }
        content.wantsLayer = true

        // — Sidebar background (vibrancy)
        let sideVibrancy = NSVisualEffectView(frame: NSRect(x: 0, y: 0, width: sideW, height: totalH))
        sideVibrancy.material     = .sidebar
        sideVibrancy.blendingMode = .behindWindow
        sideVibrancy.state        = .active
        sideVibrancy.autoresizingMask = [.height]
        content.addSubview(sideVibrancy)

        // — Divisore verticale
        let div = NSView(frame: NSRect(x: sideW, y: 0, width: 1, height: totalH))
        div.wantsLayer = true
        div.layer?.backgroundColor = NSColor.separatorColor.cgColor
        div.autoresizingMask = [.height]
        content.addSubview(div)

        // — Area contenuto destra
        contentHost = NSView(frame: NSRect(x: sideW + 1, y: 0,
                                           width: contentW, height: totalH))
        contentHost.autoresizingMask = [.width, .height]
        content.addSubview(contentHost)

        // — Sidebar header
        let header = NSTextField(labelWithString: "Impostazioni")
        header.font      = .systemFont(ofSize: 13, weight: .semibold)
        header.textColor = .labelColor
        header.frame     = NSRect(x: 16, y: totalH - 56, width: sideW - 32, height: 20)
        header.autoresizingMask = [.minYMargin]
        sideVibrancy.addSubview(header)

        // — TableView sidebar
        let tv = NSTableView()
        tv.headerView      = nil
        tv.backgroundColor = .clear
        tv.style           = .sourceList
        tv.rowHeight       = 36
        tv.intercellSpacing = NSSize(width: 0, height: 2)
        let col = NSTableColumn(identifier: .init("main"))
        col.width = sideW - 16
        tv.addTableColumn(col)
        tv.dataSource = self
        tv.delegate   = self
        sidebar        = tv

        let sv = NSScrollView(frame: NSRect(x: 8, y: 8, width: sideW - 16,
                                             height: totalH - 72))
        sv.documentView    = tv
        sv.hasVerticalScroller  = false
        sv.drawsBackground = false
        sv.autoresizingMask = [.height]
        sideVibrancy.addSubview(sv)

        // — Costruisce tutti i pannelli una sola volta
        panels["generale"]  = buildGenerale()
        panels["voce"]      = buildVoce()
        panels["aspetto"]   = buildAspetto()
        panels["avanzate"]  = buildAvanzate()

        tv.reloadData()
        selectItem(at: 0, animated: false)
    }

    // MARK: - Selezione

    private func selectItem(at idx: Int, animated: Bool) {
        guard idx >= 0 && idx < items.count else { return }
        selectedIdx = idx
        sidebar.selectRowIndexes(IndexSet(integer: idx), byExtendingSelection: false)

        let id = items[idx].id
        guard let panel = panels[id] else { return }

        contentHost.subviews.forEach { $0.removeFromSuperview() }
        panel.frame = contentHost.bounds
        panel.autoresizingMask = [.width, .height]
        contentHost.addSubview(panel)
    }

    // MARK: - Pannello GENERALE

    private func buildGenerale() -> NSView {
        let s   = SettingsManager.shared.settings
        let stk = makeStack()

        stk.addArrangedSubview(sectionHeader("AVVIO"))
        stk.setCustomSpacing(10, after: stk.arrangedSubviews.last!)

        loginSwitch = NSSwitch()
        loginSwitch.state  = SMAppService.mainApp.status == .enabled ? .on : .off
        loginSwitch.target = self
        loginSwitch.action = #selector(loginChanged)
        stk.addArrangedSubview(row(label: "Avvia con il Mac",
                                   detail: "Ari si avvia automaticamente al login",
                                   control: loginSwitch))
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)
        stk.addArrangedSubview(separator())
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)

        stk.addArrangedSubview(sectionHeader("NOTIFICHE PROATTIVE"))
        stk.setCustomSpacing(10, after: stk.arrangedSubviews.last!)

        proactiveSwitch = NSSwitch()
        proactiveSwitch.state  = s.proactiveEnabled ? .on : .off
        proactiveSwitch.target = self
        proactiveSwitch.action = #selector(proactiveChanged)
        stk.addArrangedSubview(row(label: "Monitoraggio attivo",
                                   detail: "Ari avvisa per CPU, RAM, temperatura e anomalie",
                                   control: proactiveSwitch))
        stk.setCustomSpacing(12, after: stk.arrangedSubviews.last!)

        // CPU threshold
        cpuThreshLabel = valueLabel("\(Int(s.cpuAlertThreshold))%")
        cpuThreshSlider = NSSlider(value: s.cpuAlertThreshold,
                                   minValue: 60, maxValue: 100,
                                   target: self, action: #selector(cpuThreshChanged))
        cpuThreshSlider.numberOfTickMarks = 5
        stk.addArrangedSubview(row(label: "Soglia alert CPU",
                                   control: sliderPair(cpuThreshSlider, cpuThreshLabel)))
        stk.setCustomSpacing(8, after: stk.arrangedSubviews.last!)

        // RAM threshold
        ramThreshLabel = valueLabel("\(Int(s.ramAlertThreshold))%")
        ramThreshSlider = NSSlider(value: s.ramAlertThreshold,
                                   minValue: 60, maxValue: 100,
                                   target: self, action: #selector(ramThreshChanged))
        ramThreshSlider.numberOfTickMarks = 5
        stk.addArrangedSubview(row(label: "Soglia alert RAM",
                                   control: sliderPair(ramThreshSlider, ramThreshLabel)))
        stk.setCustomSpacing(8, after: stk.arrangedSubviews.last!)

        // Temp threshold
        tempThreshLabel = valueLabel("\(Int(s.tempAlertThreshold))°C")
        tempThreshSlider = NSSlider(value: s.tempAlertThreshold,
                                    minValue: 60, maxValue: 100,
                                    target: self, action: #selector(tempThreshChanged))
        tempThreshSlider.numberOfTickMarks = 5
        stk.addArrangedSubview(row(label: "Soglia alert Temp",
                                   control: sliderPair(tempThreshSlider, tempThreshLabel)))

        return wrap(stk)
    }

    // MARK: - Pannello VOCE

    private func buildVoce() -> NSView {
        let s   = SettingsManager.shared.settings
        let stk = makeStack()

        stk.addArrangedSubview(sectionHeader("SINTESI VOCALE"))
        stk.setCustomSpacing(10, after: stk.arrangedSubviews.last!)

        ttsSwitch = NSSwitch()
        ttsSwitch.state  = s.ttsEnabled ? .on : .off
        ttsSwitch.target = self
        ttsSwitch.action = #selector(ttsChanged)
        stk.addArrangedSubview(row(label: "Voce di risposta (TTS)", control: ttsSwitch))
        stk.setCustomSpacing(8, after: stk.arrangedSubviews.last!)

        ttsEngineControl = NSSegmentedControl(
            labels: ["Apple (Federica)", "Kokoro"],
            trackingMode: .selectOne,
            target: self, action: #selector(ttsEngineChanged)
        )
        ttsEngineControl.selectedSegment = s.ttsEngine == "kokoro" ? 1 : 0
        stk.addArrangedSubview(row(label: "Motore TTS",
                                   detail: "Kokoro richiede: pip install kokoro soundfile",
                                   control: ttsEngineControl))
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)
        stk.addArrangedSubview(separator())
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)

        stk.addArrangedSubview(sectionHeader("ATTIVAZIONE"))
        stk.setCustomSpacing(10, after: stk.arrangedSubviews.last!)

        wakeSwitch = NSSwitch()
        wakeSwitch.state  = s.wakeWordEnabled ? .on : .off
        wakeSwitch.target = self
        wakeSwitch.action = #selector(wakeChanged)
        stk.addArrangedSubview(row(label: "Wake word",
                                   detail: "\"Ehi Ari\" attiva il microfono",
                                   control: wakeSwitch))
        stk.setCustomSpacing(8, after: stk.arrangedSubviews.last!)

        clapSwitch = NSSwitch()
        clapSwitch.state  = s.clapWakeEnabled ? .on : .off
        clapSwitch.target = self
        clapSwitch.action = #selector(clapChanged)
        stk.addArrangedSubview(row(label: "Doppio battito",
                                   detail: "Stile Iron Man — batti le mani due volte",
                                   control: clapSwitch))
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)
        stk.addArrangedSubview(separator())
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)

        stk.addArrangedSubview(sectionHeader("SCORCIATOIA TASTIERA"))
        stk.setCustomSpacing(10, after: stk.arrangedSubviews.last!)

        hotkeyLabel = NSTextField(labelWithString: currentHotkeyString())
        hotkeyLabel.font      = .monospacedSystemFont(ofSize: 18, weight: .semibold)
        hotkeyLabel.textColor = .controlAccentColor

        let editBtn = NSButton(title: "Modifica", target: self, action: #selector(startRecording))
        editBtn.bezelStyle = .rounded

        let hotkeyRow = NSStackView(views: [hotkeyLabel, editBtn])
        hotkeyRow.spacing = 16
        hotkeyRow.translatesAutoresizingMaskIntoConstraints = false
        hotkeyRow.widthAnchor.constraint(equalToConstant: rowW).isActive = true
        stk.addArrangedSubview(hotkeyRow)

        return wrap(stk)
    }

    // MARK: - Pannello ASPETTO

    private func buildAspetto() -> NSView {
        let s   = SettingsManager.shared.settings
        let stk = makeStack()

        stk.addArrangedSubview(sectionHeader("MODALITÀ ORB"))
        stk.setCustomSpacing(10, after: stk.arrangedSubviews.last!)

        orbModeControl = NSSegmentedControl(
            labels: ["Flottante", "Notch"],
            trackingMode: .selectOne,
            target: self, action: #selector(orbModeChanged)
        )
        orbModeControl.selectedSegment = s.orbMode == .notch ? 1 : 0
        stk.addArrangedSubview(row(label: "Posizione orb",
                                   detail: "Pannello flottante libero o ancorato al notch",
                                   control: orbModeControl))
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)
        stk.addArrangedSubview(separator())
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)

        stk.addArrangedSubview(sectionHeader("FINESTRE"))
        stk.setCustomSpacing(10, after: stk.arrangedSubviews.last!)

        snapSwitch = NSSwitch()
        snapSwitch.state  = s.snapEnabled ? .on : .off
        snapSwitch.target = self
        snapSwitch.action = #selector(snapChanged)
        stk.addArrangedSubview(row(label: "Aggancio magnetico",
                                   detail: "I pannelli si agganciano tra loro e ai bordi",
                                   control: snapSwitch))
        stk.setCustomSpacing(8, after: stk.arrangedSubviews.last!)

        opacitySlider = NSSlider(value: Double(s.panelOpacity),
                                 minValue: 0.4, maxValue: 1.0,
                                 target: self, action: #selector(opacityChanged))
        opacitySlider.controlSize = .small
        stk.addArrangedSubview(row(label: "Opacità pannelli",
                                   detail: "Trasparenza pannelli risposta e input",
                                   control: opacitySlider))
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)
        stk.addArrangedSubview(separator())
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)

        // ── COLORI ──
        stk.addArrangedSubview(sectionHeader("COLORI"))
        stk.setCustomSpacing(10, after: stk.arrangedSubviews.last!)

        accentColorWell = NSColorWell()
        accentColorWell.color  = ColorManager.shared.accentColor
        accentColorWell.target = self
        accentColorWell.action = #selector(accentColorChanged)
        accentColorWell.translatesAutoresizingMaskIntoConstraints = false
        accentColorWell.widthAnchor.constraint(equalToConstant: 44).isActive  = true
        accentColorWell.heightAnchor.constraint(equalToConstant: 28).isActive = true
        stk.addArrangedSubview(row(label: "Colore accent",
                                   detail: "Usato per pulsanti e testo in evidenza",
                                   control: accentColorWell))
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)
        stk.addArrangedSubview(separator())
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)

        // ── RISPOSTA ──
        stk.addArrangedSubview(sectionHeader("PANNELLO RISPOSTA"))
        stk.setCustomSpacing(10, after: stk.arrangedSubviews.last!)

        fontSizeLabel = valueLabel("\(Int(s.responseFontSize))pt")
        fontSlider = NSSlider(value: s.responseFontSize,
                              minValue: 11, maxValue: 17,
                              target: self, action: #selector(fontSizeChanged))
        fontSlider.numberOfTickMarks = 7
        fontSlider.allowsTickMarkValuesOnly = true
        stk.addArrangedSubview(row(label: "Dimensione testo",
                                   control: sliderPair(fontSlider, fontSizeLabel)))
        stk.setCustomSpacing(8, after: stk.arrangedSubviews.last!)

        autoHideSwitch = NSSwitch()
        autoHideSwitch.state  = s.autoHideResponse ? .on : .off
        autoHideSwitch.target = self
        autoHideSwitch.action = #selector(autoHideChanged)
        stk.addArrangedSubview(row(label: "Nascondi risposta",
                                   detail: "Chiude il pannello dopo X secondi dall'ultima risposta",
                                   control: autoHideSwitch))
        stk.setCustomSpacing(8, after: stk.arrangedSubviews.last!)

        autoHideDelayLabel = NSTextField(labelWithString: "\(Int(s.autoHideDelay))s")
        autoHideDelayLabel.font      = .monospacedSystemFont(ofSize: 12, weight: .medium)
        autoHideDelayLabel.textColor = .secondaryLabelColor
        autoHideDelayLabel.alignment = .right
        autoHideDelayLabel.translatesAutoresizingMaskIntoConstraints = false
        autoHideDelayLabel.widthAnchor.constraint(equalToConstant: 34).isActive = true

        autoHideDelayStepper = NSStepper()
        autoHideDelayStepper.minValue  = 3
        autoHideDelayStepper.maxValue  = 60
        autoHideDelayStepper.increment = 1
        autoHideDelayStepper.doubleValue = s.autoHideDelay
        autoHideDelayStepper.target    = self
        autoHideDelayStepper.action    = #selector(autoHideDelayChanged)

        let stepRow = NSStackView(views: [autoHideDelayLabel, autoHideDelayStepper])
        stepRow.spacing = 4
        stk.addArrangedSubview(row(label: "Ritardo auto-hide",
                                   control: stepRow))

        return wrap(stk)
    }

    // MARK: - Pannello AVANZATE

    private func buildAvanzate() -> NSView {
        let s   = SettingsManager.shared.settings
        let stk = makeStack()

        // ── MODELLO AI ──────────────────────────────────────────────────

        stk.addArrangedSubview(sectionHeader("MODELLO AI"))
        stk.setCustomSpacing(10, after: stk.arrangedSubviews.last!)

        // Stato dinamico (dot + label)
        let dot = NSView()
        dot.wantsLayer = true
        dot.layer?.cornerRadius = 4
        dot.layer?.backgroundColor = NSColor.systemGray.cgColor
        dot.translatesAutoresizingMaskIntoConstraints = false
        dot.widthAnchor.constraint(equalToConstant: 8).isActive  = true
        dot.heightAnchor.constraint(equalToConstant: 8).isActive = true
        modelStatusDot = dot

        modelStatusLabel = NSTextField(labelWithString: "Caricamento...")
        modelStatusLabel.font      = .monospacedSystemFont(ofSize: 11, weight: .regular)
        modelStatusLabel.textColor = .secondaryLabelColor

        let statusRow = NSStackView(views: [dot, modelStatusLabel])
        statusRow.spacing = 6
        stk.addArrangedSubview(statusRow)
        stk.setCustomSpacing(12, after: statusRow)

        // Backend segmented
        backendControl = NSSegmentedControl(
            labels: ["Locale MLX", "OpenRouter"],
            trackingMode: .selectOne,
            target: self, action: #selector(backendChanged)
        )
        backendControl.selectedSegment = s.selectedBackend == "openrouter" ? 1 : 0
        stk.addArrangedSubview(row(label: "Backend", control: backendControl))
        stk.setCustomSpacing(12, after: stk.arrangedSubviews.last!)

        // Locale MLX — popup preset
        localModelPopup = NSPopUpButton()
        localModels.forEach { localModelPopup.addItem(withTitle: $0) }
        if case .ready(let current) = WebSocketManager.shared.modelState,
           let idx = localModels.firstIndex(of: current) {
            localModelPopup.selectItem(at: idx)
        }
        localModelBox = row(label: "Modello locale", control: localModelPopup)
        stk.addArrangedSubview(localModelBox)
        stk.setCustomSpacing(8, after: localModelBox)

        // OpenRouter — model id + api key
        orModelField            = NSTextField()
        orModelField.placeholderString = "es. openai/gpt-4o"
        orModelField.stringValue       = s.openRouterModelId
        orModelField.translatesAutoresizingMaskIntoConstraints = false
        orModelField.widthAnchor.constraint(equalToConstant: 190).isActive = true

        orApiKeyField            = NSSecureTextField()
        orApiKeyField.placeholderString = "sk-or-..."
        orApiKeyField.stringValue       = s.openRouterApiKey
        orApiKeyField.translatesAutoresizingMaskIntoConstraints = false
        orApiKeyField.widthAnchor.constraint(equalToConstant: 190).isActive = true

        let orModelRow = row(label: "Modello", control: orModelField)
        let orKeyRow   = row(label: "API Key",
                             detail: "Crea chiave su openrouter.ai/keys",
                             control: orApiKeyField)
        let orInner    = NSStackView(views: [orModelRow, orKeyRow])
        orInner.orientation = .vertical
        orInner.spacing     = 8
        orInner.translatesAutoresizingMaskIntoConstraints = false

        let orWrap = NSView()
        orWrap.translatesAutoresizingMaskIntoConstraints = false
        orWrap.addSubview(orInner)
        NSLayoutConstraint.activate([
            orInner.topAnchor.constraint(equalTo: orWrap.topAnchor),
            orInner.leadingAnchor.constraint(equalTo: orWrap.leadingAnchor),
            orInner.bottomAnchor.constraint(equalTo: orWrap.bottomAnchor),
            orInner.trailingAnchor.constraint(equalTo: orWrap.trailingAnchor),
        ])
        orBox = orWrap
        stk.addArrangedSubview(orBox)
        stk.setCustomSpacing(16, after: orBox)

        // Pulsanti azione
        let changeBtn    = NSButton(title: "Cambia",    target: self, action: #selector(changeModel))
        let reloadBtn    = NSButton(title: "Riavvia",   target: self, action: #selector(reloadModel))
        let redownBtn    = NSButton(title: "Riscarica", target: self, action: #selector(redownloadModel))
        [changeBtn, reloadBtn, redownBtn].forEach { $0.bezelStyle = .rounded }
        let actRow = NSStackView(views: [changeBtn, reloadBtn, redownBtn])
        actRow.spacing = 8
        stk.addArrangedSubview(actRow)
        stk.setCustomSpacing(20, after: actRow)
        stk.addArrangedSubview(separator())
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)

        updateBackendVisibility()
        updateModelStatusLabel(WebSocketManager.shared.modelState)

        // Combine: aggiorna lo stato in tempo reale
        WebSocketManager.shared.$modelState
            .receive(on: DispatchQueue.main)
            .sink { [weak self] state in self?.updateModelStatusLabel(state) }
            .store(in: &cancellables)

        // ── BRAIN ───────────────────────────────────────────────────────

        stk.addArrangedSubview(sectionHeader("BRAIN"))
        stk.setCustomSpacing(10, after: stk.arrangedSubviews.last!)

        let restartBtn = NSButton(title: "Riavvia brain", target: self, action: #selector(restartBrain))
        restartBtn.bezelStyle = .rounded
        stk.addArrangedSubview(row(label: "Processo Python",
                                   detail: "Ferma e rilancia il daemon (utile dopo aggiornamenti)",
                                   control: restartBtn))
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)
        stk.addArrangedSubview(separator())
        stk.setCustomSpacing(20, after: stk.arrangedSubviews.last!)

        // ── DIAGNOSTICA ─────────────────────────────────────────────────

        stk.addArrangedSubview(sectionHeader("DIAGNOSTICA"))
        stk.setCustomSpacing(10, after: stk.arrangedSubviews.last!)

        let logsBtn = NSButton(title: "Apri log Python", target: self, action: #selector(openLogs))
        logsBtn.bezelStyle = .rounded
        stk.addArrangedSubview(logsBtn)
        stk.setCustomSpacing(8, after: stk.arrangedSubviews.last!)

        let resetBtn = NSButton(title: "Reset posizioni pannelli", target: self, action: #selector(resetFrames))
        resetBtn.bezelStyle = .rounded
        stk.addArrangedSubview(resetBtn)

        return wrapScrollable(stk)
    }

    private func updateBackendVisibility() {
        let isOR = backendControl.selectedSegment == 1
        localModelBox?.isHidden = isOR
        orBox?.isHidden         = !isOR
    }

    private func updateModelStatusLabel(_ state: ModelState) {
        switch state {
        case .loading:
            modelStatusDot?.layer?.backgroundColor   = NSColor.systemOrange.cgColor
            modelStatusLabel?.stringValue            = "Caricamento modello..."
            modelStatusLabel?.textColor              = .systemOrange
        case .ready(let id):
            modelStatusDot?.layer?.backgroundColor   = NSColor.systemGreen.cgColor
            let short = id.components(separatedBy: "/").last ?? id
            modelStatusLabel?.stringValue            = "Pronto — \(short)"
            modelStatusLabel?.textColor              = .secondaryLabelColor
        }
    }

    // MARK: - Helpers UI

    private let rowW: CGFloat = 372   // contentW - 2×24

    private func makeStack() -> NSStackView {
        let s = NSStackView()
        s.orientation  = .vertical
        s.alignment    = .leading
        s.spacing      = 0
        s.edgeInsets   = NSEdgeInsets(top: 24, left: 24, bottom: 24, right: 24)
        s.translatesAutoresizingMaskIntoConstraints = false
        return s
    }

    private func wrap(_ stk: NSStackView) -> NSView {
        let v = NSView()
        v.translatesAutoresizingMaskIntoConstraints = false
        v.addSubview(stk)
        NSLayoutConstraint.activate([
            stk.topAnchor.constraint(equalTo: v.topAnchor),
            stk.leadingAnchor.constraint(equalTo: v.leadingAnchor),
            stk.bottomAnchor.constraint(lessThanOrEqualTo: v.bottomAnchor),
        ])
        return v
    }

    private func wrapScrollable(_ stk: NSStackView) -> NSView {
        let clipDoc = NSView()
        clipDoc.translatesAutoresizingMaskIntoConstraints = false
        clipDoc.addSubview(stk)
        NSLayoutConstraint.activate([
            stk.topAnchor.constraint(equalTo: clipDoc.topAnchor),
            stk.leadingAnchor.constraint(equalTo: clipDoc.leadingAnchor),
            stk.trailingAnchor.constraint(equalTo: clipDoc.trailingAnchor),
            stk.bottomAnchor.constraint(equalTo: clipDoc.bottomAnchor),
        ])

        let sv = NSScrollView()
        sv.translatesAutoresizingMaskIntoConstraints = false
        sv.hasVerticalScroller = true
        sv.hasHorizontalScroller = false
        sv.drawsBackground = false
        sv.documentView    = clipDoc

        // Forza larghezza pari al contentW così lo stack non si comprime
        clipDoc.widthAnchor.constraint(equalToConstant: contentW).isActive = true

        return sv
    }

    private func sectionHeader(_ text: String) -> NSTextField {
        let f = NSTextField(labelWithString: text)
        f.font      = .systemFont(ofSize: 11, weight: .semibold)
        f.textColor = .secondaryLabelColor
        return f
    }

    private func row(label: String, detail: String? = nil, control: NSView) -> NSView {
        let container = NSView()
        container.translatesAutoresizingMaskIntoConstraints = false

        let titleLbl = NSTextField(labelWithString: label)
        titleLbl.font = .systemFont(ofSize: 13)
        titleLbl.textColor = .labelColor
        titleLbl.translatesAutoresizingMaskIntoConstraints = false
        container.addSubview(titleLbl)

        control.translatesAutoresizingMaskIntoConstraints = false
        container.addSubview(control)

        let rowH: CGFloat = detail != nil ? 52 : 36

        if let detail {
            let d = NSTextField(labelWithString: detail)
            d.font = .systemFont(ofSize: 11)
            d.textColor = .secondaryLabelColor
            d.translatesAutoresizingMaskIntoConstraints = false
            container.addSubview(d)
            NSLayoutConstraint.activate([
                titleLbl.topAnchor.constraint(equalTo: container.topAnchor, constant: 8),
                titleLbl.leadingAnchor.constraint(equalTo: container.leadingAnchor),
                d.topAnchor.constraint(equalTo: titleLbl.bottomAnchor, constant: 2),
                d.leadingAnchor.constraint(equalTo: container.leadingAnchor),
                d.trailingAnchor.constraint(lessThanOrEqualTo: control.leadingAnchor, constant: -8),
            ])
        } else {
            NSLayoutConstraint.activate([
                titleLbl.centerYAnchor.constraint(equalTo: container.centerYAnchor),
                titleLbl.leadingAnchor.constraint(equalTo: container.leadingAnchor),
            ])
        }

        NSLayoutConstraint.activate([
            control.centerYAnchor.constraint(equalTo: container.centerYAnchor),
            control.trailingAnchor.constraint(equalTo: container.trailingAnchor),
            container.heightAnchor.constraint(equalToConstant: rowH),
            container.widthAnchor.constraint(equalToConstant: rowW),
        ])
        return container
    }

    // Coppia slider + etichetta valore — usata per font size e soglie
    private func sliderPair(_ slider: NSSlider, _ label: NSTextField) -> NSView {
        slider.controlSize = .small
        slider.translatesAutoresizingMaskIntoConstraints = false
        slider.widthAnchor.constraint(equalToConstant: 110).isActive = true
        label.translatesAutoresizingMaskIntoConstraints = false
        label.widthAnchor.constraint(equalToConstant: 40).isActive = true
        label.alignment = .right
        let s = NSStackView(views: [slider, label])
        s.spacing = 6
        return s
    }

    private func valueLabel(_ text: String) -> NSTextField {
        let f = NSTextField(labelWithString: text)
        f.font      = .monospacedSystemFont(ofSize: 12, weight: .medium)
        f.textColor = .secondaryLabelColor
        return f
    }

    private func separator() -> NSBox {
        let b = NSBox()
        b.boxType = .separator
        b.translatesAutoresizingMaskIntoConstraints = false
        b.widthAnchor.constraint(equalToConstant: rowW).isActive = true
        return b
    }

    // MARK: - Actions

    @objc private func loginChanged() {
        let on = loginSwitch.state == .on
        do {
            if on { try SMAppService.mainApp.register()   }
            else  { try SMAppService.mainApp.unregister() }
        } catch {
            loginSwitch.state = on ? .off : .on
        }
    }

    @objc private func proactiveChanged() {
        SettingsManager.shared.settings.proactiveEnabled = proactiveSwitch.state == .on
        SettingsManager.shared.save()
    }

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

    @objc private func snapChanged() {
        let on = snapSwitch.state == .on
        SettingsManager.shared.settings.snapEnabled = on
        SettingsManager.shared.save()
        if !on { SnapManager.shared.separateAll() }
    }

    @objc private func orbModeChanged() {
        let mode: OrbMode = orbModeControl.selectedSegment == 1 ? .notch : .floating
        if let delegate = NSApp.delegate as? AppDelegate {
            delegate.menuBar.switchOrbMode(mode)
        }
    }

    @objc private func opacityChanged() {
        SettingsManager.shared.settings.panelOpacity = Float(opacitySlider.doubleValue)
        SettingsManager.shared.save()
    }

    @objc private func ttsEngineChanged() {
        let engine = ttsEngineControl.selectedSegment == 1 ? "kokoro" : "apple"
        SettingsManager.shared.settings.ttsEngine = engine
        SettingsManager.shared.save()
        WebSocketManager.shared.sendJSON(["type": "set_tts_engine", "engine": engine])
    }

    @objc private func cpuThreshChanged() {
        let v = cpuThreshSlider.doubleValue
        SettingsManager.shared.settings.cpuAlertThreshold = v
        SettingsManager.shared.save()
        cpuThreshLabel.stringValue = "\(Int(v))%"
        sendThresholds()
    }

    @objc private func ramThreshChanged() {
        let v = ramThreshSlider.doubleValue
        SettingsManager.shared.settings.ramAlertThreshold = v
        SettingsManager.shared.save()
        ramThreshLabel.stringValue = "\(Int(v))%"
        sendThresholds()
    }

    @objc private func tempThreshChanged() {
        let v = tempThreshSlider.doubleValue
        SettingsManager.shared.settings.tempAlertThreshold = v
        SettingsManager.shared.save()
        tempThreshLabel.stringValue = "\(Int(v))°C"
        sendThresholds()
    }

    private func sendThresholds() {
        let s = SettingsManager.shared.settings
        WebSocketManager.shared.sendJSON([
            "type": "set_thresholds",
            "cpu":  s.cpuAlertThreshold,
            "ram":  s.ramAlertThreshold,
            "temp": s.tempAlertThreshold,
        ])
    }

    @objc private func accentColorChanged() {
        ColorManager.shared.apply(accentColorWell.color)
    }

    @objc private func fontSizeChanged() {
        let v = fontSlider.doubleValue
        SettingsManager.shared.settings.responseFontSize = v
        SettingsManager.shared.save()
        fontSizeLabel.stringValue = "\(Int(v))pt"
        NotificationCenter.default.post(name: .ariFontSizeChanged, object: v)
    }

    @objc private func autoHideChanged() {
        SettingsManager.shared.settings.autoHideResponse = autoHideSwitch.state == .on
        SettingsManager.shared.save()
    }

    @objc private func autoHideDelayChanged() {
        let v = autoHideDelayStepper.doubleValue
        SettingsManager.shared.settings.autoHideDelay = v
        SettingsManager.shared.save()
        autoHideDelayLabel.stringValue = "\(Int(v))s"
    }

    @objc private func backendChanged() {
        updateBackendVisibility()
    }

    @objc private func changeModel() {
        let s = SettingsManager.shared.settings
        let isOR = backendControl.selectedSegment == 1
        if isOR {
            let modelId = orModelField.stringValue.trimmingCharacters(in: .whitespaces)
            let apiKey  = orApiKeyField.stringValue.trimmingCharacters(in: .whitespaces)
            guard !modelId.isEmpty else { return }
            SettingsManager.shared.settings.selectedBackend   = "openrouter"
            SettingsManager.shared.settings.openRouterModelId = modelId
            SettingsManager.shared.settings.openRouterApiKey  = apiKey
            SettingsManager.shared.save()
            WebSocketManager.shared.switchModel(modelId: modelId, backend: "openrouter", apiKey: apiKey)
        } else {
            let modelId = localModels[localModelPopup.indexOfSelectedItem]
            SettingsManager.shared.settings.selectedBackend = "mlx"
            SettingsManager.shared.save()
            WebSocketManager.shared.switchModel(modelId: modelId, backend: "mlx")
        }
        _ = s // silence unused warning
    }

    @objc private func reloadModel() {
        WebSocketManager.shared.reloadModel()
    }

    @objc private func redownloadModel() {
        let alert = NSAlert()
        alert.messageText     = "Riscarica modello?"
        alert.informativeText = "Il modello verrà eliminato e riscaricato. L'operazione può richiedere diversi minuti."
        alert.addButton(withTitle: "Riscarica")
        alert.addButton(withTitle: "Annulla")
        alert.alertStyle = .warning
        guard alert.runModal() == .alertFirstButtonReturn else { return }
        WebSocketManager.shared.redownloadModel()
    }

    @objc private func restartBrain() {
        DaemonManager.shared.stop()
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
            DaemonManager.shared.start()
        }
    }

    @objc private func openLogs() {
        let url = URL(fileURLWithPath: NSHomeDirectory() + "/Documents/Athena/ari/brain/ari.log")
        if FileManager.default.fileExists(atPath: url.path) {
            NSWorkspace.shared.open(url)
        }
    }

    @objc private func resetFrames() {
        ["ari.frame.orb", "ari.frame.response", "ari.frame.input"].forEach {
            UserDefaults.standard.removeObject(forKey: $0)
        }
    }

    // MARK: - Hotkey

    @objc private func startRecording() {
        guard !recordingMode else { return }
        recordingMode = true
        hotkeyLabel.stringValue = "⌨ Premi…"
        hotkeyLabel.textColor   = .systemYellow

        localMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            self?.captureHotkey(event: event)
            return nil
        }
    }

    private func captureHotkey(event: NSEvent) {
        defer {
            recordingMode = false
            if let m = localMonitor { NSEvent.removeMonitor(m); localMonitor = nil }
        }
        guard event.keyCode != 53 else {
            hotkeyLabel.stringValue = currentHotkeyString()
            hotkeyLabel.textColor   = .controlAccentColor
            return
        }
        var modRaw: UInt64 = 0
        let m = event.modifierFlags
        if m.contains(.command) { modRaw |= CGEventFlags.maskCommand.rawValue   }
        if m.contains(.shift)   { modRaw |= CGEventFlags.maskShift.rawValue     }
        if m.contains(.option)  { modRaw |= CGEventFlags.maskAlternate.rawValue }
        if m.contains(.control) { modRaw |= CGEventFlags.maskControl.rawValue   }
        SettingsManager.shared.settings.hotkeyKeyCode   = Int(event.keyCode)
        SettingsManager.shared.settings.hotkeyModifiers = modRaw
        SettingsManager.shared.save()
        hotkeyLabel.stringValue = currentHotkeyString()
        hotkeyLabel.textColor   = .controlAccentColor
        HotkeyManager.shared.updateFromSettings()
    }

    private func currentHotkeyString() -> String {
        let s = SettingsManager.shared.settings
        return HotkeyManager.formatHotkey(keyCode: s.hotkeyKeyCode, modifiers: s.hotkeyModifiers)
    }

    // MARK: - Sync

    private func refresh() {
        let s = SettingsManager.shared.settings
        ttsSwitch?.state                = s.ttsEnabled        ? .on : .off
        ttsEngineControl?.selectedSegment = s.ttsEngine == "kokoro" ? 1 : 0
        wakeSwitch?.state               = s.wakeWordEnabled   ? .on : .off
        clapSwitch?.state               = s.clapWakeEnabled   ? .on : .off
        proactiveSwitch?.state          = s.proactiveEnabled  ? .on : .off
        snapSwitch?.state               = s.snapEnabled       ? .on : .off
        orbModeControl?.selectedSegment  = s.orbMode == .notch ? 1 : 0
        opacitySlider?.doubleValue      = Double(s.panelOpacity)
        hotkeyLabel?.stringValue        = currentHotkeyString()
        loginSwitch?.state              = SMAppService.mainApp.status == .enabled ? .on : .off
        cpuThreshSlider?.doubleValue    = s.cpuAlertThreshold
        cpuThreshLabel?.stringValue     = "\(Int(s.cpuAlertThreshold))%"
        ramThreshSlider?.doubleValue    = s.ramAlertThreshold
        ramThreshLabel?.stringValue     = "\(Int(s.ramAlertThreshold))%"
        tempThreshSlider?.doubleValue   = s.tempAlertThreshold
        tempThreshLabel?.stringValue    = "\(Int(s.tempAlertThreshold))°C"
        accentColorWell?.color          = ColorManager.shared.accentColor
        fontSlider?.doubleValue         = s.responseFontSize
        fontSizeLabel?.stringValue      = "\(Int(s.responseFontSize))pt"
        autoHideSwitch?.state           = s.autoHideResponse  ? .on : .off
        autoHideDelayStepper?.doubleValue = s.autoHideDelay
        autoHideDelayLabel?.stringValue = "\(Int(s.autoHideDelay))s"
    }
}

// MARK: - Notification names

extension Notification.Name {
    static let ariFontSizeChanged = Notification.Name("ari.fontSizeChanged")
    static let ariModelError      = Notification.Name("ari.modelError")
}

// MARK: - NSTableViewDataSource / Delegate

extension SettingsWindowController: NSTableViewDataSource, NSTableViewDelegate {

    func numberOfRows(in tableView: NSTableView) -> Int { items.count }

    func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
        let item = items[row]

        let cell = NSTableCellView()
        cell.identifier = .init("cell")

        let img = NSImageView()
        img.image       = NSImage(systemSymbolName: item.icon, accessibilityDescription: nil)
        img.contentTintColor = .secondaryLabelColor
        img.translatesAutoresizingMaskIntoConstraints = false
        img.widthAnchor.constraint(equalToConstant: 16).isActive = true
        img.heightAnchor.constraint(equalToConstant: 16).isActive = true

        let lbl = NSTextField(labelWithString: item.label)
        lbl.font = .systemFont(ofSize: 13)
        lbl.translatesAutoresizingMaskIntoConstraints = false

        let hStack = NSStackView(views: [img, lbl])
        hStack.spacing = 8
        hStack.translatesAutoresizingMaskIntoConstraints = false
        cell.addSubview(hStack)

        NSLayoutConstraint.activate([
            hStack.leadingAnchor.constraint(equalTo: cell.leadingAnchor, constant: 8),
            hStack.centerYAnchor.constraint(equalTo: cell.centerYAnchor),
        ])
        return cell
    }

    func tableViewSelectionDidChange(_ notification: Notification) {
        let idx = sidebar.selectedRow
        guard idx >= 0 else { return }
        selectItem(at: idx, animated: true)
    }
}
