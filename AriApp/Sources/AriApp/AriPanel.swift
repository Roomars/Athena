import AppKit

final class AriPanel: NSPanel {
    override var canBecomeKey: Bool  { true }
    override var canBecomeMain: Bool { true }
    var onRightClick: ((NSEvent) -> Void)?

    override func rightMouseDown(with event: NSEvent) {
        onRightClick?(event)
    }
}
