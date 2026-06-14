import Foundation
import Combine

enum OrbState: String {
    case idle, thinking, listening, speaking
}

final class WebSocketManager: ObservableObject {
    static let shared = WebSocketManager()

    @Published var orbState: OrbState = .idle
    @Published var lastResponse: String = ""
    @Published var isConnected = false

    private var task: URLSessionWebSocketTask?
    private var pingTimer: Timer?

    func connect() {
        let url = URL(string: "ws://127.0.0.1:8765/ws")!
        task = URLSession.shared.webSocketTask(with: url)
        task?.resume()
        isConnected = true
        receive()
        startPing()
    }

    func disconnect() {
        pingTimer?.invalidate()
        task?.cancel(with: .normalClosure, reason: nil)
        isConnected = false
    }

    func send(content: String) {
        let msg: [String: Any] = ["type": "user_input", "content": content, "mode": "text"]
        guard let data = try? JSONSerialization.data(withJSONObject: msg),
              let str = String(data: data, encoding: .utf8) else { return }
        task?.send(.string(str)) { _ in }
    }

    func sendPrivacyMode(enabled: Bool) {
        let msg: [String: Any] = ["type": "privacy_mode", "enabled": enabled]
        guard let data = try? JSONSerialization.data(withJSONObject: msg),
              let str = String(data: data, encoding: .utf8) else { return }
        task?.send(.string(str)) { _ in }
    }

    private func receive() {
        task?.receive { [weak self] result in
            guard let self else { return }
            switch result {
            case .success(let message):
                if case .string(let text) = message {
                    self.handle(text)
                }
                self.receive()
            case .failure:
                DispatchQueue.main.async { self.isConnected = false }
                DispatchQueue.main.asyncAfter(deadline: .now() + 3) { self.connect() }
            }
        }
    }

    private func handle(_ text: String) {
        guard let data = text.data(using: .utf8),
              let msg = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let type = msg["type"] as? String else { return }

        DispatchQueue.main.async {
            switch type {
            case "orb_state":
                self.orbState = OrbState(rawValue: msg["state"] as? String ?? "idle") ?? .idle
            case "response_chunk":
                self.lastResponse = msg["content"] as? String ?? ""
            case "response_done":
                self.orbState = .idle
            default:
                break
            }
        }
    }

    private func startPing() {
        pingTimer = Timer.scheduledTimer(withTimeInterval: 10, repeats: true) { [weak self] _ in
            let ping = #"{"type":"ping"}"#
            self?.task?.send(.string(ping)) { _ in }
        }
    }
}
