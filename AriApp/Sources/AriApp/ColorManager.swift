import AppKit

// Gestisce l'accent color dell'interfaccia.
// I pannelli osservano accentDidChange per aggiornarsi senza rebuild.
final class ColorManager {
    static let shared = ColorManager()
    static let accentDidChange = Notification.Name("ari.accentColorChanged")

    var accentColor: NSColor {
        NSColor(hex: SettingsManager.shared.settings.accentColorHex)
            ?? NSColor(red: 0, green: 0.85, blue: 1, alpha: 1)
    }

    func apply(_ color: NSColor) {
        SettingsManager.shared.settings.accentColorHex = color.hexString
        SettingsManager.shared.save()
        NotificationCenter.default.post(name: ColorManager.accentDidChange, object: color)
    }
}

// MARK: - NSColor hex helpers

extension NSColor {
    convenience init?(hex: String) {
        let h = hex.trimmingCharacters(in: .init(charactersIn: "#"))
        guard h.count == 6, let val = UInt64(h, radix: 16) else { return nil }
        self.init(
            red:   CGFloat((val >> 16) & 0xFF) / 255,
            green: CGFloat((val >>  8) & 0xFF) / 255,
            blue:  CGFloat( val        & 0xFF) / 255,
            alpha: 1
        )
    }

    var hexString: String {
        guard let c = usingColorSpace(.sRGB) else { return "#00D9FF" }
        let r = Int(c.redComponent   * 255)
        let g = Int(c.greenComponent * 255)
        let b = Int(c.blueComponent  * 255)
        return String(format: "#%02X%02X%02X", r, g, b)
    }
}
