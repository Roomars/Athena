import SwiftUI

struct OrbView: View {
    var body: some View {
        TimelineView(.animation(minimumInterval: 0.05, paused: false)) { _ in
            let wm  = WebSocketManager.shared
            let lbl = label(wm: wm)
            VStack(spacing: 6) {
                CyberEyeView(state: wm.orbState, size: 200)
                if !lbl.isEmpty {
                    Text(lbl)
                        .font(.system(size: 10, weight: .medium, design: .monospaced))
                        .foregroundColor(.white.opacity(0.45))
                        .shadow(color: .black.opacity(0.9), radius: 3, x: 0, y: 1)
                }
            }
            .frame(width: 220, height: 220)
            .background(Color.clear)
        }
    }

    private func label(wm: WebSocketManager) -> String {
        guard wm.isConnected else { return "offline" }
        switch wm.modelState {
        case .loading: return "caricamento..."
        case .ready:
            switch wm.orbState {
            case .idle:      return ""           // nessuna etichetta a riposo
            case .thinking:  return "elaboro..."
            case .listening: return "ascolto..."
            case .speaking:  return "rispondo"
            }
        }
    }
}
