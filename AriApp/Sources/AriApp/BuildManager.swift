import AppKit
import Foundation

/// Compila AriApp e rilancia il binario — usato dalla FASE 7 self-modify.
final class BuildManager {
    static let shared = BuildManager()

    var ariDir: String {
        let src = URL(fileURLWithPath: #file)
        return src
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .path
    }

    /// Esegue `swift build` in background.
    /// completion: (success, output)
    func build(onProgress: ((String) -> Void)? = nil,
               completion: @escaping (Bool, String) -> Void) {
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self else { return }

            let appDir = self.ariDir + "/AriApp"
            let p = Process()
            p.executableURL      = URL(fileURLWithPath: "/usr/bin/swift")
            p.arguments          = ["build"]
            p.currentDirectoryURL = URL(fileURLWithPath: appDir)

            let pipe = Pipe()
            p.standardOutput = pipe
            p.standardError  = pipe

            pipe.fileHandleForReading.readabilityHandler = { handle in
                let chunk = String(data: handle.availableData, encoding: .utf8) ?? ""
                if !chunk.isEmpty { onProgress?(chunk) }
            }

            do {
                try p.run()
                p.waitUntilExit()
                pipe.fileHandleForReading.readabilityHandler = nil
                let output  = String(data: pipe.fileHandleForReading.readDataToEndOfFile(),
                                     encoding: .utf8) ?? ""
                let success = p.terminationStatus == 0
                DispatchQueue.main.async { completion(success, output) }
            } catch {
                DispatchQueue.main.async { completion(false, error.localizedDescription) }
            }
        }
    }

    /// Lancia il nuovo binario e termina l'app corrente.
    func restart() {
        let binary = ariDir + "/AriApp/.build/debug/AriApp"
        guard FileManager.default.fileExists(atPath: binary) else { return }
        let p = Process()
        p.executableURL = URL(fileURLWithPath: binary)
        try? p.run()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) {
            NSApp.terminate(nil)
        }
    }
}
