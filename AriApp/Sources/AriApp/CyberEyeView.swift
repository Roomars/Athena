import SwiftUI

// Orb cybernetico ispirato all'occhio tech:
// pupilla nera + iris con raggi + anelli glow ciano + riflesso mobile
// Implementato con Canvas + TimelineView — nessun Metal necessario.

struct CyberEyeView: View {
    let state: OrbState
    let size: CGFloat

    var body: some View {
        TimelineView(.animation) { timeline in
            Canvas { ctx, canvasSize in
                let t = timeline.date.timeIntervalSinceReferenceDate
                let cx = canvasSize.width / 2
                let cy = canvasSize.height / 2
                // 0.40: le onde si espandono fino a r*2.1 → restano dentro min(cx,cy)*0.84
                let r = min(cx, cy) * 0.40
                draw(ctx: ctx, cx: cx, cy: cy, r: r, t: t)
            }
        }
        .frame(width: size, height: size)
    }

    // MARK: - Colori per stato

    private var primaryColor: Color {
        switch state {
        case .idle:      return Color(red: 0.0, green: 0.85, blue: 1.0)
        case .thinking:  return Color(red: 1.0, green: 0.6,  blue: 0.1)
        case .listening: return Color(red: 0.2, green: 1.0,  blue: 0.4)
        case .speaking:  return Color(red: 0.6, green: 0.2,  blue: 1.0)
        }
    }

    private var glowColor: Color { primaryColor.opacity(0.35) }

    // MARK: - Draw

    private func draw(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat, r: CGFloat, t: Double) {
        let col   = primaryColor
        let speed: Double = state == .thinking ? 1.8 : (state == .speaking ? 1.4 : 0.6)
        let amp: CGFloat  = state == .thinking ? 0.65 : (state == .speaking ? 1.1 : 0.35)

        // Ordine z:
        // particelle (fondo) → raggi iris → iris base (li vela) → pupilla → circuit segments → riflesso
        drawParticleRing(ctx: ctx, cx: cx, cy: cy, r: r * 0.92, t: t * speed, col: col, amp: amp)
        drawIrisRays(ctx: ctx, cx: cx, cy: cy, r: r * 0.62, t: t * speed, col: col)
        drawIrisBase(ctx: ctx, cx: cx, cy: cy, r: r * 0.62)
        drawPupil(ctx: ctx, cx: cx, cy: cy, r: r * 0.28)
        drawCircuitSegments(ctx: ctx, cx: cx, cy: cy, r: r * 0.72, t: t, col: col)
        drawSpecular(ctx: ctx, cx: cx, cy: cy, r: r * 0.20, t: t * 0.7)
    }

    // Particle ring da athenaOld/AIEyeView — 3 shell sinusoidali concentriche
    private func drawParticleRing(
        ctx: GraphicsContext, cx: CGFloat, cy: CGFloat,
        r: CGFloat, t: Double, col: Color, amp: CGFloat
    ) {
        let sc  = r / 38.0
        let amp = max(0.25, amp)
        let N   = 360

        let gctx = ctx

        let shells: [(dR: CGFloat, bright: Double)] = [
            (-4.0 * sc, 0.45),
            ( 0.0,      1.00),
            ( 5.0 * sc, 0.30),
        ]

        for shell in shells {
            for i in 0..<N {
                let θ  = Double(i) / Double(N) * 2 * .pi
                let w1 = 20.0 * sc * CGFloat(sin(4.0  * θ + t * 1.0))
                let w2 = 11.0 * sc * CGFloat(sin(7.0  * θ - t * 1.5 + 0.9))
                let w3 =  6.0 * sc * CGFloat(sin(11.0 * θ + t * 2.2 + 1.8))

                let dr = (w1 + w2 + w3) * amp + shell.dR
                let x  = cx + (r + dr) * CGFloat(cos(θ))
                let y  = cy + (r + dr) * CGFloat(sin(θ))

                let peak  = min(1.0, Double(abs(w1 + w2)) / Double(20.0 * sc))
                let alpha = shell.bright * (0.22 + peak * 0.78) * min(1.8, max(0.4, Double(amp)))
                let ptR   = (0.9 + peak * 2.0) * Double(sc) * min(1.5, max(0.5, Double(amp)))

                gctx.fill(
                    Path(ellipseIn: CGRect(x: x - CGFloat(ptR), y: y - CGFloat(ptR),
                                           width: CGFloat(ptR * 2), height: CGFloat(ptR * 2))),
                    with: .color(col.opacity(min(1.0, alpha)))
                )
            }
        }

        // Alone esterno ai picchi d'onda
        for i in stride(from: 0, to: N, by: 4) {
            let θ  = Double(i) / Double(N) * 2 * .pi
            let w  = 20.0 * sc * CGFloat(sin(4.0 * θ + t))
            let rr = r + w * amp + 9.0 * sc
            let x  = cx + rr * CGFloat(cos(θ))
            let y  = cy + rr * CGFloat(sin(θ))
            let fr = 0.7 * sc
            gctx.fill(
                Path(ellipseIn: CGRect(x: x - fr, y: y - fr, width: fr * 2, height: fr * 2)),
                with: .color(col.opacity(0.10))
            )
        }
    }

