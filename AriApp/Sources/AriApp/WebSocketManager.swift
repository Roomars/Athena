import Foundation
import Combine

enum OrbState: String {
    case idle, thinking, listening, speaking
}

enum ModelState {
    case loading, ready(String)
}

final class WebSocketManager: ObservableObject {
    static let shared = WebSocketManager()

    @Published var orbState: OrbState = .idle
    @Published var streamingText: String = ""
    @Published var lastResponse: String = ""
    @Published var isConnected = false
    @Published var modelState: ModelState = .loading

    // Callback AppKit puro
    var onTextChunk:             ((String) -> Void)?
    var onResponseDone:          ((String) -> Void)?
    var onSTTResult:             ((String) -> Void)?
    var onProactiveNotification: ((String, String) -> Void)?  // (title, body)
    var onMemoryDump:            (([String: String], [[String: Any]]) -> Void)?
    var onStatsUpdate:           (([String: Any]) -> Void)?
    var onCaptureScreen:         ((String) -> Void)?
    var onDiffProposal:          ((String) -> Void)?
    var onTTSDone:               (() -> Void)?

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
        sendJSON(msg)
    }

    func sendVoiceStart() { sendJSON(["type": "voice_start"]) }
    func sendVoiceStop()  { sendJSON(["type": "voice_stop"])  }
    func sendTTSStop()    { sendJSON(["type": "tts_stop"])    }
    func setTTSEnabled(_ on: Bool) { sendJSON(["type": "tts_enabled", "enabled": on]) }

    func sendPrivacyMode(enabled: Bool) {
        sendJSON(["type": "privacy_mode", "enabled": enabled])
    }

    func clearMemory() {
        sendJSON(["type": "clear_memory"])
    }

    func requestMemoryDump() {
        sendJSON(["type": "memory_dump"])
    }

    func sendVisionRequest(image: String, prompt: String) {
        sendJSON(["type": "vision_request", "image": image, "prompt": prompt])
    }

    // MARK: - Private

    func sendJSON(_ payload: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: payload),
              let str = String(data: data, encoding: .utf8) else { return }
        task?.send(.string(str)) { _ in }
    }

    private func receive() {
        task?.receive { [weak self] result in
            guard let self else { return }
            switch result {
            case .success(let message):
                if case .string(let text) = message { self.handle(text) }
                self.receive()
            case .failure:
                DispatchQueue.main.async {
                    self.isConnected = false
                    self.orbState = .idle
                }
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
                let token = msg["content"] as? String ?? ""
                self.streamingText += token
                self.onTextChunk?(self.streamingText)

            case "response_done":
                self.lastResponse = self.streamingText
                self.streamingText = ""
                self.orbState = .idle
                self.onResponseDone?(self.lastResponse)

            case "model_loading":
                self.modelState = .loading

            case "model_ready":
                let modelId = msg["model"] as? String ?? "mlx"
                self.modelState = .ready(modelId)

            case "stt_result":
                let text = msg["text"] as? String ?? ""
                self.onSTTResult?(text)

            case "proactive_notification":
                let title = msg["title"] as? String ?? "Ari"
                let body  = msg["body"]  as? String ?? ""
                self.onProactiveNotification?(title, body)

            case "memory_cleared":
                self.lastResponse = ""
                self.streamingText = ""

            case "memory_dump_response":
                let facts    = msg["facts"]    as? [String: String]  ?? [:]
                let episodes = msg["episodes"] as? [[String: Any]]   ?? []
                self.onMemoryDump?(facts, episodes)

            case "stats_update":
                self.onStatsUpdate?(msg)

            case "capture_screen":
                let prompt = msg["prompt"] as? String ?? "Descrivi cosa vedi in questo screenshot."
                self.onCaptureScreen?(prompt)

            case "diff_proposal":
                let desc = msg["description"] as? String ?? "Modifica proposta"
                self.onDiffProposal?(desc)

            case "rebuild_app":
                // Python ha scritto i file Swift — compila e riavvia
                self.handleRebuild()

            case "modification_applied":
                break

            case "tts_done":
                self.onTTSDone?()

            default:
                break
            }
        }
    }

    private func handleRebuild() {
        sendJSON(["type": "build_started"])
        BuildManager.shared.build(
            onProgress: { chunk in
                self.sendJSON(["type": "build_log", "content": chunk])
            },
            completion: { success, output in
                if success {
                    self.sendJSON(["type": "build_success"])
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                        BuildManager.shared.restart()
                    }
                } else {
                    self.sendJSON(["type": "build_failed", "error": output])
                }
            }
        )
    }

    private func startPing() {
        pingTimer = Timer.scheduledTimer(withTimeInterval: 10, repeats: true) { [weak self] _ in
            self?.task?.send(.string(#"{"type":"ping"}"#)) { _ in }
        }
    }
}
