// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "AriApp",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "AriApp",
            path: "Sources/AriApp",
            resources: [.copy("orb.html")]
        ),
    ]
)
