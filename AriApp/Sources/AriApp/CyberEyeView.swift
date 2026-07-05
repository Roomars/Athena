import SwiftUI

struct CyberEyeView: View {
    let state:           OrbState
    let prevState:       OrbState
    let transitionStart: Date
    let workload:        Double
    let size:            CGFloat
    let activeEvent:     OrbEvent?
    let eventStart:      Date?

    var body: some View {
        TimelineView(.animation(minimumInterval: 0.033, paused: false)) { tl in
            Canvas { ctx, sz in
                let t  = tl.date.timeIntervalSinceReferenceDate
                let cx = sz.width / 2
                let cy = sz.height / 2
                let r  = min(cx, cy) * 0.54
                let lerpT = CGFloat(min(1.0, tl.date.timeIntervalSince(transitionStart) / 0.55))
                let evAge = eventStart.map { CGFloat(tl.date.timeIntervalSince($0)) }
                drawAll(ctx: ctx, cx: cx, cy: cy, r: r, t: t, lerpT: lerpT, evAge: evAge)
            }
        }
        .frame(width: size, height: size)
    }

    // MARK: - Palette (lerp RGB)

    private typealias RGB = (r: Double, g: Double, b: Double)

    private func stateRGB(_ s: OrbState) -> RGB {
        switch s {
        case .idle:      return (0.10, 0.65, 1.00)
        case .listening: return (0.30, 1.00, 0.55)
        case .thinking:  return (1.00, 0.52, 0.05)
        case .speaking:  return (0.72, 0.28, 1.00)
        }
    }

    private func lerpedCol(_ t: CGFloat) -> Color {
        let a = stateRGB(prevState), b = stateRGB(state), f = Double(t)
        return Color(red: a.r + (b.r - a.r) * f,
                     green: a.g + (b.g - a.g) * f,
                     blue:  a.b + (b.b - a.b) * f)
    }

    private func stateBri(_ s: OrbState) -> CGFloat {
        switch s {
        case .idle:      return 0.55
        case .listening: return 0.75
        case .thinking:  return 0.88
        case .speaking:  return 1.00
        }
    }

    private func lerpedBri(_ t: CGFloat) -> CGFloat {
        stateBri(prevState) + (stateBri(state) - stateBri(prevState)) * t
    }

    private func stateRotSpeed(_ s: OrbState) -> Double {
        let b: Double
        switch s {
        case .idle:      b = 0.25
        case .listening: b = 0.55
        case .thinking:  b = 1.40
        case .speaking:  b = 0.80
        }
        return b * (1 + workload * 0.60)
    }

    private func lerpedRotSpeed(_ t: CGFloat) -> Double {
        stateRotSpeed(prevState) + (stateRotSpeed(state) - stateRotSpeed(prevState)) * Double(t)
    }

    // MARK: - Dispatcher

