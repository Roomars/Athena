import Foundation

// Avvia il daemon Python come subprocess e lo monitora.
// Se crasha, lo rilancia dopo 3 secondi (max 5 volte).
final class DaemonManager {
    static let shared = DaemonManager()

    private var process: Process?
    private var restartCount = 0
    private let maxRestarts = 5

    var daemonPath: String {
        // In produzione: bundle. In sviluppo: path relativo.
        if let bundlePath = Bundle.main.resourceURL?.appendingPathComponent("ari").path {
            return bundlePath
        }
        // Fallback sviluppo: cartella ari/ accanto all'app
        let here = URL(fileURLWithPath: #file)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
        return here.path
    }

    func start() {
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
    }

    private func waitForHealth(attempt: Int = 0) {
        guard attempt < 10 else {
            print("[DaemonManager] /health non risponde dopo 10 tentativi")
            return
        }
        let url = URL(string: "http://127.0.0.1:8765/health")!
        URLSession.shared.dataTask(with: url) { [weak self] _, resp, _ in
            if (resp as? HTTPURLResponse)?.statusCode == 200 {
                DispatchQueue.main.async { WebSocketManager.shared.connect() }
            } else {
                DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
                    self?.waitForHealth(attempt: attempt + 1)
                }
            }
        }.resume()
    }
}
