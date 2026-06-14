import SwiftUI

// FASE 1: orb placeholder — cerchio statico con colore per stato.
// FASE 2: sostituito con Metal shader animato.
struct OrbView: View {
    @ObservedObject var ws = WebSocketManager.shared
    @State private var inputText = ""
    @FocusState private var inputFocused: Bool

    var body: some View {
        VStack(spacing: 12) {
            // Orb
            Circle()
                .fill(orbColor)
                .frame(width: 48, height: 48)
                .shadow(color: orbColor.opacity(0.6), radius: 8)
                .animation(.easeInOut(duration: 0.3), value: ws.orbState)

            // Stato
            Text(stateLabel)
                .font(.system(size: 11, weight: .medium, design: .monospaced))
                .foregroundColor(.secondary)

            // Ultima risposta
            if !ws.lastResponse.isEmpty {
                Text(ws.lastResponse)
                    .font(.system(size: 13))
                    .foregroundColor(.primary)
                    .multilineTextAlignment(.center)
                    .lineLimit(4)
                    .padding(.horizontal, 8)
            }

            // Input
            HStack(spacing: 6) {
                TextField("Scrivi ad Ari...", text: $inputText)
                    .textFieldStyle(.plain)
                    .font(.system(size: 13))
                    .focused($inputFocused)
                    .onSubmit { send() }

                Button(action: send) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 18))
                        .foregroundColor(.accentColor)
                }
                .buttonStyle(.plain)
                .disabled(inputText.trimmingCharacters(in: .whitespaces).isEmpty)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(Color(nsColor: .controlBackgroundColor))
            .cornerRadius(8)
        }
        .padding(16)
        .frame(width: 260)
        .onAppear { inputFocused = true }
    }

    private var orbColor: Color {
        switch ws.orbState {
        case .idle:      return .blue
        case .thinking:  return .orange
        case .listening: return .green
        case .speaking:  return .purple
        }
    }

    private var stateLabel: String {
        switch ws.orbState {
        case .idle:      return ws.isConnected ? "in ascolto" : "disconnessa"
        case .thinking:  return "elaboro..."
        case .listening: return "ascolto..."
        case .speaking:  return "rispondo"
        }
    }

    private func send() {
        let text = inputText.trimmingCharacters(in: .whitespaces)
        guard !text.isEmpty else { return }
        ws.send(content: text)
        inputText = ""
        // Ripristina focus dopo l'invio
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) {
            inputFocused = true
        }
    }
}
