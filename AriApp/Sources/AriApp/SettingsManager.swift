import Foundation

enum OrbMode: String, Codable {
    case floating   // pannello flottante libero (comportamento attuale)
    case notch      // ancorato al notch, espandibile
}

struct AriSettings: Codable {
    var version: Int = 1
    // Hotkey voce — keyCode + modifiers (CGEventFlags raw)
    var hotkeyKeyCode:  Int    = 0          // 0 = tasto "A"
    var hotkeyModifiers: UInt64 = 1_179_648 // Cmd(1048576) + Shift(131072)
    var wakeWordEnabled: Bool = false
    var clapWakeEnabled: Bool = false
    var ttsEnabled:      Bool = true
    var ttsVoice:        String = "Federica (Premium)"
    var snapEnabled:         Bool   = true
    var orbMode:             OrbMode = .floating
    var proactiveEnabled:    Bool   = true
    var panelOpacity:        Float  = 1.0
    // TTS engine — "apple" | "kokoro"
    var ttsEngine:           String = "apple"
    // TTS tuning — velocità e tono (50–150, default 100)
    var ttsRate:             Double = 100.0
    var ttsPitch:            Double = 100.0
    // Personalità vocale — "nessuna" | "professionale" | "amichevole" | "arguta"
    var activePersona:       String = "nessuna"
    // Accent color
    var accentColorHex:      String = "#00D9FF"
    // Alert thresholds
    var cpuAlertThreshold:   Double = 85.0
    var ramAlertThreshold:   Double = 88.0
    var tempAlertThreshold:  Double = 85.0
    // Risposta
    var responseFontSize:    Double = 13.0
    var autoHideResponse:    Bool   = false
    var autoHideDelay:       Double = 10.0
    var setupCompleted:      Bool   = false
    // Whitelist "Consenti sempre" per approvazione tool a 3 livelli.
    // Chiave: tipo azione (es. "computer_control", "code_runner"). Valore: sempre consentito.
    var alwaysAllowed:       [String: Bool] = [:]
    // Modello AI
    var selectedBackend:     String = "mlx"           // "mlx" | "openrouter"
    var openRouterModelId:   String = ""
    var openRouterApiKey:    String = ""
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
