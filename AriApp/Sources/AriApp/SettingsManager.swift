import Foundation

struct AriSettings: Codable {
    var version: Int = 1
    // Hotkey voce — keyCode + modifiers (CGEventFlags raw)
    var hotkeyKeyCode:  Int    = 0          // 0 = tasto "A"
    var hotkeyModifiers: UInt64 = 1_179_648 // Cmd(1048576) + Shift(131072)
    var wakeWordEnabled: Bool = false
    var clapWakeEnabled: Bool = false
    var ttsEnabled:      Bool = true
    var ttsVoice:        String = "Federica (Premium)"
    var setupCompleted:  Bool = false
}

final class SettingsManager {
    static let shared = SettingsManager()
    var settings = AriSettings()

    private var url: URL {
        let support = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let dir = support.appendingPathComponent("Ari")
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir.appendingPathComponent("settings.json")
    }

    func load() {
        guard let data = try? Data(contentsOf: url),
              let decoded = try? JSONDecoder().decode(AriSettings.self, from: data)
        else { save(); return }
        settings = decoded
    }

    func save() {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        if let data = try? encoder.encode(settings) {
            try? data.write(to: url)
        }
    }
}
