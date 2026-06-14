import Foundation

struct AriSettings: Codable {
    var version: Int = 1
    var hotkey: String = "cmd+shift+a"
    var wakeWordEnabled: Bool = false
    var orbPosition: String = "notch"
    var ttsVoice: String = "Federica (Premium)"
    var setupCompleted: Bool = false

    enum CodingKeys: String, CodingKey {
        case version, hotkey
        case wakeWordEnabled = "wake_word_enabled"
        case orbPosition = "orb_position"
        case ttsVoice = "tts_voice"
        case setupCompleted = "setup_completed"
    }
}

final class SettingsManager {
    static let shared = SettingsManager()
    private(set) var settings = AriSettings()

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
