import SwiftUI

// Electric plasma sphere — ispirato alle plasma ball nei riferimenti.
// Layer: background → outerHaze → [clip: sphereBody → swirls → lightning → innerGlow
//         → waveform(speaking) → scanArm(thinking)] → surfaceSparks → rim → hotCenter

struct CyberEyeView: View {
    let state:    OrbState
    let workload: Double
    let size:     CGFloat

    var body: some View {
        TimelineView(.animation(minimumInterval: 0.033, paused: false)) { tl in
            Canvas { ctx, sz in
                let t  = tl.date.timeIntervalSinceReferenceDate
                let cx = sz.width / 2
                let cy = sz.height / 2
                let r  = min(cx, cy) * 0.86
                drawAll(ctx: ctx, cx: cx, cy: cy, r: r, t: t)
            }
        }
        .frame(width: size, height: size)
    }

    // MARK: - Palette

    private var col: Color {
        switch state {
        case .idle:      return Color(red: 0.10, green: 0.65, blue: 1.00)
        case .listening: return Color(red: 0.30, green: 1.00, blue: 0.55)
        case .thinking:  return Color(red: 1.00, green: 0.52, blue: 0.05)
        case .speaking:  return Color(red: 0.72, green: 0.28, blue: 1.00)
        }
    }

    private var rotSpeed: Double {
        let b: Double
        switch state {
        case .idle:      b = 0.25
        case .listening: b = 0.55
        case .thinking:  b = 1.40
        case .speaking:  b = 0.80
        }
        return b * (1 + workload * 0.60)
    }

    private var bri: CGFloat {
        switch state {
        case .idle:      return 0.55
        case .listening: return 0.75
        case .thinking:  return 0.88
        case .speaking:  return 1.00
        }
    }

    // MARK: - Dispatcher

    private func drawAll(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat, r: CGFloat, t: Double) {
        drawBackground(ctx: ctx, cx: cx, cy: cy, r: r)
        drawOuterHaze(ctx: ctx, cx: cx, cy: cy, r: r, t: t)

        let sphereRect = CGRect(x: cx - r, y: cy - r, width: r * 2, height: r * 2)
        ctx.drawLayer { inner in
            inner.clip(to: Path(ellipseIn: sphereRect))
            drawSphereBody(ctx: inner, cx: cx, cy: cy, r: r, t: t)
            drawEnergySwirls(ctx: inner, cx: cx, cy: cy, r: r, t: t)
            drawLightning(ctx: inner, cx: cx, cy: cy, r: r, t: t)
            drawInnerGlow(ctx: inner, cx: cx, cy: cy, r: r, t: t)
            if state == .speaking  { drawWaveformRing(ctx: inner, cx: cx, cy: cy, r: r, t: t) }
            if state == .thinking  { drawScanArm(ctx: inner, cx: cx, cy: cy, r: r, t: t) }
        }

        drawSurfaceSparks(ctx: ctx, cx: cx, cy: cy, r: r, t: t)
        drawRim(ctx: ctx, cx: cx, cy: cy, r: r, t: t)
        drawHotCenter(ctx: ctx, cx: cx, cy: cy, r: r, t: t)
    }

    // MARK: - Background

    private func drawBackground(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat, r: CGFloat) {
        ctx.fill(Path(CGRect(x: cx - r * 1.5, y: cy - r * 1.5, width: r * 3, height: r * 3)),
                 with: .color(.black))
    }

    // MARK: - Outer haze

    private func drawOuterHaze(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                r: CGFloat, t: Double) {
        let pulse = CGFloat(0.5 + 0.5 * sin(t * 1.4))
        let hR    = r * 1.25
        let g = Gradient(stops: [
            .init(color: col.opacity(0),                             location: 0.50),
            .init(color: col.opacity(0.20 * bri * pulse),           location: 0.78),
            .init(color: col.opacity(0),                             location: 1.00),
        ])
        ctx.fill(Path(ellipseIn: CGRect(x: cx - hR, y: cy - hR, width: hR * 2, height: hR * 2)),
                 with: .radialGradient(g, center: CGPoint(x: cx, y: cy),
                                       startRadius: r * 0.50, endRadius: hR))
    }

    // MARK: - Sphere body (volumetric gradient)

