import Foundation

// Avvia il daemon Python come subprocess e lo monitora.
// Se crasha, lo rilancia dopo 3 secondi (max 5 volte).
final class DaemonManager {
    static let shared = DaemonManager()

    private var process: Process?
    private var restartCount = 0
    private let maxRestarts = 5

    var daemonPath: String {
        // Produzione: ari/ dentro il bundle Resources
        if let bundleRes = Bundle.main.resourceURL {
            let candidate = bundleRes.appendingPathComponent("ari")
            if FileManager.default.fileExists(atPath: candidate.appendingPathComponent(".venv").path) {
                return candidate.path
            }
        }
        // Sviluppo Xcode: risali dal file sorgente fino a ari/
        // #file = .../ari/AriApp/Sources/AriApp/DaemonManager.swift
        let src = URL(fileURLWithPath: #file)
        let ariDir = src
            .deletingLastPathComponent()  // AriApp/
            .deletingLastPathComponent()  // Sources/
            .deletingLastPathComponent()  // AriApp (package)/
            .deletingLastPathComponent()  // ari/
        return ariDir.path
    }

    func start() {
        freePort()
        let ariDir = daemonPath
        let venv = "\(ariDir)/.venv/bin/uvicorn"
        let uvicorn = FileManager.default.fileExists(atPath: venv) ? venv : "uvicorn"

        let p = Process()
        p.executableURL = URL(fileURLWithPath: uvicorn)
        p.arguments = ["brain.main:app", "--host", "127.0.0.1", "--port", "8765", "--log-level", "warning"]
        p.currentDirectoryURL = URL(fileURLWithPath: ariDir)

        p.terminationHandler = { [weak self] _ in
            guard let self, self.restartCount < self.maxRestarts else { return }
            self.restartCount += 1
            print("[DaemonManager] daemon terminato, riavvio \(self.restartCount)/\(self.maxRestarts)")
            DispatchQueue.main.asyncAfter(deadline: .now() + 3) { self.start() }
        }

        do {
            try p.run()
            process = p
            restartCount = 0
            print("[DaemonManager] daemon avviato (PID \(p.processIdentifier))")
            // Attende che /health risponda prima di aprire il WebSocket
            waitForHealth()
        } catch {
            print("[DaemonManager] errore avvio daemon: \(error)")
        }
    }

    func stop() {
        process?.terminate()
        process = nil
        freePort()
    }

    private func freePort() {
        let killer = Process()
        killer.executableURL = URL(fileURLWithPath: "/bin/sh")
        killer.arguments = ["-c", "lsof -ti:8765 | xargs kill -9 2>/dev/null; true"]
        try? killer.run()
        killer.waitUntilExit()
    }

    private func waitForHealth(attempt: Int = 0) {
        guard attempt < 60 else {
            print("[DaemonManager] /health non risponde dopo 60 tentativi — controlla i log del daemon")
            return
        }
        // Prima attesa più lunga: il daemon impiega qualche secondo per avviarsi
        let delay: Double = attempt == 0 ? 3.0 : 2.0
        DispatchQueue.main.asyncAfter(deadline: .now() + delay) { [weak self] in
            let url = URL(string: "http://127.0.0.1:8765/health")!
            URLSession.shared.dataTask(with: url) { _, resp, _ in
                if (resp as? HTTPURLResponse)?.statusCode == 200 {
                    DispatchQueue.main.async { WebSocketManager.shared.connect() }
                } else {
                    self?.waitForHealth(attempt: attempt + 1)
                }
            }.resume()
        }
    }
}