    private func drawAll(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                         r: CGFloat, t: Double, lerpT: CGFloat, evAge: CGFloat?) {
        let col      = lerpedCol(lerpT)
        let bri      = lerpedBri(lerpT)
        let rotSpeed = lerpedRotSpeed(lerpT)

        drawOuterHaze(ctx: ctx, cx: cx, cy: cy, r: r, t: t, col: col, bri: bri)

        let sphereRect = CGRect(x: cx - r, y: cy - r, width: r * 2, height: r * 2)
        ctx.drawLayer { inner in
            inner.clip(to: Path(ellipseIn: sphereRect))
            drawSphereBody(ctx: inner, cx: cx, cy: cy, r: r, t: t, col: col, bri: bri)
            drawEnergySwirls(ctx: inner, cx: cx, cy: cy, r: r, t: t,
                             col: col, bri: bri, rotSpeed: rotSpeed)
            // Fulmini prima del guscio — appaiono intrappolati dentro la sfera
            drawLightning(ctx: inner, cx: cx, cy: cy, r: r, t: t,
                          col: col, bri: bri, rotSpeed: rotSpeed)
            // Guscio vitreo SOPRA i fulmini (Fresnel + speculare)
            drawVitreousShell(ctx: inner, cx: cx, cy: cy, r: r, t: t, col: col, bri: bri)
            drawInnerGlow(ctx: inner, cx: cx, cy: cy, r: r, t: t, col: col, bri: bri)
            if state == .speaking || (prevState == .speaking && lerpT < 1) {
                drawWaveformRing(ctx: inner, cx: cx, cy: cy, r: r, t: t,
                                 col: col, speakAmt: state == .speaking ? lerpT : 1 - lerpT)
            }
            if state == .thinking || (prevState == .thinking && lerpT < 1) {
                drawScanArm(ctx: inner, cx: cx, cy: cy, r: r, t: t,
                            col: col, rotSpeed: rotSpeed,
                            alpha: state == .thinking ? lerpT : 1 - lerpT)
            }
        }

        drawGravitationalWaves(ctx: ctx, cx: cx, cy: cy, r: r, t: t,
                               col: col, bri: bri, rotSpeed: rotSpeed)
        drawListeningRings(ctx: ctx, cx: cx, cy: cy, r: r, t: t,
                           col: col, lerpT: lerpT)
        if let age = evAge, age < 2.5 {
            drawEventPulse(ctx: ctx, cx: cx, cy: cy, r: r, evAge: age)
        }
        drawRim(ctx: ctx, cx: cx, cy: cy, r: r, t: t, col: col, bri: bri)
        drawHotCenter(ctx: ctx, cx: cx, cy: cy, r: r, t: t)
    }

    // MARK: - Outer haze

    private func drawOuterHaze(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                r: CGFloat, t: Double, col: Color, bri: CGFloat) {
        let pulse = CGFloat(0.5 + 0.5 * sin(t * 1.4))
        let hR    = r * 1.25
        let g = Gradient(stops: [
            .init(color: col.opacity(0),                   location: 0.50),
            .init(color: col.opacity(0.20 * bri * pulse),  location: 0.78),
            .init(color: col.opacity(0),                   location: 1.00),
        ])
        ctx.fill(Path(ellipseIn: CGRect(x: cx - hR, y: cy - hR, width: hR * 2, height: hR * 2)),
                 with: .radialGradient(g, center: CGPoint(x: cx, y: cy),
                                       startRadius: r * 0.50, endRadius: hR))
    }

    // MARK: - Sphere body (attenuazione non-lineare — guscio denso)

    private func drawSphereBody(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                 r: CGFloat, t: Double, col: Color, bri: CGFloat) {
        let rect = CGRect(x: cx - r, y: cy - r, width: r * 2, height: r * 2)
        // Stop addensati verso il centro: la sfera appare piena, non cava.
        // Curve quadratica simulata con 6 stop — opacity decade come (1-x)².
        let g = Gradient(stops: [
            .init(color: col.opacity(0.92 * bri), location: 0.00),
            .init(color: col.opacity(0.88 * bri), location: 0.20),
            .init(color: col.opacity(0.78 * bri), location: 0.42),
            .init(color: col.opacity(0.52 * bri), location: 0.62),
            .init(color: col.opacity(0.18 * bri), location: 0.82),
            .init(color: Color.clear,             location: 1.00),
        ])
        ctx.fill(Path(ellipseIn: rect),
                 with: .radialGradient(g, center: CGPoint(x: cx, y: cy),
                                       startRadius: 0, endRadius: r))
    }

    // MARK: - Energy swirls