    // Segmenti arco "circuit board" sul ring intermedio
    private func drawCircuitSegments(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat, r: CGFloat, t: Double, col: Color) {
        let segCount = 24
        let rotOffset = t * 0.12
        for i in 0..<segCount {
            let angle = Double(i) / Double(segCount) * .pi * 2 + rotOffset
            let skip = (i % 4 == 3) // gap ogni 4
            if skip { continue }
            let arcLen: Double = (i % 3 == 0) ? 0.18 : 0.10
            let startA = angle
            let endA = angle + arcLen

            var path = Path()
            path.addArc(center: CGPoint(x: cx, y: cy),
                        radius: r,
                        startAngle: .radians(startA),
                        endAngle: .radians(endA),
                        clockwise: false)
            let opacity = 0.5 + 0.3 * sin(t * 2.0 + Double(i) * 0.4)
            ctx.stroke(path, with: .color(col.opacity(opacity)),
                       style: StrokeStyle(lineWidth: i % 3 == 0 ? 2.0 : 1.0))
        }
    }

    // Raggi radiali dell'iris — ruotano con lo stato
    private func drawIrisRays(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat, r: CGFloat, t: Double, col: Color) {
        let rayCount = 72
        let innerR = r * 0.45

        for i in 0..<rayCount {
            let angle = Double(i) / Double(rayCount) * .pi * 2 + t * 0.08
            let bright = (i % 3 == 0) ? 0.9 : 0.5
            let len = (i % 6 == 0) ? r : (i % 3 == 0 ? r * 0.85 : r * 0.70)

            let x1 = cx + innerR * cos(angle)
            let y1 = cy + innerR * sin(angle)
            let x2 = cx + len * cos(angle)
            let y2 = cy + len * sin(angle)

            var path = Path()
            path.move(to: CGPoint(x: x1, y: y1))
            path.addLine(to: CGPoint(x: x2, y: y2))

            ctx.stroke(path, with: .color(col.opacity(bright)),
                       style: StrokeStyle(lineWidth: i % 6 == 0 ? 0.6 : 0.25))
        }
    }

    // Base iris: cerchio sfumato teal/nero
    private func drawIrisBase(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat, r: CGFloat) {
        let rect = CGRect(x: cx - r, y: cy - r, width: r * 2, height: r * 2)
        ctx.drawLayer { inner in
            let gradient = Gradient(stops: [
                .init(color: Color(red: 0, green: 0.28, blue: 0.35).opacity(0.95), location: 0.0),
                .init(color: Color.black.opacity(0.80), location: 1.0),
            ])
            inner.fill(Path(ellipseIn: rect),
                       with: .radialGradient(gradient,
                                             center: CGPoint(x: cx, y: cy),
                                             startRadius: 0,
                                             endRadius: r))
        }
    }

    // Pupilla nera centrale
    private func drawPupil(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat, r: CGFloat) {
        let rect = CGRect(x: cx - r, y: cy - r, width: r * 2, height: r * 2)
        let gradient = Gradient(colors: [
            Color(red: 0.05, green: 0.05, blue: 0.08),
            Color.black,
        ])
        ctx.fill(Path(ellipseIn: rect),
                 with: .radialGradient(gradient,
                                       center: CGPoint(x: cx, y: cy),
                                       startRadius: 0,
                                       endRadius: r))
    }

    // Riflesso speculare che orbita intorno alla pupilla
    private func drawSpecular(ctx: GraphicsContext, cx: CGFloat, cy: CGFloat, r: CGFloat, t: Double) {
        let orbit = r * 0.65
        let sx = cx + orbit * cos(t) - r * 0.18
        let sy = cy + orbit * sin(t) - r * 0.10

        let specRect = CGRect(x: sx - r * 0.28, y: sy - r * 0.16,
                              width: r * 0.56, height: r * 0.32)
        let gradient = Gradient(colors: [
            Color.white.opacity(0.85),
            Color.white.opacity(0.0),
        ])
        ctx.fill(Path(ellipseIn: specRect),
                 with: .radialGradient(gradient,
                                       center: CGPoint(x: sx, y: sy),
                                       startRadius: 0,
                                       endRadius: r * 0.28))
    }
}

#Preview {
    ZStack {
        Color.black
        VStack(spacing: 20) {
            CyberEyeView(state: .idle, size: 120)
            HStack(spacing: 20) {
                CyberEyeView(state: .thinking, size: 80)
                CyberEyeView(state: .speaking, size: 80)
                CyberEyeView(state: .listening, size: 80)
            }
        }
    }
    .frame(width: 300, height: 280)
}
