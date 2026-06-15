import Foundation
import AVFoundation

/// Rileva un doppio battito di mani (doppio clap) come wake trigger.
/// Usa AVAudioEngine per monitorare l'ampiezza RMS in tempo reale.
/// Due picchi sopra la soglia entro 0.8 secondi = wake.
final class ClapWakeManager {
    static let shared = ClapWakeManager()

    private var engine:       AVAudioEngine?
    private var restartTimer: Timer?
    private(set) var isActive = false

    // Rilevazione
    private var lastPeak:     Float  = 0
    private var lastClapTime: Double = 0
    private let threshold:    Float  = 0.12   // RMS minima per un battito
    private let maxGap:       Double = 0.80   // secondi max tra i due battiti
    private let minGap:       Double = 0.10   // evita doppio-trigger su un singolo battito

    var onWakeDetected: (() -> Void)?

    private init() {}

    // MARK: - Pubblico

    func start() {
        guard !isActive else { return }
        isActive = true
        beginEngine()
    }

    func stop() {
        isActive = false
        restartTimer?.invalidate()
        restartTimer = nil
        endEngine()
    }

    // MARK: - Engine

    private func beginEngine() {
        guard isActive else { return }
        let eng = AVAudioEngine()
        engine  = eng
        let inputNode = eng.inputNode
        let fmt = inputNode.outputFormat(forBus: 0)

        inputNode.installTap(onBus: 0, bufferSize: 512, format: fmt) { [weak self] buf, _ in
            self?.processBuffer(buf)
        }

        do {
            eng.prepare()
            try eng.start()
        } catch {
            scheduleRestart(after: 5)
        }
    }

    private func endEngine() {
        guard let eng = engine else { return }
        if eng.isRunning {
            eng.inputNode.removeTap(onBus: 0)
            eng.stop()
        }
        engine = nil
    }

    // MARK: - Analisi audio (thread real-time)

    private func processBuffer(_ buffer: AVAudioPCMBuffer) {
        guard let ch = buffer.floatChannelData?[0] else { return }
        let count = Int(buffer.frameLength)
        var sum: Float = 0
        for i in 0..<count { sum += ch[i] * ch[i] }
        let rms = (count > 0) ? sqrt(sum / Float(count)) : 0

        // Onset detection: picco sopra soglia dopo silenzio relativo
        let wasQuiet = lastPeak < threshold * 0.4
        if rms > threshold && wasQuiet {
            let now  = CACurrentMediaTime()
            let gap  = now - lastClapTime

            if lastClapTime > 0 && gap < maxGap && gap > minGap {
                // Doppio battito rilevato
                lastClapTime = 0
                DispatchQueue.main.async { [weak self] in
                    guard let self, self.isActive else { return }
                    self.endEngine()
                    self.onWakeDetected?()
                    // Riprende ad ascoltare dopo 8s (tempo per la risposta vocale)
                    self.scheduleRestart(after: 8)
                }
            } else {
                lastClapTime = now
            }
        }
        lastPeak = rms
    }

    private func scheduleRestart(after delay: TimeInterval) {
        restartTimer?.invalidate()
        restartTimer = Timer.scheduledTimer(withTimeInterval: delay, repeats: false) { [weak self] _ in
            guard let self, self.isActive else { return }
            self.endEngine()
            self.beginEngine()
        }
    }
}