    private func drawEnergySwirls(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                   r: CGFloat, t: Double, col: Color,
                                   bri: CGFloat, rotSpeed: Double) {
        ctx.drawLayer { layer in
            layer.blendMode = .plusLighter
            let count = 6; let rot = t * rotSpeed
            for i in 0..<count {
                let a0    = Double(i) / Double(count) * .pi * 2 + rot
                let pulse = CGFloat(0.55 + 0.45 * sin(t * 2.2 + Double(i) * 0.95))
                let x0 = cx + r * 0.06 * CGFloat(cos(a0))
                let y0 = cy + r * 0.06 * CGFloat(sin(a0))
                let xc = cx + r * 0.42 * CGFloat(cos(a0 + .pi / 4))
                let yc = cy + r * 0.42 * CGFloat(sin(a0 + .pi / 4))
                let x1 = cx + r * 0.72 * pulse * CGFloat(cos(a0 + .pi / 2.6))
                let y1 = cy + r * 0.72 * pulse * CGFloat(sin(a0 + .pi / 2.6))
                var p = Path()
                p.move(to: CGPoint(x: x0, y: y0))
                p.addQuadCurve(to: CGPoint(x: x1, y: y1), control: CGPoint(x: xc, y: yc))
                layer.stroke(p, with: .color(col.opacity(0.09 * bri * pulse)),
                             style: StrokeStyle(lineWidth: 16, lineCap: .round))
                layer.stroke(p, with: .color(col.opacity(0.18 * bri * pulse)),
                             style: StrokeStyle(lineWidth: 5,  lineCap: .round))
            }
        }
    }

    // MARK: - Lightning

    private func drawLightning(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                r: CGFloat, t: Double, col: Color,
                                bri: CGFloat, rotSpeed: Double) {
        ctx.drawLayer { layer in
            layer.blendMode = .plusLighter
            let boltCount = state == .thinking ? 6 : (state == .speaking ? 5 : 4)
            for i in 0..<boltCount {
                let seed  = Double(i) * 1.618
                let phase = sin(t * (2.8 + seed * 0.7) + seed * 3.14)
                guard phase > -0.10 else { continue }
                let alpha     = CGFloat(min(1.0, (phase + 0.10) / 0.35)) * bri
                let baseAngle = Double(i) / Double(boltCount) * .pi * 2 + t * rotSpeed * 0.18
                drawBolt(ctx: layer, cx: cx, cy: cy, r: r, t: t,
                         baseAngle: baseAngle, seed: seed, alpha: alpha, branch: true, col: col)
            }
        }
    }

