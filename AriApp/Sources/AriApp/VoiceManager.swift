import Foundation
import AVFoundation

// VoiceManager — gestisce solo UI e segnali WebSocket.
// La trascrizione è delegata a Python (mlx-whisper) via voice_start / voice_stop.
// WakeWordManager e ClapWakeManager mantengono il proprio AVAudioEngine indipendente.

final class VoiceManager: NSObject {
    static let shared = VoiceManager()

    private(set) var isRecording = false

    // Callback — onPartialResult non più usata (Whisper non ha partial),
    // mantenuta per non rompere eventuali call site esterni.
    var onPartialResult: ((String) -> Void)?
    var onFinalResult:   ((String) -> Void)?   // legacy — ora usa wm.onSTTResult
    var onError:         ((String) -> Void)?

    private override init() { super.init() }

    // MARK: - Permessi microfono (richiesto da macOS per sounddevice in Python)

    func requestPermissions() {
        AVCaptureDevice.requestAccess(for: .audio) { granted in
            if !granted {
                DispatchQueue.main.async {
                    self.onError?("Accesso al microfono negato — necessario per il riconoscimento vocale.")
                }
            }
        }
    }

    // MARK: - Registrazione

    /// useVAD=true → Python ferma automaticamente dopo il silenzio (wake word).
    /// useVAD=false → stop esplicito via stopRecording() (hold-to-talk).
    func startRecording(useVAD: Bool = false) {
        guard !isRecording else { return }
        isRecording = true
        WebSocketManager.shared.sendJSON(["type": "voice_start", "vad": useVAD])
    }

    func stopRecording() {
        guard isRecording else { return }
        isRecording = false
        WebSocketManager.shared.sendJSON(["type": "voice_stop"])
    }

    // MARK: - Chiamato quando Python restituisce il testo trascritto

    func handleSTTResult(_ text: String) {
        isRecording = false
        onFinalResult?(text)   // compatibilità legacy
    }
}
