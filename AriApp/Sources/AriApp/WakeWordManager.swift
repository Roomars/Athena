import Foundation
import Speech
import AVFoundation

final class WakeWordManager: NSObject {
    static let shared = WakeWordManager()

    private let recognizer:    SFSpeechRecognizer?
    private var audioEngine    = AVAudioEngine()
    private var task:          SFSpeechRecognitionTask?
    private var request:       SFSpeechAudioBufferRecognitionRequest?
    private var restartTimer:  Timer?
    private var isRestarting   = false   // previene restart concorrenti
    private(set) var isActive  = false

    var onWakeDetected: (() -> Void)?

    private let triggers = ["ari", "hey ari", "ehi ari", "ciao ari", "ok ari"]

    private override init() {
        recognizer = SFSpeechRecognizer(locale: Locale(identifier: "it-IT"))
        super.init()
    }

    // MARK: - Pubblico

    func start() {
        guard !isActive else { return }
        isActive     = true
        isRestarting = false
        beginSession()
    }

    func stop() {
        isActive     = false
        isRestarting = false
        endSession()
    }

    // MARK: - Sessione

    private func beginSession() {
        guard isActive, !isRestarting else { return }
        guard let rec = recognizer, rec.isAvailable else {
            scheduleRestart(after: 10)
            return
        }

        audioEngine = AVAudioEngine()
        let req = SFSpeechAudioBufferRecognitionRequest()
        req.shouldReportPartialResults = true
        request = req

        let inputNode = audioEngine.inputNode
        let fmt = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: fmt) { [weak self] buf, _ in
            self?.request?.append(buf)
        }

        task = rec.recognitionTask(with: req) { [weak self] result, error in
            guard let self else { return }
            if let text = result?.bestTranscription.formattedString {
                self.checkForWakeWord(in: text)
            }
            // Riavvia SOLO su completamento naturale (isFinal senza errore grave)
            // Gli errori CoreAudio (-10877) li ignoriamo — il timer da 45s gestisce il ciclo
            if result?.isFinal == true, error == nil {
                DispatchQueue.main.async { [weak self] in
                    if self?.isActive == true { self?.scheduleRestart(after: 5) }
                }
            }
        }

        do {
            audioEngine.prepare()
            try audioEngine.start()
        } catch {
            // Avvio fallito — riprova tra 10s (non 0.3s come prima)
            scheduleRestart(after: 10)
            return
        }

        // Restart preventivo prima del timeout Apple (~60s)
        restartTimer = Timer.scheduledTimer(withTimeInterval: 50, repeats: false) { [weak self] _ in
            self?.scheduleRestart(after: 0.5)
        }
    }

    private func endSession() {
        restartTimer?.invalidate()
        restartTimer = nil
        task?.cancel()
        task    = nil
        request = nil
        guard audioEngine.isRunning else { return }
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
    }

    private func scheduleRestart(after delay: TimeInterval) {
        guard !isRestarting, isActive else { return }
        isRestarting = true
        DispatchQueue.main.asyncAfter(deadline: .now() + delay) { [weak self] in
            guard let self, self.isActive else { return }
            self.isRestarting = false
            self.endSession()
            self.beginSession()
        }
    }

    // MARK: - Rilevazione

    private func checkForWakeWord(in text: String) {
        let lower = text.lowercased()
        for trigger in triggers where lower.contains(trigger) {
            endSession()
            isActive = false
            DispatchQueue.main.async { self.onWakeDetected?() }
            return
        }
    }
}