    private func drawBolt(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                           r: CGFloat, t: Double, baseAngle: Double,
                           seed: Double, alpha: CGFloat, branch: Bool, col: Color) {
        let segments = 8
        let innerR   = r * 0.07
        let outerR   = r * (0.70 + 0.14 * sin(seed * 2.1 + t * 0.4))
        let maxDev   = r * 0.22   // ampiezza massima zigzag alla punta

        var pts: [CGPoint] = []
        for j in 0...segments {
            let progress  = Double(j) / Double(segments)
            let rr        = innerR + (outerR - innerR) * CGFloat(progress)
            // Jitter = 0 alla radice, scala con la distanza dal centro
            let jitter    = maxDev * CGFloat(progress) *
                            CGFloat(sin(seed * 3.14 + Double(j) * 1.5 + t * 11.5))
            let perpAngle = baseAngle + .pi / 2
            pts.append(CGPoint(
                x: cx + rr * CGFloat(cos(baseAngle)) + jitter * CGFloat(cos(perpAngle)),
                y: cy + rr * CGFloat(sin(baseAngle)) + jitter * CGFloat(sin(perpAngle))
            ))
        }

        // Tre passate per ogni segmento — spessore che si assottiglia dalla radice alla punta
        let rootW: CGFloat = 2.8   // 2.5-3.0 pt alla radice
        let tipW:  CGFloat = 0.6   // 0.5-1.0 pt alla punta

        for j in 0..<(pts.count - 1) {
            let prog = CGFloat(j) / CGFloat(pts.count - 1)
            let lw   = rootW + (tipW - rootW) * prog
            var seg  = Path(); seg.move(to: pts[j]); seg.addLine(to: pts[j + 1])
            // Glow morbido
            ctx.stroke(seg, with: .color(col.opacity(0.14 * alpha)),
                       style: StrokeStyle(lineWidth: lw * 5.0, lineCap: .round))
            // Corpo colorato
            ctx.stroke(seg, with: .color(col.opacity(0.60 * alpha)),
                       style: StrokeStyle(lineWidth: lw, lineCap: .round))
            // Core bianco brillante
            ctx.stroke(seg, with: .color(Color.white.opacity(0.82 * alpha)),
                       style: StrokeStyle(lineWidth: max(0.4, lw * 0.40), lineCap: .round))
        }

        // Ramo secondario (~40% della lunghezza principale)
        if branch, pts.count > 4 {
            let bIdx  = pts.count * 2 / 5
            let bSeed = seed + 7.3
            let bAngle = baseAngle + .pi / 5.0 + sin(bSeed) * 0.35
            let bLen   = r * (0.20 + 0.10 * sin(bSeed * 1.7))
            let bSegs  = 4
            var bpts: [CGPoint] = [pts[bIdx]]
            for j in 1...bSegs {
                let prog = Double(j) / Double(bSegs)
                let jit  = r * 0.07 * CGFloat(prog) * CGFloat(sin(bSeed * 2 + Double(j) + t * 9.0))
                let perp = bAngle + .pi / 2
                bpts.append(CGPoint(
                    x: bpts[j - 1].x + (bLen / CGFloat(bSegs)) * CGFloat(cos(bAngle))
                       + jit * CGFloat(cos(perp)),
                    y: bpts[j - 1].y + (bLen / CGFloat(bSegs)) * CGFloat(sin(bAngle))
                       + jit * CGFloat(sin(perp))
                ))
            }
            let bRootW: CGFloat = 1.4; let bTipW: CGFloat = 0.35
            for j in 0..<(bpts.count - 1) {
                let prog = CGFloat(j) / CGFloat(bpts.count - 1)
                let lw   = bRootW + (bTipW - bRootW) * prog
                var seg  = Path(); seg.move(to: bpts[j]); seg.addLine(to: bpts[j + 1])
                ctx.stroke(seg, with: .color(col.opacity(0.38 * alpha)),
                           style: StrokeStyle(lineWidth: lw + 2.5, lineCap: .round))
                ctx.stroke(seg, with: .color(Color.white.opacity(0.52 * alpha)),
                           style: StrokeStyle(lineWidth: max(0.3, lw * 0.50), lineCap: .round))
            }
        }
    }

    // MARK: - Vitreous shell (guscio vitreo sopra i fulmini)

    private func drawVitreousShell(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                    r: CGFloat, t: Double, col: Color, bri: CGFloat) {
        let rect = CGRect(x: cx - r, y: cy - r, width: r * 2, height: r * 2)

        // Fresnel / limb darkening: bordo scuro che simula rifrazione del vetro
        let fresnelG = Gradient(stops: [
            .init(color: Color.clear,                     location: 0.00),
            .init(color: Color.clear,                     location: 0.62),
            .init(color: col.opacity(0.06 * bri),         location: 0.80),
            .init(color: Color.black.opacity(0.42),       location: 0.93),
            .init(color: Color.black.opacity(0.65),       location: 1.00),
        ])
        ctx.fill(Path(ellipseIn: rect),
                 with: .radialGradient(fresnelG, center: CGPoint(x: cx, y: cy),
                                       startRadius: 0, endRadius: r))

        // Speculare primario — riflesso luce in alto a sinistra
        let hlX = cx - r * 0.28; let hlY = cy - r * 0.30
        let hlR = r * 0.40
        let specG = Gradient(stops: [
            .init(color: Color.white.opacity(0.30), location: 0.00),
            .init(color: Color.white.opacity(0.10), location: 0.55),
            .init(color: Color.clear,               location: 1.00),
        ])
        ctx.fill(
            Path(ellipseIn: CGRect(x: hlX - hlR, y: hlY - hlR, width: hlR * 2, height: hlR * 2)),
            with: .radialGradient(specG, center: CGPoint(x: hlX, y: hlY),
                                   startRadius: 0, endRadius: hlR))

        // Speculare secondario — piccolo punto brillante (caustic)
        let s2X = cx - r * 0.16; let s2Y = cy - r * 0.44
        let s2R = r * 0.09
        ctx.fill(
            Path(ellipseIn: CGRect(x: s2X - s2R, y: s2Y - s2R, width: s2R * 2, height: s2R * 2)),
            with: .radialGradient(
                Gradient(colors: [Color.white.opacity(0.60), Color.clear]),
                center: CGPoint(x: s2X, y: s2Y), startRadius: 0, endRadius: s2R))
    }

