import AppKit

final class SnapManager {
    static let shared = SnapManager()

    private var groups:        [[AriPanel]]                  = []
    private var lastPositions: [ObjectIdentifier: NSPoint]   = [:]
    private var isMovingGroup  = false
    private let snapThreshold: CGFloat = 14
    private let accentColor    = NSColor(red: 0, green: 0.85, blue: 1, alpha: 0.7)

    // MARK: - Registration

    func register(_ panels: [AriPanel]) {
        groups = panels.map { [$0] }
        for p in panels {
            lastPositions[ObjectIdentifier(p)] = p.frame.origin
            NotificationCenter.default.addObserver(
                self,
                selector: #selector(panelDidMove(_:)),
                name: NSWindow.didMoveNotification,
                object: p
            )
        }
    }

    // MARK: - Move sync

    @objc private func panelDidMove(_ note: Notification) {
        guard !isMovingGroup, let moved = note.object as? AriPanel else { return }
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

    // MARK: - Snap detection

    private func checkSnap(movedGroup: [AriPanel]) {
        for panel in movedGroup {
            for group in groups where !group.contains(where: { $0 === panel }) {
                for other in group {
                    if let neo = snapOrigin(panel, to: other) {
                        isMovingGroup = true
                        panel.setFrameOrigin(neo)
                        lastPositions[ObjectIdentifier(panel)] = neo
                        isMovingGroup = false
                        mergeGroups(containing: panel, and: other)
                        updateVisuals()
                        return
                    }
                }
            }
        }
        updateVisuals()
    }

    // Returns the snapped origin for `a` relative to `b`, or nil if too far
    private func snapOrigin(_ a: AriPanel, to b: AriPanel) -> NSPoint? {
        let af = a.frame
        let bf = b.frame
        let t  = snapThreshold

        // Require at least 20px of shared edge to avoid false snaps on corners
        let vOverlap = min(af.maxY, bf.maxY) - max(af.minY, bf.minY) > 20
        let hOverlap = min(af.maxX, bf.maxX) - max(af.minX, bf.minX) > 20

        if vOverlap && abs(af.maxX - bf.minX) < t { return NSPoint(x: bf.minX - af.width, y: af.minY) }
        if vOverlap && abs(af.minX - bf.maxX) < t { return NSPoint(x: bf.maxX,             y: af.minY) }
        if hOverlap && abs(af.maxY - bf.minY) < t { return NSPoint(x: af.minX, y: bf.minY - af.height) }
        if hOverlap && abs(af.minY - bf.maxY) < t { return NSPoint(x: af.minX, y: bf.maxY) }
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
