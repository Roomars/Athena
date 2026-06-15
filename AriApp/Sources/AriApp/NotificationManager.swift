import Foundation

/// Mostra notifiche macOS via osascript — funziona senza bundle identifier.
final class NotificationManager {
    static let shared = NotificationManager()
    private init() {}

    func setup() {
        // Nessun setup necessario con osascript
    }

    func show(title: String, body: String) {
        let safeTitle = title.replacingOccurrences(of: "\"", with: "'")
        let safeBody  = body.replacingOccurrences(of:  "\"", with: "'")
        let script = "display notification \"\(safeBody)\" with title \"\(safeTitle)\""

        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        task.arguments = ["-e", script]
        try? task.run()
    }
}