    // MARK: - Inner glow

    private func drawInnerGlow(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                r: CGFloat, t: Double, col: Color, bri: CGFloat) {
        let pulse = CGFloat(0.88 + 0.12 * sin(t * 3.0))
        let gR    = r * 0.28 * pulse
        let g = Gradient(stops: [
            .init(color: Color.white.opacity(bri * 0.95), location: 0.00),
            .init(color: col.opacity(bri * 0.70),         location: 0.35),
            .init(color: col.opacity(bri * 0.20),         location: 0.75),
            .init(color: col.opacity(0),                  location: 1.00),
        ])
        ctx.fill(Path(ellipseIn: CGRect(x: cx - gR, y: cy - gR, width: gR * 2, height: gR * 2)),
                 with: .radialGradient(g, center: CGPoint(x: cx, y: cy),
                                       startRadius: 0, endRadius: gR))
    }

    // MARK: - Waveform ring (speaking)

    private func drawWaveformRing(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                   r: CGFloat, t: Double, col: Color, speakAmt: CGFloat) {
        let count = 44; let base = r * 0.80
        for i in 0..<count {
            let θ  = Double(i) / Double(count) * .pi * 2
            let a  = 0.3 + 0.7 * abs(sin(t * (1.8 + Double(i % 7) * 0.4) + Double(i) * 0.14))
            let bL = r * 0.04 + r * 0.10 * CGFloat(a) * speakAmt
            let x1 = cx + base * CGFloat(cos(θ));  let y1 = cy + base * CGFloat(sin(θ))
            let x2 = cx + (base + bL) * CGFloat(cos(θ)); let y2 = cy + (base + bL) * CGFloat(sin(θ))
            var p = Path(); p.move(to: CGPoint(x: x1, y: y1)); p.addLine(to: CGPoint(x: x2, y: y2))
            ctx.stroke(p, with: .color(col.opacity((0.45 + 0.55 * a) * Double(speakAmt))),
                       style: StrokeStyle(lineWidth: i % 4 == 0 ? 2.0 : 1.0, lineCap: .round))
        }
    }

    // MARK: - Scan arm (thinking)

    private func drawScanArm(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                              r: CGFloat, t: Double, col: Color,
                              rotSpeed: Double, alpha: CGFloat) {
        let θ  = t * rotSpeed * 1.5; let rr = r * 0.88
        for j in 1...20 {
            let tr = θ - Double(j) * 0.055
            let fd = CGFloat(1 - Double(j) / 20.0) * alpha
            var tp = Path()
            tp.move(to: CGPoint(x: cx, y: cy))
            tp.addLine(to: CGPoint(x: cx + rr * CGFloat(cos(tr)), y: cy + rr * CGFloat(sin(tr))))
            ctx.stroke(tp, with: .color(col.opacity(0.50 * fd)), style: StrokeStyle(lineWidth: 1.5))
        }
        var mp = Path(); mp.move(to: CGPoint(x: cx, y: cy))
        mp.addLine(to: CGPoint(x: cx + rr * CGFloat(cos(θ)), y: cy + rr * CGFloat(sin(θ))))
        ctx.stroke(mp, with: .color(col.opacity(0.90 * alpha)),
                   style: StrokeStyle(lineWidth: 1.8, lineCap: .round))
        let tx = cx + rr * CGFloat(cos(θ)); let ty = cy + rr * CGFloat(sin(θ))
        ctx.fill(Path(ellipseIn: CGRect(x: tx - 3, y: ty - 3, width: 6, height: 6)),
                 with: .color(.white.opacity(0.95 * alpha)))
    }

