// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "AriApp",
    platforms: [.macOS(.v13)],
    dependencies: [
        .package(url: "https://github.com/MrKai77/DynamicNotchKit", from: "1.1.0"),
    ],
    targets: [
        .executableTarget(
            name: "AriApp",
            dependencies: ["DynamicNotchKit"],
            path: "Sources/AriApp",
            resources: [.copy("orb.html"), .copy("memory_graph.html")]
        ),
    ]
)
