import SwiftUI

@main
struct AriApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var delegate

    var body: some Scene {
        // Nessuna finestra principale — viviamo solo nella menu bar e nel notch
        Settings { EmptyView() }
    }
}