    private func drawSphereBody(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                 r: CGFloat, t: Double) {
        let rect = CGRect(x: cx - r, y: cy - r, width: r * 2, height: r * 2)
        // Gradiente profondità: bianco caldo → colore plasma → profondo scuro ai bordi
        let g = Gradient(stops: [
            .init(color: Color.white.opacity(0.90),                                    location: 0.00),
            .init(color: Color(red: 0.75, green: 0.95, blue: 1.00).opacity(0.85),      location: 0.08),
            .init(color: col.opacity(0.78 * bri),                                      location: 0.30),
            .init(color: col.opacity(0.55 * bri),                                      location: 0.58),
            .init(color: Color(red: 0.03, green: 0.06, blue: 0.18).opacity(0.85),      location: 0.83),
            .init(color: Color(red: 0.01, green: 0.02, blue: 0.08).opacity(1.00),      location: 1.00),
        ])
        ctx.fill(Path(ellipseIn: rect),
                 with: .radialGradient(g, center: CGPoint(x: cx, y: cy),
                                       startRadius: 0, endRadius: r))
        // Speculare top-left — rende la sfera 3D
        let hlR = r * 0.42
        let hlX = cx - r * 0.27
        let hlY = cy - r * 0.28
        ctx.fill(
            Path(ellipseIn: CGRect(x: hlX - hlR, y: hlY - hlR, width: hlR * 2, height: hlR * 2)),
            with: .radialGradient(
                Gradient(colors: [Color.white.opacity(0.20), Color.white.opacity(0)]),
                center: CGPoint(x: hlX, y: hlY), startRadius: 0, endRadius: hlR))
    }

    // MARK: - Energy swirls (sfondo texture plasma — morbido)

    private func drawEnergySwirls(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                   r: CGFloat, t: Double) {
        ctx.drawLayer { layer in
            layer.blendMode = .plusLighter
            let count = 6
            let rot   = t * rotSpeed
            for i in 0..<count {
                let a0     = Double(i) / Double(count) * .pi * 2 + rot
                let pulse  = CGFloat(0.55 + 0.45 * sin(t * 2.2 + Double(i) * 0.95))
                let x0     = cx + r * 0.06 * CGFloat(cos(a0))
                let y0     = cy + r * 0.06 * CGFloat(sin(a0))
                let xc     = cx + r * 0.42 * CGFloat(cos(a0 + .pi / 4))
                let yc     = cy + r * 0.42 * CGFloat(sin(a0 + .pi / 4))
                let x1     = cx + r * 0.72 * pulse * CGFloat(cos(a0 + .pi / 2.6))
                let y1     = cy + r * 0.72 * pulse * CGFloat(sin(a0 + .pi / 2.6))
                var p = Path()
                p.move(to: CGPoint(x: x0, y: y0))
                p.addQuadCurve(to: CGPoint(x: x1, y: y1), control: CGPoint(x: xc, y: yc))
                layer.stroke(p, with: .color(col.opacity(0.09 * bri * pulse)),
                             style: StrokeStyle(lineWidth: 16, lineCap: .round))
                layer.stroke(p, with: .color(col.opacity(0.18 * bri * pulse)),
                             style: StrokeStyle(lineWidth: 5, lineCap: .round))
            }
        }
    }

    // MARK: - Lightning bolts (fulmine — il cuore dell'effetto elettrico)

    private func drawLightning(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                r: CGFloat, t: Double) {
        ctx.drawLayer { layer in
            layer.blendMode = .plusLighter
            let boltCount = state == .thinking ? 6 : (state == .speaking ? 5 : 4)
            for i in 0..<boltCount {
                let seed   = Double(i) * 1.618
                // Ogni fulmine appare/sparisce in modo indipendente
                let phase  = sin(t * (2.8 + seed * 0.7) + seed * 3.14)
                guard phase > -0.10 else { continue }
                let alpha  = CGFloat(min(1.0, (phase + 0.10) / 0.35)) * bri

                let baseAngle = Double(i) / Double(boltCount) * .pi * 2 + t * rotSpeed * 0.18
                drawBolt(ctx: layer, cx: cx, cy: cy, r: r, t: t,
                         baseAngle: baseAngle, seed: seed, alpha: alpha, branch: true)
            }
        }
    }

