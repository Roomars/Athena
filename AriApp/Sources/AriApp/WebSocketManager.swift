import Foundation
import Combine

enum OrbState: String {
    case idle, thinking, listening, speaking
}

enum ModelState {
    case loading, ready(String)
}

enum OrbEvent {
    case memorySave, contradiction, entityUpdate
}

final class WebSocketManager: ObservableObject {
    static let shared = WebSocketManager()

    @Published var orbState: OrbState = .idle
    @Published var streamingText: String = ""
    @Published var lastResponse: String = ""
    @Published var isConnected = false
    @Published var modelState: ModelState = .loading
    @Published var cpuLoad: Double = 0.0

    @Published var activeEvent: OrbEvent? = nil
    private(set) var prevOrbState: OrbState = .idle
    private(set) var stateChangedAt: Date = .now
    private(set) var eventStartedAt: Date? = nil
    private var eventTimer: Timer?

    // Callback AppKit puro
    var onTextChunk:             ((String) -> Void)?
    var onResponseDone:          ((String) -> Void)?
    var onSTTResult:             ((String) -> Void)?
    var onProactiveNotification: ((String, String) -> Void)?  // (title, body)
    /// facts = array di {key,value,tags,confidence,updated_at}
    /// relations = array di {from_key,to_key,rel_type}
    /// episodes = array di {summary,timestamp,message_count}
    /// graph    = {nodes:[String], edges:[{from,to,rel}]}
    var onMemoryDump: (([[String: Any]], [[String: Any]], [[String: Any]], [String: Any]) -> Void)?
    var onStatsUpdate:           (([String: Any]) -> Void)?
    var onCaptureScreen:         ((String) -> Void)?
    var onDiffProposal:          ((String) -> Void)?
    var onTTSDone:               (() -> Void)?

    private var task: URLSessionWebSocketTask?
    private var pingTimer: Timer?

    func connect() {
        // Cancella task precedente per evitare receive() multipli in parallelo
        pingTimer?.invalidate()
        task?.cancel(with: .goingAway, reason: nil)
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
                let newState = OrbState(rawValue: msg["state"] as? String ?? "idle") ?? .idle
                if newState != self.orbState {
                    self.prevOrbState   = self.orbState
                    self.stateChangedAt = Date()
                }
                self.orbState = newState

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
                AriNotchNotifier.shared.notifyModelReady(modelId)

            case "stt_result":
                let text = msg["text"] as? String ?? ""
                self.onSTTResult?(text)

            case "proactive_notification":
                let title = msg["title"] as? String ?? "Ari"
                let body  = msg["body"]  as? String ?? ""
                self.onProactiveNotification?(title, body)
                AriNotchNotifier.shared.notifyProactive(title: title, body: body)

            case "memory_cleared":
                self.lastResponse = ""
                self.streamingText = ""

            case "memory_dump_response":
                let facts     = msg["facts"]     as? [[String: Any]] ?? []
                let relations = msg["relations"] as? [[String: Any]] ?? []
                let episodes  = msg["episodes"]  as? [[String: Any]] ?? []
                let graph     = msg["graph"]     as? [String: Any]   ?? [:]
                self.onMemoryDump?(facts, relations, episodes, graph)

            case "stats_update":
                self.cpuLoad = (msg["cpu_pct"] as? Double ?? 0) / 100.0
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

            case "orb_event":
                let ev = msg["event"] as? String ?? ""
                switch ev {
                case "memory_save":   self.activeEvent = .memorySave
                case "contradiction": self.activeEvent = .contradiction
                case "entity_update": self.activeEvent = .entityUpdate
                default: break
                }
                self.eventStartedAt = Date()
                self.eventTimer?.invalidate()
                self.eventTimer = Timer.scheduledTimer(withTimeInterval: 2.5, repeats: false) { [weak self] _ in
                    DispatchQueue.main.async { self?.activeEvent = nil }
                }

            case "request_tool_approval":
                let actionType = msg["action_type"] as? String ?? "tool"
                let desc       = msg["description"] as? String ?? "Azione richiesta"
                ApprovalBanner.shared.show(description: desc, mode: .tool(type: actionType))

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
