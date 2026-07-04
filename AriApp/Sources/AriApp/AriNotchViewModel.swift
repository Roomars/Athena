import AppKit
import Combine

// MARK: - State types

enum NotchState: Equatable {
    case collapsed
    case expanded
    case sneakPeek   // auto-chiude dopo sneakPeekDuration
}

enum AriPhase: Equatable {
    case idle
    case listening
    case thinking
    case speaking
}

// MARK: - ViewModel

final class AriNotchViewModel: ObservableObject {
    static let shared = AriNotchViewModel()

    // Notch geometry (rilevata una volta sola)
    let notchWidth:    CGFloat
    let notchHeight:   CGFloat = 38

    // Espansione
    @Published var state:    NotchState = .collapsed
    @Published var phase:    AriPhase   = .idle
    @Published var response: String     = ""
    @Published var isHovered: Bool      = false

    // Dimensioni pannello espanso
    let expandedWidth:  CGFloat = 620
    let expandedHeight: CGFloat = 300

    private let sneakPeekDuration: TimeInterval = 4
    private var sneakPeekTask: DispatchWorkItem?
    private var hoverTimer: Timer?

    private init() {
        notchWidth = AriNotchViewModel.detectNotchWidth()
    }

    // MARK: - Geometry

    private static func detectNotchWidth() -> CGFloat {
        guard let screen = NSScreen.main else { return 160 }
        let left  = screen.auxiliaryTopLeftArea?.width  ?? 0
        let right = screen.auxiliaryTopRightArea?.width ?? 0
        let notch = screen.frame.width - left - right
        return notch > 0 ? notch : 160
    }

    var collapsedSize: CGSize { CGSize(width: notchWidth, height: notchHeight) }
    var expandedSize:  CGSize { CGSize(width: expandedWidth, height: expandedHeight) }
    var currentSize:   CGSize {
        switch state {
        case .collapsed:              return collapsedSize
        case .expanded, .sneakPeek:  return expandedSize
        }
    }

    // MARK: - Transitions

    func expand(permanent: Bool = true) {
        cancelSneakPeek()
        state = permanent ? .expanded : .sneakPeek
        if !permanent { scheduleSneakPeekHide() }
    }

    func collapse() {
        cancelSneakPeek()
        state = .collapsed
    }

    func toggle() {
        state == .collapsed ? expand() : collapse()
    }

    // MARK: - Response

    func setResponse(_ text: String) {
        response = text
        if state == .collapsed { expand(permanent: false) }
    }

    // MARK: - Phase

    func setPhase(_ p: AriPhase) {
        phase = p
        if p == .listening || p == .thinking {
            if state == .collapsed { expand(permanent: false) }
        }
    }

    // MARK: - Hover

    func onHover(_ inside: Bool) {
        isHovered = inside
        hoverTimer?.invalidate()
        if inside {
            hoverTimer = Timer.scheduledTimer(withTimeInterval: 0.3, repeats: false) { [weak self] _ in
                guard let self, self.isHovered else { return }
                self.expand(permanent: true)
            }
        } else {
            if state == .expanded {
                hoverTimer = Timer.scheduledTimer(withTimeInterval: 0.6, repeats: false) { [weak self] _ in
                    guard let self, !self.isHovered else { return }
                    self.collapse()
                }
            }
        }
    }

    // MARK: - SneakPeek

    private func scheduleSneakPeekHide() {
        cancelSneakPeek()
        let item = DispatchWorkItem { [weak self] in
            guard let self, self.state == .sneakPeek else { return }
            DispatchQueue.main.async { self.collapse() }
        }
        sneakPeekTask = item
        DispatchQueue.main.asyncAfter(deadline: .now() + sneakPeekDuration, execute: item)
    }

    private func cancelSneakPeek() {
        sneakPeekTask?.cancel()
        sneakPeekTask = nil
    }
}