    private func drawBolt(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                           r: CGFloat, t: Double,
                           baseAngle: Double, seed: Double, alpha: CGFloat, branch: Bool) {
        let segments  = 7
        let innerR    = r * 0.06
        let outerR    = r * (0.68 + 0.12 * sin(seed * 2.1 + t * 0.4))
        let maxDev    = r * 0.18

        // Costruiamo i punti del fulmine
        var pts: [CGPoint] = []
        for j in 0...segments {
            let progress = Double(j) / Double(segments)
            let rr       = innerR + (outerR - innerR) * CGFloat(progress)
            // Deviazione perpendicolare — t * alta frequenza = jitter rapido
            let jitter   = maxDev * CGFloat(sin(seed * 3.14 + Double(j) * 1.3 + t * 11.0))
            let perpAngle = baseAngle + .pi / 2
            let x = cx + rr * CGFloat(cos(baseAngle)) + jitter * CGFloat(cos(perpAngle))
            let y = cy + rr * CGFloat(sin(baseAngle)) + jitter * CGFloat(sin(perpAngle))
            pts.append(CGPoint(x: x, y: y))
        }

        var path = Path()
        path.move(to: pts[0])
        for pt in pts.dropFirst() { path.addLine(to: pt) }

        // 1. Alone esterno soffice (glow)
        ctx.stroke(path, with: .color(col.opacity(0.18 * alpha)),
                   style: StrokeStyle(lineWidth: 10, lineCap: .round, lineJoin: .round))
        // 2. Corpo intermedio colorato
        ctx.stroke(path, with: .color(col.opacity(0.55 * alpha)),
                   style: StrokeStyle(lineWidth: 2.8, lineCap: .round, lineJoin: .round))
        // 3. Core bianco brillante
        ctx.stroke(path, with: .color(Color.white.opacity(0.75 * alpha)),
                   style: StrokeStyle(lineWidth: 1.0, lineCap: .round, lineJoin: .round))

        // Ramificazione: parte a metà del fulmine principale
        if branch, pts.count > 4 {
            let branchStart = pts[3]
            let branchAngle = baseAngle + .pi / 5.5
            let branchLen   = r * 0.28
            let bSeed       = seed + 7.3
            let bx = branchStart.x + branchLen * CGFloat(cos(branchAngle))
                   + CGFloat(sin(bSeed * 2 + t * 9.0)) * r * 0.08
            let by = branchStart.y + branchLen * CGFloat(sin(branchAngle))
                   + CGFloat(cos(bSeed * 2 + t * 9.0)) * r * 0.08
            var bp = Path()
            bp.move(to: branchStart)
            bp.addLine(to: CGPoint(x: bx, y: by))
            ctx.stroke(bp, with: .color(col.opacity(0.35 * alpha)),
                       style: StrokeStyle(lineWidth: 1.5, lineCap: .round))
            ctx.stroke(bp, with: .color(Color.white.opacity(0.45 * alpha)),
                       style: StrokeStyle(lineWidth: 0.6, lineCap: .round))
        }
    }

    // MARK: - Inner glow (nucleo caldo)

    private func drawInnerGlow(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                r: CGFloat, t: Double) {
        let pulse = CGFloat(0.88 + 0.12 * sin(t * 3.0))
        let gR    = r * 0.28 * pulse
        let g = Gradient(stops: [
            .init(color: Color.white.opacity(bri * 0.95),              location: 0.00),
            .init(color: col.opacity(bri * 0.70),                      location: 0.35),
            .init(color: col.opacity(bri * 0.20),                      location: 0.75),
            .init(color: col.opacity(0),                               location: 1.00),
        ])
        ctx.fill(Path(ellipseIn: CGRect(x: cx - gR, y: cy - gR, width: gR * 2, height: gR * 2)),
                 with: .radialGradient(g, center: CGPoint(x: cx, y: cy),
                                       startRadius: 0, endRadius: gR))
    }

    // MARK: - Waveform ring (speaking)

    private func drawWaveformRing(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                   r: CGFloat, t: Double) {
        let count = 44
        let base  = r * 0.80
        for i in 0..<count {
            let θ  = Double(i) / Double(count) * .pi * 2
            let a  = 0.3 + 0.7 * abs(sin(t * (1.8 + Double(i % 7) * 0.4) + Double(i) * 0.14))
            let bL = r * 0.04 + r * 0.10 * CGFloat(a)
            let x1 = cx + base * CGFloat(cos(θ))
            let y1 = cy + base * CGFloat(sin(θ))
            let x2 = cx + (base + bL) * CGFloat(cos(θ))
            let y2 = cy + (base + bL) * CGFloat(sin(θ))
            var p = Path(); p.move(to: CGPoint(x: x1, y: y1)); p.addLine(to: CGPoint(x: x2, y: y2))
            ctx.stroke(p, with: .color(col.opacity(0.45 + 0.55 * a)),
                       style: StrokeStyle(lineWidth: i % 4 == 0 ? 2.0 : 1.0, lineCap: .round))
        }
    }

    // MARK: - Scan arm (thinking)

