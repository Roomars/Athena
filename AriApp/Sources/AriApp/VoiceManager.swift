import Foundation
import Speech
import AVFoundation

final class VoiceManager: NSObject {
    static let shared = VoiceManager()

    private let recognizer:       SFSpeechRecognizer?
    private var audioEngine       = AVAudioEngine()
    private var recognitionTask:  SFSpeechRecognitionTask?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private(set) var isRecording  = false

    // VAD — silence detection per modalità wake word
    private var vadEnabled  = false
    private var silenceTimer: Timer?
    private let silenceTimeout: TimeInterval = 3.0   // secondi di silenzio prima dello stop

    var onPartialResult: ((String) -> Void)?
    var onFinalResult:   ((String) -> Void)?
    var onError:         ((String) -> Void)?

    private override init() {
        recognizer = SFSpeechRecognizer(locale: Locale(identifier: "it-IT"))
        super.init()
    }

    func requestPermissions() {
        SFSpeechRecognizer.requestAuthorization { _ in }
        AVCaptureDevice.requestAccess(for: .audio) { _ in }
    }

    /// useVAD=true → stop automatico dopo `silenceTimeout` secondi senza parole (modalità wake word)
    func startRecording(useVAD: Bool = false) {
        guard !isRecording else { return }
        guard let rec = recognizer, rec.isAvailable else {
            DispatchQueue.main.async { self.onError?("Riconoscimento vocale non disponibile") }
            return
        }
        cleanup()
        isRecording = true
        vadEnabled  = useVAD
        audioEngine = AVAudioEngine()

        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        recognitionRequest = request

        let inputNode = audioEngine.inputNode
        let fmt = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: fmt) { [weak self] buf, _ in
            self?.recognitionRequest?.append(buf)
        }

        recognitionTask = rec.recognitionTask(with: request) { [weak self] result, error in
            guard let self else { return }
            if let result = result {
                let text = result.bestTranscription.formattedString
                DispatchQueue.main.async {
                    if result.isFinal {
                        self.cancelSilenceTimer()
                        self.isRecording = false
                        self.recognitionTask = nil
                        self.recognitionRequest = nil
                        self.onFinalResult?(text)
                    } else {
                        self.onPartialResult?(text)
                        if self.vadEnabled { self.resetSilenceTimer() }
                    }
                }
            }
            if let error = error {
                let code = (error as NSError).code
                guard code != 201 && code != 216 else { return }
                DispatchQueue.main.async {
                    self.cancelSilenceTimer()
                    self.isRecording = false
                    self.onError?(error.localizedDescription)
                }
            }
        }

        do {
            audioEngine.prepare()
            try audioEngine.start()
            // In VAD mode avvia subito il timer: se non parla entro 6s, stop
            if useVAD {
                silenceTimer = Timer.scheduledTimer(withTimeInterval: 6.0, repeats: false) { [weak self] _ in
                    self?.stopRecording()
                }
            }
        } catch {
            isRecording = false
            DispatchQueue.main.async { self.onError?("Audio engine: \(error.localizedDescription)") }
        }
    }

    func stopRecording() {
        guard isRecording else { return }
        cancelSilenceTimer()
        audioEngine.stop()
        if audioEngine.inputNode.numberOfInputs > 0 {
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        recognitionRequest?.endAudio()
        // onFinalResult arriva in modo asincrono dopo endAudio()
    }

    // MARK: - VAD helpers

    private func resetSilenceTimer() {
        silenceTimer?.invalidate()
        silenceTimer = Timer.scheduledTimer(withTimeInterval: silenceTimeout, repeats: false) { [weak self] _ in
            self?.stopRecording()
        }
    }

    private func cancelSilenceTimer() {
        silenceTimer?.invalidate()
        silenceTimer = nil
    }

    // MARK: - Cleanup

    private func cleanup() {
        cancelSilenceTimer()
        recognitionTask?.cancel()
        recognitionTask    = nil
        recognitionRequest = nil
        if audioEngine.isRunning {
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        isRecording = false
        vadEnabled  = false
    }
}
