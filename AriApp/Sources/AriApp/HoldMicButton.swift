import AppKit

/// Bottone che si attiva al mouseDown e rilascia al mouseUp.
/// Durante il tracking il run loop continua a girare,
/// quindi i callback main-thread (onPartialResult) si aggiornano in tempo reale.
final class HoldMicButton: NSButton {
    var onPress:   (() -> Void)?
    var onRelease: (() -> Void)?

    override func mouseDown(with event: NSEvent) {
        onPress?()
        // nextEvent blocca fino a mouseUp ma lascia girare il run loop
        while let e = window?.nextEvent(matching: [.leftMouseUp, .leftMouseDragged]) {
            if e.type == .leftMouseUp { break }
        }
        onRelease?()
    }
}
