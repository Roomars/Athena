import AppKit
import SwiftUI
import Combine

// NSPanel ancorata al notch — level .mainMenu + 3 (sopra Spotlight e screen lock)
final class NotchPanel: NSPanel {

    private let vm = AriNotchViewModel.shared
    private var cancellables = Set<AnyCancellable>()

    override var canBecomeKey:  Bool { false }
    override var canBecomeMain: Bool { false }

    // MARK: - Factory

    static func make() -> NotchPanel {
        guard let screen = NSScreen.main else { fatalError("no main screen") }

        let vm = AriNotchViewModel.shared

        let initW = vm.notchWidth
        let initH = vm.notchHeight
        let initX = screen.frame.midX - initW / 2
        let initY = screen.frame.maxY - initH

        let panel = NotchPanel(
            contentRect: NSRect(x: initX, y: initY, width: initW, height: initH),
            styleMask:   [.borderless, .nonactivatingPanel],
            backing:     .buffered,
            defer:       false
        )

        panel.level              = NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.mainMenuWindow)) + 3)
        panel.isFloatingPanel    = true
        panel.isOpaque           = false
        panel.backgroundColor    = .clear
        panel.hasShadow          = false
        panel.isMovable          = false
        panel.hidesOnDeactivate  = false
        panel.animationBehavior  = .none
        panel.collectionBehavior = [.canJoinAllSpaces, .stationary, .ignoresCycle, .fullScreenAuxiliary]

        let hosting = NSHostingView(rootView: NotchView().environmentObject(vm))
        hosting.frame = NSRect(x: 0, y: 0, width: initW, height: initH)
        hosting.autoresizingMask = [.width, .height]
        panel.contentView = hosting

        // Ridimensiona il panel ogni volta che lo stato del notch cambia
        vm.$state
            .receive(on: DispatchQueue.main)
            .sink { [weak panel] _ in
                panel?.resizeTo(vm.currentSize, animated: true)
            }
            .store(in: &panel.cancellables)

        panel.orderFrontRegardless()
        return panel
    }

    // MARK: - Resize on state change

    func resizeTo(_ size: CGSize, animated: Bool = true) {
        guard let screen = NSScreen.main else { return }
        let x = screen.frame.midX - size.width  / 2
        let y = screen.frame.maxY - size.height
        let target = NSRect(x: x, y: y, width: size.width, height: size.height)

        if animated {
            NSAnimationContext.runAnimationGroup { ctx in
                ctx.duration       = 0.22
                ctx.timingFunction = CAMediaTimingFunction(name: .easeOut)
                self.animator().setFrame(target, display: true)
            }
        } else {
            setFrame(target, display: true)
        }
    }
}