    // MARK: - Listening rings (NUOVO)

    private func drawListeningRings(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                     r: CGFloat, t: Double, col: Color, lerpT: CGFloat) {
        let listenAmt: CGFloat = {
            if state == .listening { return lerpT }
            if prevState == .listening { return 1 - lerpT }
            return 0
        }()
        guard listenAmt > 0.01 else { return }
        for i in 0..<3 {
            let phase    = Double(i) / 3.0
            let progress = CGFloat(fmod(t * 0.55 + phase, 1.0))
            let ringR    = r * (1.06 + progress * 0.38)
            let fade     = (1.0 - progress) * 0.45 * listenAmt
            var ring = Path()
            ring.addEllipse(in: CGRect(x: cx - ringR, y: cy - ringR,
                                       width: ringR * 2, height: ringR * 2))
            ctx.stroke(ring, with: .color(col.opacity(Double(fade))),
                       style: StrokeStyle(lineWidth: 1.5))
        }
    }

    // MARK: - Gravitational waves

    private func drawGravitationalWaves(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                         r: CGFloat, t: Double, col: Color,
                                         bri: CGFloat, rotSpeed: Double) {
        let u = r / 60.0
        let amp: CGFloat
        switch state {
        case .idle:      amp = 0.40
        case .listening: amp = 0.65
        case .thinking:  amp = 0.90
        case .speaking:  amp = 1.20
        }
        let N = 300; let base = t * rotSpeed
        let pulse = CGFloat(0.80 + 0.20 * sin(t * 1.7))
        let waves: [(baseR: CGFloat, f1: Double, f2: Double, speed: Double,
                     color: Color, lw: CGFloat, alpha: CGFloat)] = [
            (r * 1.10, 3, 6, 0.60, col,                       1.6, 0.55),
            (r * 1.20, 4, 8, 1.00, col,                       2.0, 0.75),
            (r * 1.30, 5, 3, 1.40, Color.white.opacity(0.85), 1.0, 0.50),
            (r * 1.42, 3, 7, 1.80, col.opacity(0.70),         0.7, 0.35),
        ]
        ctx.drawLayer { layer in
            layer.blendMode = .plusLighter
            for wave in waves {
                let tS = base * wave.speed
                var path = Path()
                for i in 0...N {
                    let θ  = Double(i) / Double(N) * 2 * .pi
                    let dr = amp * (
                        10.0 * u * CGFloat(sin(wave.f1 * θ + tS)) +
                         4.0 * u * CGFloat(sin(wave.f2 * θ - tS * 0.75 + 1.3))
                    )
                    let rr = wave.baseR + dr
                    let pt = CGPoint(x: cx + rr * CGFloat(cos(θ)), y: cy + rr * CGFloat(sin(θ)))
                    i == 0 ? path.move(to: pt) : path.addLine(to: pt)
                }
                path.closeSubpath()
                let a = wave.alpha * pulse
                layer.stroke(path, with: .color(wave.color.opacity(Double(a * 0.18))),
                             style: StrokeStyle(lineWidth: wave.lw * 6, lineCap: .round))
                layer.stroke(path, with: .color(wave.color.opacity(Double(a * 0.35))),
                             style: StrokeStyle(lineWidth: wave.lw * 2.5, lineCap: .round))
                layer.stroke(path, with: .color(wave.color.opacity(Double(a))),
                             style: StrokeStyle(lineWidth: wave.lw, lineCap: .round))
            }
        }
    }

    // MARK: - Event pulse (NUOVO)

