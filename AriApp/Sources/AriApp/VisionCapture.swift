import AppKit
import Foundation

enum VisionCapture {
    /// Cattura lo schermo principale, lo codifica in base64 e lo invia al brain.
    static func captureAndSend(prompt: String) {
        DispatchQueue.global(qos: .userInitiated).async {
            let tmpURL = URL(fileURLWithPath: NSTemporaryDirectory())
                .appendingPathComponent("ari_screen.png")

            let task = Process()
            task.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
            task.arguments     = ["-x", "-t", "png", tmpURL.path]
            try? task.run()
            task.waitUntilExit()

            guard let data = try? Data(contentsOf: tmpURL) else {
                DispatchQueue.main.async {
                    WebSocketManager.shared.send(content: "Errore: non riesco a catturare lo schermo.")
                }
                return
            }
            try? FileManager.default.removeItem(at: tmpURL)

            let b64 = data.base64EncodedString()
            DispatchQueue.main.async {
                WebSocketManager.shared.sendVisionRequest(image: b64, prompt: prompt)
            }
        }
    }
}
