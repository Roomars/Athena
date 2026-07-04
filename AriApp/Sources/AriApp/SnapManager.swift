import AppKit

final class SnapManager {
    static let shared = SnapManager()

    private var groups:        [[AriPanel]]                  = []
    private var lastPositions: [ObjectIdentifier: NSPoint]   = [:]
    private var lastSizes:     [ObjectIdentifier: NSSize]    = [:]
    private var isMovingGroup  = false
    private var isResizingGroup = false
    private let snapThreshold: CGFloat = 14
    private let edgeThreshold: CGFloat = 20   // snap verso bordi schermo
    private let accentColor    = NSColor(red: 0, green: 0.85, blue: 1, alpha: 0.7)

    // MARK: - Registration

    func register(_ panels: [AriPanel]) {
        groups = panels.map { [$0] }
        for p in panels { observe(p) }
    }

    // Aggiunge un panel creato dopo la registrazione iniziale (es. MemoryPanel)
    func registerExtra(_ panel: AriPanel) {
        groups.append([panel])
        observe(panel)
    }

    private func observe(_ panel: AriPanel) {
        let id = ObjectIdentifier(panel)
        lastPositions[id] = panel.frame.origin
        lastSizes[id]     = panel.frame.size
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(panelDidMove(_:)),
            name: NSWindow.didMoveNotification,
            object: panel
        )
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(panelDidResize(_:)),
            name: NSWindow.didResizeNotification,
            object: panel
        )
    }

    var isEnabled: Bool {
        get { SettingsManager.shared.settings.snapEnabled }
    }

    // MARK: - Move sync

    @objc private func panelDidMove(_ note: Notification) {
        guard isEnabled, !isMovingGroup, let moved = note.object as? AriPanel else { return }
        let id = ObjectIdentifier(moved)
        guard let last = lastPositions[id] else {
            lastPositions[id] = moved.frame.origin; return
        }
        let delta = NSPoint(x: moved.frame.origin.x - last.x,
                            y: moved.frame.origin.y - last.y)
        guard delta.x != 0 || delta.y != 0 else { return }
        lastPositions[id] = moved.frame.origin

        // Drag all peers in the same group
        isMovingGroup = true
        for peer in findGroup(of: moved) where peer !== moved {
            let o   = peer.frame.origin
            let neo = NSPoint(x: o.x + delta.x, y: o.y + delta.y)
            peer.setFrameOrigin(neo)
            lastPositions[ObjectIdentifier(peer)] = neo
        }
        isMovingGroup = false

        checkSnap(movedGroup: findGroup(of: moved))
    }

    // MARK: - Resize propagation (Pack B)

    @objc private func panelDidResize(_ note: Notification) {
        guard isEnabled, !isResizingGroup, !isMovingGroup,
              let resized = note.object as? AriPanel else { return }
        let id      = ObjectIdentifier(resized)
        let oldSize = lastSizes[id] ?? resized.frame.size
        let newSize = resized.frame.size
        let dw = newSize.width  - oldSize.width
        let dh = newSize.height - oldSize.height
        lastSizes[id] = newSize
        guard abs(dw) > 0.5 || abs(dh) > 0.5 else { return }

        isResizingGroup = true
        let group = findGroup(of: resized)
        let rf    = resized.frame
        let t: CGFloat = 3

        for peer in group where peer !== resized {
            var pf = peer.frame
            // Condivide bordo destro di resized → sposta peer X
            if abs(rf.maxX - pf.minX) < t {
                pf.origin.x += dw
                pf.size.width = max(peer.minSize.width, pf.size.width - dw)
            }
            // Condivide bordo sinistro di resized → peer si allarga a sinistra
            else if abs(rf.minX - pf.maxX) < t {
                pf.size.width = max(peer.minSize.width, pf.size.width + dw)
            }
            // Condivide bordo superiore di resized → sposta peer Y
            if abs(rf.maxY - pf.minY) < t {
                pf.origin.y += dh
                pf.size.height = max(peer.minSize.height, pf.size.height - dh)
            }
            // Condivide bordo inferiore di resized → peer si allarga
            else if abs(rf.minY - pf.maxY) < t {
                pf.size.height = max(peer.minSize.height, pf.size.height + dh)
            }
            peer.setFrame(pf, display: true, animate: false)
            lastSizes[ObjectIdentifier(peer)]     = pf.size
            lastPositions[ObjectIdentifier(peer)] = pf.origin
        }
        isResizingGroup = false
        updateVisuals()
    }

    // MARK: - Snap detection

    private func checkSnap(movedGroup: [AriPanel]) {
        // 1. Snap pannello↔pannello
        for panel in movedGroup {
            for group in groups where !group.contains(where: { $0 === panel }) {
                for other in group {
                    if let neo = snapFrame(panel, to: other) {
                        isMovingGroup = true
                        panel.setFrame(neo, display: true, animate: false)
                        lastPositions[ObjectIdentifier(panel)] = neo.origin
                        isMovingGroup = false
                        mergeGroups(containing: panel, and: other)
                        updateVisuals()
                        return
                    }
                }
            }
        }
        // 2. Snap verso bordi schermo
        for panel in movedGroup {
            if let neo = snapToScreenEdge(panel) {
                isMovingGroup = true
                panel.setFrameOrigin(neo)
                lastPositions[ObjectIdentifier(panel)] = neo
                isMovingGroup = false
            }
        }
        updateVisuals()
    }

    private func snapToScreenEdge(_ panel: AriPanel) -> NSPoint? {
        guard let screen = panel.screen ?? NSScreen.main else { return nil }
        let sf = screen.visibleFrame
        let pf = panel.frame
        let t  = edgeThreshold
        var x  = pf.origin.x
        var y  = pf.origin.y
        var snapped = false

        if abs(pf.minX - sf.minX) < t { x = sf.minX;             snapped = true }
        if abs(pf.maxX - sf.maxX) < t { x = sf.maxX - pf.width;  snapped = true }
        if abs(pf.minY - sf.minY) < t { y = sf.minY;             snapped = true }
        if abs(pf.maxY - sf.maxY) < t { y = sf.maxY - pf.height; snapped = true }

        return snapped ? NSPoint(x: x, y: y) : nil
    }

    // Returns the snapped frame for `a` relative to `b`:
    // horizontal snap → a adopts b's height and bottom-aligns
    // vertical snap   → a adopts b's width and left-aligns
    private func snapFrame(_ a: AriPanel, to b: AriPanel) -> NSRect? {
        let af = a.frame
        let bf = b.frame
        let t  = snapThreshold

        let vOverlap = min(af.maxY, bf.maxY) - max(af.minY, bf.minY) > 20
        let hOverlap = min(af.maxX, bf.maxX) - max(af.minX, bf.minX) > 20

        // A snaps to LEFT of B (a.maxX ≈ b.minX)
        if vOverlap && abs(af.maxX - bf.minX) < t {
            return NSRect(x: bf.minX - af.width, y: bf.minY, width: af.width, height: bf.height)
        }
        // A snaps to RIGHT of B (a.minX ≈ b.maxX)
        if vOverlap && abs(af.minX - bf.maxX) < t {
            return NSRect(x: bf.maxX, y: bf.minY, width: af.width, height: bf.height)
        }
        // A snaps ABOVE B (a.minY ≈ b.maxY)
        if hOverlap && abs(af.minY - bf.maxY) < t {
            return NSRect(x: bf.minX, y: bf.maxY, width: bf.width, height: af.height)
        }
        // A snaps BELOW B (a.maxY ≈ b.minY)
        if hOverlap && abs(af.maxY - bf.minY) < t {
            return NSRect(x: bf.minX, y: bf.minY - af.height, width: bf.width, height: af.height)
        }
        return nil
    }

    // MARK: - Group management

    func findGroup(of panel: AriPanel) -> [AriPanel] {
        groups.first(where: { $0.contains(where: { $0 === panel }) }) ?? [panel]
    }

    func isInGroup(_ panel: AriPanel) -> Bool {
        findGroup(of: panel).count > 1
    }

    private func mergeGroups(containing a: AriPanel, and b: AriPanel) {
        guard let i = groupIndex(of: a), let j = groupIndex(of: b), i != j else { return }
        let merged = groups[i] + groups[j]
        let hi = max(i, j), lo = min(i, j)
        groups.remove(at: hi)
        groups.remove(at: lo)
        groups.append(merged)
    }

    func separateAll() {
        groups = groups.flatMap { $0 }.map { [$0] }
        updateVisuals()
    }

    func separate(_ panel: AriPanel) {
        guard isInGroup(panel),
              let idx = groupIndex(of: panel) else { return }
        var group = groups[idx]
        group.removeAll(where: { $0 === panel })
        groups.remove(at: idx)
        if !group.isEmpty { groups.append(group) }
        groups.append([panel])
        // Nudge so the separation is visible
        let o = panel.frame.origin
        panel.setFrameOrigin(NSPoint(x: o.x + 24, y: o.y - 24))
        lastPositions[ObjectIdentifier(panel)] = panel.frame.origin
        updateVisuals()
    }

    private func groupIndex(of panel: AriPanel) -> Int? {
        groups.firstIndex(where: { $0.contains(where: { $0 === panel }) })
    }

    // MARK: - Visuals

    func updateVisuals() {
        let allPanels = groups.flatMap { $0 }
        // Remove stale edge indicators
        for p in allPanels {
            p.contentView?.subviews.filter { $0.identifier?.rawValue == "snapEdge" }.forEach { $0.removeFromSuperview() }
        }
        for group in groups {
            for panel in group {
                applyCorners(panel, group: group)
                if group.count > 1 { addEdgeLines(panel, group: group) }
            }
        }
    }

    // Corner masking: flatten corners on the shared edges
    private func applyCorners(_ panel: AriPanel, group: [AriPanel]) {
        guard let cv = panel.contentView else { return }
        cv.wantsLayer = true
        cv.layer?.cornerRadius   = 10
        cv.layer?.masksToBounds  = true

        var mask: CACornerMask = [
            .layerMinXMinYCorner, .layerMinXMaxYCorner,
            .layerMaxXMinYCorner, .layerMaxXMaxYCorner
        ]
        if group.count > 1 {
            let f = panel.frame
            let t: CGFloat = 2
            for other in group where other !== panel {
                let of = other.frame
                if abs(f.maxX - of.minX) < t { mask.remove([.layerMaxXMinYCorner, .layerMaxXMaxYCorner]) }
                if abs(f.minX - of.maxX) < t { mask.remove([.layerMinXMinYCorner, .layerMinXMaxYCorner]) }
                if abs(f.maxY - of.minY) < t { mask.remove([.layerMinXMaxYCorner, .layerMaxXMaxYCorner]) }
                if abs(f.minY - of.maxY) < t { mask.remove([.layerMinXMinYCorner, .layerMaxXMinYCorner]) }
            }
        }
        cv.layer?.maskedCorners = mask
    }

    // Cyan accent line on the shared edge
    private func addEdgeLines(_ panel: AriPanel, group: [AriPanel]) {
        guard let cv = panel.contentView else { return }
        let f = panel.frame
        let t: CGFloat = 2

        for other in group where other !== panel {
            let of = other.frame
            var rect: NSRect?

            if abs(f.maxX - of.minX) < t {
                rect = NSRect(x: cv.bounds.maxX - 2, y: 0, width: 2, height: cv.bounds.height)
            } else if abs(f.minX - of.maxX) < t {
                rect = NSRect(x: 0, y: 0, width: 2, height: cv.bounds.height)
            } else if abs(f.maxY - of.minY) < t {
                rect = NSRect(x: 0, y: 0, width: cv.bounds.width, height: 2)
            } else if abs(f.minY - of.maxY) < t {
                rect = NSRect(x: 0, y: cv.bounds.maxY - 2, width: cv.bounds.width, height: 2)
            }

            if let r = rect {
                let line = NSView(frame: r)
                line.identifier = NSUserInterfaceItemIdentifier("snapEdge")
                line.wantsLayer = true
                line.layer?.backgroundColor = accentColor.cgColor
                cv.addSubview(line)
            }
        }
    }
}