    private func drawScanArm(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                              r: CGFloat, t: Double) {
        let θ  = t * rotSpeed * 1.5
        let rr = r * 0.88
        for j in 1...20 {
            let tr = θ - Double(j) * 0.055
            let fd = CGFloat(1 - Double(j) / 20.0)
            var tp = Path()
            tp.move(to: CGPoint(x: cx, y: cy))
            tp.addLine(to: CGPoint(x: cx + rr * CGFloat(cos(tr)), y: cy + rr * CGFloat(sin(tr))))
            ctx.stroke(tp, with: .color(col.opacity(0.50 * fd)),
                       style: StrokeStyle(lineWidth: 1.5))
        }
        var mp = Path()
        mp.move(to: CGPoint(x: cx, y: cy))
        mp.addLine(to: CGPoint(x: cx + rr * CGFloat(cos(θ)), y: cy + rr * CGFloat(sin(θ))))
        ctx.stroke(mp, with: .color(col.opacity(0.90)),
                   style: StrokeStyle(lineWidth: 1.8, lineCap: .round))
        let tx = cx + rr * CGFloat(cos(θ))
        let ty = cy + rr * CGFloat(sin(θ))
        ctx.fill(Path(ellipseIn: CGRect(x: tx-3, y: ty-3, width: 6, height: 6)),
                 with: .color(.white.opacity(0.95)))
    }

    // MARK: - Surface sparks (particelle sul bordo della sfera)

    private func drawSurfaceSparks(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                    r: CGFloat, t: Double) {
        let count = 28
        for i in 0..<count {
            let θ     = Double(i) / Double(count) * .pi * 2 + t * rotSpeed * 0.08
            let pulse = abs(sin(t * (3.5 + Double(i % 5) * 0.6) + Double(i) * 0.44))
            guard pulse > 0.25 else { continue }
            let radVar = CGFloat(1.0 + 0.06 * sin(t * 4.1 + Double(i) * 0.8))
            let rr     = r * radVar
            let x      = cx + rr * CGFloat(cos(θ))
            let y      = cy + rr * CGFloat(sin(θ))
            let pr     = CGFloat(1.2 + pulse * 3.0)
            // Particella
            ctx.fill(Path(ellipseIn: CGRect(x: x-pr, y: y-pr, width: pr*2, height: pr*2)),
                     with: .color(col.opacity(0.60 + 0.40 * pulse)))
            // Glow intorno alla particella
            let gr = pr * 3.5
            ctx.fill(Path(ellipseIn: CGRect(x: x-gr, y: y-gr, width: gr*2, height: gr*2)),
                     with: .color(col.opacity(0.12 * pulse)))
            // Spike radiale (scintilla)
            if pulse > 0.65 {
                let sLen = r * 0.06 * CGFloat(pulse)
                var sp   = Path()
                sp.move(to: CGPoint(x: x, y: y))
                sp.addLine(to: CGPoint(x: cx + (rr + sLen) * CGFloat(cos(θ)),
                                        y: cy + (rr + sLen) * CGFloat(sin(θ))))
                ctx.stroke(sp, with: .color(col.opacity(0.70 * pulse)),
                           style: StrokeStyle(lineWidth: 0.8, lineCap: .round))
            }
        }
    }

    // MARK: - Rim (bordo sfera luminoso)

    private func drawRim(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                          r: CGFloat, t: Double) {
        let pulse = CGFloat(0.65 + 0.35 * sin(t * 2.0))
        // Anello principale
        var p = Path()
        p.addEllipse(in: CGRect(x: cx-r, y: cy-r, width: r*2, height: r*2))
        ctx.stroke(p, with: .color(col.opacity(0.55 * bri * pulse)),
                   style: StrokeStyle(lineWidth: 1.5))
        // Alone esterno
        let gr = r * 1.03
        var gp = Path()
        gp.addEllipse(in: CGRect(x: cx-gr, y: cy-gr, width: gr*2, height: gr*2))
        ctx.stroke(gp, with: .color(col.opacity(0.14 * bri * pulse)),
                   style: StrokeStyle(lineWidth: 4.0))
    }

    // MARK: - Hot center

    private func drawHotCenter(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
                                r: CGFloat, t: Double) {
        let p = CGFloat(0.88 + 0.12 * sin(t * 4.5))
        let h = r * 0.048 * p
        ctx.fill(Path(ellipseIn: CGRect(x: cx-h, y: cy-h, width: h*2, height: h*2)),
                 with: .color(.white.opacity(0.98)))
        let aR = h * 3.2
        ctx.fill(Path(ellipseIn: CGRect(x: cx-aR, y: cy-aR, width: aR*2, height: aR*2)),
                 with: .radialGradient(
                    Gradient(colors: [.white.opacity(0.55), .white.opacity(0)]),
                    center: CGPoint(x: cx, y: cy), startRadius: 0, endRadius: aR))
    }
}

#Preview {
    ZStack {
        Color.black
        VStack(spacing: 22) {
            CyberEyeView(state: .idle,      workload: 0.10, size: 160)
            HStack(spacing: 22) {
                CyberEyeView(state: .thinking,  workload: 0.80, size: 100)
                CyberEyeView(state: .speaking,  workload: 0.55, size: 100)
                CyberEyeView(state: .listening, workload: 0.25, size: 100)
            }
        }
    }
    .frame(width: 420, height: 360)
}
