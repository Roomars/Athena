import SwiftUI

struct OrbView: View {
    @ObservedObject private var wm = WebSocketManager.shared

    var body: some View {
        let lbl = stateLabel(wm: wm)

        GeometryReader { geo in
            let sz = min(geo.size.width, geo.size.height)
            ZStack {
                Color.clear
                CyberEyeView(
                    state:          wm.orbState,
                    prevState:      wm.prevOrbState,
                    transitionStart: wm.stateChangedAt,
                    workload:       wm.cpuLoad,
                    size:           sz,
                    activeEvent:    wm.activeEvent,
                    eventStart:     wm.eventStartedAt
                )
                    .frame(width: sz, height: sz)

                if !lbl.isEmpty {
                    Text(lbl.uppercased())
                        .font(.system(size: max(7, sz * 0.04), weight: .bold, design: .monospaced))
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
                        .offset(y: sz * 0.29)
                }
            }
            .frame(width: sz, height: sz)
            .position(x: geo.size.width / 2, y: geo.size.height / 2)
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
