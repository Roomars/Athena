import Cocoa

final class HotkeyManager {
    static let shared = HotkeyManager()
    var onActivate: (() -> Void)?   // premuto: attiva/disattiva voce

    private var eventTap: CFMachPort?

    // Legge keyCode e modifiers dalle Settings al momento del confronto
    var keyCode:   Int64   { Int64(SettingsManager.shared.settings.hotkeyKeyCode) }
    var modifiers: CGEventFlags { CGEventFlags(rawValue: SettingsManager.shared.settings.hotkeyModifiers) }

    func start() {
        let mask = CGEventMask(1 << CGEventType.keyDown.rawValue)
        eventTap = CGEvent.tapCreate(
            tap:              .cgSessionEventTap,
            place:            .headInsertEventTap,
            options:          .defaultTap,
            eventsOfInterest: mask,
            callback: { _, _, event, refcon in
                Unmanaged<HotkeyManager>.fromOpaque(refcon!).takeUnretainedValue().handle(event)
            },
            userInfo: Unmanaged.passUnretained(self).toOpaque()
        )
        guard let tap = eventTap else {
            print("[HotkeyManager] nessun CGEvent tap — verifica Accessibilità")
            return
        }
        let src = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), src, .commonModes)
        CGEvent.tapEnable(tap: tap, enable: true)
    }

    func updateFromSettings() {
        // Nessuna azione necessaria — handle() legge sempre i valori aggiornati
    }

    private func handle(_ event: CGEvent) -> Unmanaged<CGEvent>? {
        let code  = event.getIntegerValueField(.keyboardEventKeycode)
        let flags = event.flags.intersection([.maskCommand, .maskShift, .maskAlternate, .maskControl])
        let target = modifiers.intersection([.maskCommand, .maskShift, .maskAlternate, .maskControl])
        if code == keyCode && flags == target {
            DispatchQueue.main.async { self.onActivate?() }
            return nil
        }
        return Unmanaged.passUnretained(event)
    }

    /// Formatta keyCode + modifiers come stringa leggibile (es. "⌘⇧A")
    static func formatHotkey(keyCode: Int, modifiers: UInt64) -> String {
        var s = ""
        let m = CGEventFlags(rawValue: modifiers)
        if m.contains(.maskControl)   { s += "⌃" }
        if m.contains(.maskAlternate) { s += "⌥" }
        if m.contains(.maskShift)     { s += "⇧" }
        if m.contains(.maskCommand)   { s += "⌘" }
        s += keyLabel(for: keyCode)
        return s
    }

    static func keyLabel(for code: Int) -> String {
        let map: [Int: String] = [
            36:"↩", 48:"⇥", 49:"Space", 51:"⌫", 53:"Esc",
            123:"←", 124:"→", 125:"↓", 126:"↑",
            0:"A",1:"S",2:"D",3:"F",4:"H",5:"G",6:"Z",7:"X",
            8:"C",9:"V",11:"B",12:"Q",13:"W",14:"E",15:"R",
            16:"Y",17:"T",31:"O",32:"U",34:"I",35:"P",
            37:"L",38:"J",40:"K",45:"N",46:"M",
        ]
        return map[code] ?? "?"
    }
}