    private func drawEventPulse(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                 r: CGFloat, evAge: CGFloat) {
        let pulseColor: Color
        switch activeEvent {
        case .memorySave:    pulseColor = Color(red: 0.0, green: 1.0, blue: 0.6)
        case .contradiction: pulseColor = Color(red: 1.0, green: 0.2, blue: 0.1)
        case .entityUpdate:  pulseColor = Color(red: 0.6, green: 0.4, blue: 1.0)
        case nil:            return
        }
        let fade = max(0, 1.0 - evAge / 2.5)
        for i in 0..<2 {
            let delay    = CGFloat(i) * 0.6
            let progress = min(1.0, max(0, (evAge - delay) * 0.7)  )
            let ringR    = r * (1.08 + progress * 0.85)
            let alpha    = fade * (1.0 - progress) * 0.75
            guard alpha > 0.01 else { continue }
            var ring = Path()
            ring.addEllipse(in: CGRect(x: cx - ringR, y: cy - ringR,
                                       width: ringR * 2, height: ringR * 2))
            ctx.stroke(ring, with: .color(pulseColor.opacity(Double(alpha))),
                       style: StrokeStyle(lineWidth: 2.0))
            // alone morbido
            ctx.stroke(ring, with: .color(pulseColor.opacity(Double(alpha * 0.3))),
                       style: StrokeStyle(lineWidth: 7.0))
        }
    }

    // MARK: - Rim

    private func drawRim(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                          r: CGFloat, t: Double, col: Color, bri: CGFloat) {
        let pulse = CGFloat(0.65 + 0.35 * sin(t * 2.0))
        var p = Path()
        p.addEllipse(in: CGRect(x: cx - r, y: cy - r, width: r * 2, height: r * 2))
        ctx.stroke(p, with: .color(col.opacity(0.55 * bri * pulse)),
                   style: StrokeStyle(lineWidth: 1.5))
        let gr = r * 1.03
        var gp = Path()
        gp.addEllipse(in: CGRect(x: cx - gr, y: cy - gr, width: gr * 2, height: gr * 2))
        ctx.stroke(gp, with: .color(col.opacity(0.14 * bri * pulse)),
                   style: StrokeStyle(lineWidth: 4.0))
    }

    // MARK: - Hot center

    private func drawHotCenter(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                r: CGFloat, t: Double) {
        let p = CGFloat(0.88 + 0.12 * sin(t * 4.5))
        let h = r * 0.048 * p
        ctx.fill(Path(ellipseIn: CGRect(x: cx - h, y: cy - h, width: h * 2, height: h * 2)),
                 with: .color(.white.opacity(0.98)))
        let aR = h * 3.2
        ctx.fill(Path(ellipseIn: CGRect(x: cx - aR, y: cy - aR, width: aR * 2, height: aR * 2)),
                 with: .radialGradient(
                    Gradient(colors: [.white.opacity(0.55), .white.opacity(0)]),
                    center: CGPoint(x: cx, y: cy), startRadius: 0, endRadius: aR))
    }
}

#Preview {
    ZStack {
        Color.black
        VStack(spacing: 22) {
            CyberEyeView(state: .idle, prevState: .idle, transitionStart: .now,
                         workload: 0.10, size: 160, activeEvent: nil, eventStart: nil)
            HStack(spacing: 22) {
                CyberEyeView(state: .thinking, prevState: .idle, transitionStart: .now,
                             workload: 0.80, size: 100, activeEvent: nil, eventStart: nil)
                CyberEyeView(state: .speaking, prevState: .thinking, transitionStart: .now,
                             workload: 0.55, size: 100, activeEvent: .memorySave, eventStart: .now)
                CyberEyeView(state: .listening, prevState: .idle, transitionStart: .now,
                             workload: 0.25, size: 100, activeEvent: nil, eventStart: nil)
            }
        }
    }
    .frame(width: 420, height: 360)
}
