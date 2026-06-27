import SwiftUI
import WebKit

// WebOrbView — sfera plasma WebGL caricata da orb.html bundled.
// Comunicazione Swift→JS via evaluateJavaScript("setState('<STATE>')").
// Nessuna connessione di rete richiesta: Three.js è caricato da CDN,
// quindi serve internet al primo avvio (poi la cache browser lo mantiene).

struct WebOrbView: NSViewRepresentable {
    let state:    OrbState
    let size:     CGFloat

    func makeNSView(context: Context) -> WKWebView {
        let cfg = WKWebViewConfiguration()
        cfg.preferences.setValue(true, forKey: "developerExtrasEnabled")

        let wv = WKWebView(frame: .zero, configuration: cfg)
        wv.setValue(false, forKey: "drawsBackground")  // sfondo trasparente
        wv.layer?.backgroundColor = .clear
        wv.alphaValue = 1.0

        if let url = Bundle.module.url(forResource: "orb", withExtension: "html") {
            wv.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        }
        return wv
    }

    func updateNSView(_ wv: WKWebView, context: Context) {
        let js = "if(typeof go==='function'){go('\(jsState)', document.querySelector('.btn.on')||document.querySelector('.btn'));}"
        wv.evaluateJavaScript(js, completionHandler: nil)
    }

    private var jsState: String {
        switch state {
        case .idle:      return "IDLE"
        case .listening: return "IDLE"    // listening usa IDLE visivo (nessuna animazione aggiuntiva)
        case .thinking:  return "THINKING"
        case .speaking:  return "SPEAKING"
        }
    }
}
