import AppKit
import SwiftUI
import DynamicNotchKit

/// Notifiche transient nel notch (o floating pill su Mac senza notch).
/// Usato per: heartbeat triggers, proactive alerts, model_ready, stati vocali brevi.
/// Il NotchPanel gestisce l'orb persistente — questo gestisce i toast.
@MainActor
final class AriNotchNotifier {
    static let shared = AriNotchNotifier()

    // Nasconde l'orb corrente dopo showDuration secondi
    private var hideTask: Task<Void, Never>?

    /// Mostra una notifica pill nel notch per `duration` secondi.
    func show(
        icon: String,
        title: String,
        description: String? = nil,
        duration: Double = 4.0,
        iconColor: Color = Color(red: 0, green: 0.85, blue: 1)
    ) {
        hideTask?.cancel()

        let notch = DynamicNotchInfo(
            icon:        .init(systemName: icon, color: iconColor),
            title:       LocalizedStringKey(title),
            description: description.map { LocalizedStringKey($0) },
            hoverBehavior: [.keepVisible, .hapticFeedback],
            style:       .auto
        )

        hideTask = Task {
            await notch.expand()
            try? await Task.sleep(for: .seconds(duration))
            guard !Task.isCancelled else { return }
            await notch.hide()
        }
    }

    /// Notifica con progress ring — usato per download o operazioni lunghe.
    func showProgress(
        title: String,
        progress: Binding<CGFloat>,
        duration: Double = 10.0
    ) {
        hideTask?.cancel()

        let notch = DynamicNotchInfo(
            icon:             .init(progress: progress, color: Color(red: 0, green: 0.85, blue: 1)),
            title:            LocalizedStringKey(title),
            compactLeading:   .init(systemName: "waveform", color: Color(red: 0, green: 0.85, blue: 1)),
            compactTrailing:  .init(progress: progress),
            hoverBehavior:    [.keepVisible],
            style:            .auto
        )

        hideTask = Task {
            await notch.compact()
        }
    }

    // MARK: - Preset per Ari

    func notifyModelReady(_ modelId: String) {
        show(icon: "brain", title: "Ari pronta", description: modelId, duration: 3)
    }

    func notifyListening() {
        show(icon: "mic.fill", title: "Ascolto", duration: 30, iconColor: .green)
    }

    func notifyThinking() {
        show(icon: "sparkles", title: "Elaboro", duration: 60, iconColor: Color(red: 0, green: 0.85, blue: 1))
    }

    func notifyHeartbeat(title: String, body: String) {
        show(icon: "bell.fill", title: title, description: body.prefix(80).description, duration: 6)
    }

    func notifyProactive(title: String, body: String) {
        let icon = _iconForTitle(title)
        show(icon: icon, title: title, description: body.prefix(80).description, duration: 5, iconColor: .orange)
    }

    func dismiss() {
        hideTask?.cancel()
    }

    private func _iconForTitle(_ title: String) -> String {
        let t = title.lowercased()
        if t.contains("cpu") || t.contains("temperatura") { return "thermometer.medium" }
        if t.contains("ram") || t.contains("memoria")    { return "memorychip" }
        if t.contains("disco")                            { return "internaldrive" }
        if t.contains("calcio") || t.contains("partita") { return "soccerball" }
        if t.contains("cantiere") || t.contains("lavoro"){ return "hammer" }
        return "bell.fill"
    }
}
