import Cocoa

// CGEvent tap — hotkey globale OS-level (funziona anche su lock screen).
// Pattern da arinltte/LUCE.
final class HotkeyManager {
    static let shared = HotkeyManager()
    var onToggle: (() -> Void)?

    private var eventTap: CFMachPort?

    func start() {
        let mask = CGEventMask(1 << CGEventType.keyDown.rawValue)
        eventTap = CGEvent.tapCreate(
            tap: .cgSessionEventTap,
            place: .headInsertEventTap,
            options: .defaultTap,
            eventsOfInterest: mask,
            callback: { _, _, event, refcon in
                let mgr = Unmanaged<HotkeyManager>.fromOpaque(refcon!).takeUnretainedValue()
                return mgr.handleEvent(event)
            },
            userInfo: Unmanaged.passUnretained(self).toOpaque()
        )

        guard let tap = eventTap else {
            print("[HotkeyManager] impossibile creare CGEvent tap — verifica permesso Accessibilità")
            return
        }

        let source = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), source, .commonModes)
        CGEvent.tapEnable(tap: tap, enable: true)
    }

    private func handleEvent(_ event: CGEvent) -> Unmanaged<CGEvent>? {
        // Cmd+Shift+A = keyCode 0 con flags .maskCommand | .maskShift
        let keyCode = event.getIntegerValueField(.keyboardEventKeycode)
        let flags = event.flags
        let isTarget = keyCode == 0
            && flags.contains(.maskCommand)
            && flags.contains(.maskShift)
            && !flags.contains(.maskAlternate)
            && !flags.contains(.maskControl)

        if isTarget {
            DispatchQueue.main.async { self.onToggle?() }
            return nil // consuma l'evento
        }
        return Unmanaged.passUnretained(event)
    }
}
