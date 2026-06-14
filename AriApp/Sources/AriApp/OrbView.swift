import SwiftUI

struct OrbView: View {
    @ObservedObject var ws = WebSocketManager.shared
    @State private var inputText = ""
    @FocusState private var inputFocused: Bool
    @State private var pulseScale: CGFloat = 1.0
    @State private var rippleScale: CGFloat = 1.0
    @State private var rippleOpacity: Double = 0.6

    var body: some View {
        VStack(spacing: 12) {
            orbSection
            statusLabel
            responseSection
            inputSection
        }
        .padding(16)
        .frame(width: 280)
        .onAppear {
            inputFocused = true
            startIdleAnimation()
        }
        .onChange(of: ws.orbState) { _ in
            startIdleAnimation()
        }
    }

    // MARK: - Orb

    private var orbSection: some View {
        ZStack {
            // Anelli ripple — visibili solo in speaking
            if ws.orbState == .speaking {
                ForEach(0..<3, id: \.self) { i in
                    Circle()
                        .stroke(orbColor.opacity(max(0, rippleOpacity - Double(i) * 0.18)), lineWidth: 1.5)
                        .frame(width: 48 + CGFloat(i) * 18, height: 48 + CGFloat(i) * 18)
                        .scaleEffect(rippleScale)
                }
            }
            // Orb principale
            Circle()
                .fill(orbGradient)
                .frame(width: 48, height: 48)
                .scaleEffect(pulseScale)
                .shadow(color: orbColor.opacity(0.5), radius: 10)
        }
        .frame(width: 96, height: 96)
        .animation(.easeInOut(duration: 0.35), value: ws.orbState)
    }

    // MARK: - Labels

    private var statusLabel: some View {
        Group {
            switch ws.modelState {
            case .loading:
                Text("caricamento modello...")
                    .foregroundColor(.orange)
            case .ready:
                Text(stateLabel)
                    .foregroundColor(.secondary)
            }
        }
        .font(.system(size: 11, weight: .medium, design: .monospaced))
    }

    // MARK: - Response

    @ViewBuilder
    private var responseSection: some View {
        let display = ws.streamingText.isEmpty ? ws.lastResponse : ws.streamingText
        if !display.isEmpty {
            ScrollView {
                Text(display)
                    .font(.system(size: 13))
                    .foregroundColor(.primary)
                    .multilineTextAlignment(.leading)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .frame(maxHeight: 160)
            .padding(.horizontal, 4)
        }
    }

    // MARK: - Input

    private var inputSection: some View {
        HStack(spacing: 6) {
            TextField("Scrivi ad Ari...", text: $inputText)
                .textFieldStyle(.plain)
                .font(.system(size: 13))
                .focused($inputFocused)
                .onSubmit { send() }

            Button(action: send) {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.system(size: 20))
                    .foregroundColor(inputText.trimmingCharacters(in: .whitespaces).isEmpty ? .secondary : .accentColor)
            }
            .buttonStyle(.plain)
            .disabled(inputText.trimmingCharacters(in: .whitespaces).isEmpty)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 7)
        .background(Color(nsColor: .controlBackgroundColor))
        .cornerRadius(8)
    }

    // MARK: - Colori e animazioni

    private var orbColor: Color {
        switch ws.orbState {
        case .idle:      return .blue
        case .thinking:  return .orange
        case .listening: return .green
        case .speaking:  return .purple
        }
    }

    private var orbGradient: RadialGradient {
        RadialGradient(
            colors: [orbColor.opacity(0.9), orbColor.opacity(0.6)],
            center: .topLeading,
            startRadius: 4,
            endRadius: 28
        )
    }

    private var stateLabel: String {
        guard ws.isConnected else { return "disconnessa" }
        switch ws.orbState {
        case .idle:      return "in ascolto"
        case .thinking:  return "elaboro..."
        case .listening: return "ascolto..."
        case .speaking:  return "rispondo"
        }
    }

    private func startIdleAnimation() {
        switch ws.orbState {
        case .idle:
            withAnimation(.easeInOut(duration: 2.2).repeatForever(autoreverses: true)) {
                pulseScale = 1.04
            }
        case .thinking:
            withAnimation(.easeInOut(duration: 0.45).repeatForever(autoreverses: true)) {
                pulseScale = 1.08
            }
        case .speaking:
            pulseScale = 1.0
            withAnimation(.easeOut(duration: 1.4).repeatForever(autoreverses: false)) {
                rippleScale = 1.35
                rippleOpacity = 0.0
            }
        case .listening:
            withAnimation(.easeInOut(duration: 0.6).repeatForever(autoreverses: true)) {
                pulseScale = 1.1
            }
        }
    }

    // MARK: - Actions

    private func send() {
        let text = inputText.trimmingCharacters(in: .whitespaces)
        guard !text.isEmpty else { return }
        ws.send(content: text)
        inputText = ""
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) {
            inputFocused = true
        }
    }
}
