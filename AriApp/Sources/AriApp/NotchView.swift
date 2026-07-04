import SwiftUI

// Root view montata dentro NotchPanel.
// Usa matchedGeometryEffect per morphing CyberEye small→full tra collapsed e expanded.
struct NotchView: View {
    @EnvironmentObject var vm: AriNotchViewModel
    @Namespace private var ns

    var body: some View {
        ZStack(alignment: .top) {
            // Sfondo notch — nero puro per fondersi col notch fisico
            RoundedRectangle(cornerRadius: vm.state == .collapsed ? 0 : 18, style: .continuous)
                .fill(Color.black)
                .animation(.spring(response: 0.38, dampingFraction: 0.8), value: vm.state)

            if vm.state == .collapsed {
                collapsedContent
                    .transition(.opacity.combined(with: .scale(scale: 0.9, anchor: .top)))
            } else {
                expandedContent
                    .transition(.opacity.combined(with: .scale(scale: 0.95, anchor: .top)))
            }
        }
        .frame(
            width:  vm.currentSize.width,
            height: vm.currentSize.height
        )
        .onHover { vm.onHover($0) }
        .onTapGesture   { vm.toggle() }
        .animation(.spring(response: 0.38, dampingFraction: 0.8), value: vm.state)
    }

    // MARK: - Collapsed

    private var collapsedContent: some View {
        HStack(spacing: 8) {
            // Mini orb — usa matchedGeometryEffect per il morphing
            MiniOrbView(phase: vm.phase)
                .matchedGeometryEffect(id: "orb", in: ns)
                .frame(width: 28, height: 28)

            // Dot di stato — colore cambia con la fase
            Circle()
                .fill(phaseColor)
                .frame(width: 6, height: 6)
                .animation(.easeInOut(duration: 0.3), value: vm.phase)
        }
        .frame(height: vm.notchHeight)
    }

    // MARK: - Expanded

    private var expandedContent: some View {
        VStack(spacing: 0) {
            // Top bar — orb + label stato
            HStack(spacing: 12) {
                MiniOrbView(phase: vm.phase)
                    .matchedGeometryEffect(id: "orb", in: ns)
                    .frame(width: 52, height: 52)

                VStack(alignment: .leading, spacing: 2) {
                    Text("Ari")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.white)
                    Text(phaseLabel)
                        .font(.system(size: 11))
                        .foregroundColor(phaseColor)
                        .animation(.easeInOut(duration: 0.25), value: vm.phase)
                }

                Spacer()

                // Bottone chiudi
                Button(action: { vm.collapse() }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.white.opacity(0.35))
                        .font(.system(size: 16))
                }
                .buttonStyle(.plain)
                .padding(.trailing, 8)
            }
            .padding(.horizontal, 16)
            .padding(.top, 14)
            .frame(height: 76)

            Divider()
                .background(Color.white.opacity(0.1))

            // Response text — streaming
            ScrollViewReader { proxy in
                ScrollView(.vertical, showsIndicators: false) {
                    Text(vm.response.isEmpty ? "In ascolto…" : vm.response)
                        .font(.system(size: 13))
                        .foregroundColor(vm.response.isEmpty
                            ? .white.opacity(0.3)
                            : .white.opacity(0.92))
                        .multilineTextAlignment(.leading)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .id("bottom")
                }
                .onChange(of: vm.response) { _ in
                    withAnimation { proxy.scrollTo("bottom", anchor: .bottom) }
                }
            }
            .frame(maxHeight: .infinity)

            Divider()
                .background(Color.white.opacity(0.1))

            // Input rapido inline
            NotchInputBar()
                .frame(height: 44)
        }
        .frame(width: vm.expandedWidth, height: vm.expandedHeight)
    }

    // MARK: - Helpers

    private var phaseColor: Color {
        switch vm.phase {
        case .idle:      return Color(red: 0, green: 0.85, blue: 1)   // ciano
        case .listening: return Color(red: 1, green: 0.25, blue: 0.25) // rosso
        case .thinking:  return Color(red: 1, green: 0.75, blue: 0)    // giallo
        case .speaking:  return .white
        }
    }

    private var phaseLabel: String {
        switch vm.phase {
        case .idle:      return "In attesa"
        case .listening: return "Ascolto…"
        case .thinking:  return "Penso…"
        case .speaking:  return "Parlo"
        }
    }
}

// MARK: - MiniOrbView

// Versione compatta di CyberEyeView per il notch.
// Usa cerchi animati su un canvas SwiftUI — nessuna dipendenza da OrbView full.
struct MiniOrbView: View {
    let phase: AriPhase
    @State private var pulse: Bool = false

    var body: some View {
        ZStack {
            Circle()
                .fill(Color.black)

            // Anello esterno pulsante
            Circle()
                .stroke(ringColor.opacity(0.5), lineWidth: 1.5)
                .scaleEffect(pulse ? 1.15 : 1.0)
                .animation(
                    .easeInOut(duration: 1.2).repeatForever(autoreverses: true),
                    value: pulse
                )

            // Pupilla
            Circle()
                .fill(ringColor.opacity(0.85))
                .frame(width: 10, height: 10)
                .blur(radius: 1)
        }
        .onAppear { pulse = true }
        .onChange(of: phase) { _ in pulse = false; pulse = true }
    }

    private var ringColor: Color {
        switch phase {
        case .idle:      return Color(red: 0, green: 0.85, blue: 1)
        case .listening: return Color(red: 1, green: 0.25, blue: 0.25)
        case .thinking:  return Color(red: 1, green: 0.75, blue: 0)
        case .speaking:  return .white
        }
    }
}

// MARK: - NotchInputBar

struct NotchInputBar: View {
    @State private var text: String = ""

    var body: some View {
        HStack(spacing: 8) {
            TextField("Scrivi ad Ari…", text: $text)
                .textFieldStyle(.plain)
                .foregroundColor(.white)
                .font(.system(size: 13))
                .onSubmit { send() }

            Button(action: send) {
                Image(systemName: "arrow.up.circle.fill")
                    .foregroundColor(Color(red: 0, green: 0.85, blue: 1))
                    .font(.system(size: 18))
            }
            .buttonStyle(.plain)
            .disabled(text.trimmingCharacters(in: .whitespaces).isEmpty)
        }
        .padding(.horizontal, 16)
    }

    private func send() {
        let trimmed = text.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        text = ""
        WebSocketManager.shared.send(content: trimmed)
    }
}
