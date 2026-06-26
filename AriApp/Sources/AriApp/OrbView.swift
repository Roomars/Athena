import SwiftUI

struct OrbView: View {
    var body: some View {
        TimelineView(.animation(minimumInterval: 0.05, paused: false)) { _ in
            let wm  = WebSocketManager.shared
            let lbl = stateLabel(wm: wm)
            ZStack {
                Color.clear  // nessun sfondo — solo la sfera è visibile
                CyberEyeView(state: wm.orbState, workload: wm.cpuLoad, size: 208)

                // Badge stato — posizionato nella metà bassa dell'iride
                if !lbl.isEmpty {
                    Text(lbl.uppercased())
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundColor(badgeColor(wm.orbState).opacity(0.90))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(
                            RoundedRectangle(cornerRadius: 3)
                                .fill(Color.black.opacity(0.55))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 3)
                                        .strokeBorder(badgeColor(wm.orbState).opacity(0.40), lineWidth: 0.5)
                                )
                        )
                        .shadow(color: badgeColor(wm.orbState).opacity(0.6), radius: 4)
                        .offset(y: 66)
                }
            }
            .frame(width: 224, height: 224)
        }
    }

    private func stateLabel(wm: WebSocketManager) -> String {
        guard wm.isConnected else { return "offline" }
        switch wm.modelState {
        case .loading: return "boot"
        case .ready:
            switch wm.orbState {
            case .idle:      return ""
            case .thinking:  return "elaboro"
            case .listening: return "ascolto"
            case .speaking:  return "rispondo"
            }
        }
    }

    private func badgeColor(_ state: OrbState) -> Color {
        switch state {
        case .idle:      return Color(red: 0.0, green: 0.85, blue: 1.0)
        case .thinking:  return Color(red: 1.0, green: 0.60, blue: 0.1)
        case .listening: return Color(red: 0.2, green: 1.0,  blue: 0.4)
        case .speaking:  return Color(red: 0.6, green: 0.2,  blue: 1.0)
        }
    }
}
