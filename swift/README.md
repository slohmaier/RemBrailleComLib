# RemBraille Swift Implementation

Modern Swift implementation of the RemBraille communication library for macOS and iOS applications.

## Status

🚧 **Planned Implementation** - This Swift library is planned for future development.

## Target Platforms

- **macOS**: 10.15 (Catalina) and later
- **iOS**: 13.0 and later (for VoiceOver integration)
- **iPadOS**: 13.0 and later
- **watchOS**: 6.0 and later (future consideration)

## Design Goals

### Swift-First Design
- Modern Swift concurrency (async/await)
- SwiftUI integration
- Combine framework support
- Swift Package Manager distribution

### Performance
- Efficient memory management with ARC
- Concurrent message processing
- Network optimization for mobile
- Battery-conscious design

### Apple Ecosystem Integration
- VoiceOver accessibility framework integration
- Network framework for optimal connectivity
- SwiftUI reactive UI components
- Xcode project templates

## Planned API

### Core Classes

```swift
import Foundation
import Network

// Main connection class
@MainActor
public class RemBrailleConnection: ObservableObject {
    @Published public private(set) var isConnected = false
    @Published public private(set) var cellCount = 0
    @Published public private(set) var connectionStatus: ConnectionStatus = .disconnected

    public init(keyEventHandler: KeyEventHandler? = nil)

    public func connect(to host: String, port: UInt16 = 17635) async throws
    public func disconnect() async
    public func displayCells(_ cells: [UInt8]) async throws
    public func testConnection() async throws -> Bool
}

// Connection status
public enum ConnectionStatus {
    case disconnected
    case connecting
    case connected
    case reconnecting
    case failed(Error)
}

// Key event handling
public protocol KeyEventHandler {
    func keyPressed(_ keyID: UInt32)
    func keyReleased(_ keyID: UInt32)
}

// Error types
public enum RemBrailleError: Error, LocalizedError {
    case connectionFailed
    case protocolError
    case networkTimeout
    case invalidData
    case notConnected

    public var errorDescription: String? {
        switch self {
        case .connectionFailed: return "Failed to connect to RemBraille host"
        case .protocolError: return "Protocol communication error"
        case .networkTimeout: return "Network operation timed out"
        case .invalidData: return "Invalid data received"
        case .notConnected: return "Not connected to host"
        }
    }
}
```

### SwiftUI Integration

```swift
import SwiftUI
import Combine

// SwiftUI view for connection management
public struct RemBrailleConnectionView: View {
    @StateObject private var connection = RemBrailleConnection()
    @State private var hostIP = "192.168.1.100"
    @State private var port: UInt16 = 17635

    public var body: some View {
        VStack(spacing: 20) {
            ConnectionStatusView(status: connection.connectionStatus)

            VStack {
                TextField("Host IP", text: $hostIP)
                    .textFieldStyle(RoundedBorderTextFieldStyle())

                HStack {
                    Text("Port:")
                    TextField("Port", value: $port, format: .number)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                }
            }

            HStack {
                Button("Connect") {
                    Task {
                        try await connection.connect(to: hostIP, port: port)
                    }
                }
                .disabled(connection.isConnected)

                Button("Disconnect") {
                    Task {
                        await connection.disconnect()
                    }
                }
                .disabled(!connection.isConnected)
            }

            if connection.isConnected {
                Text("Display: \(connection.cellCount) cells")
                    .foregroundColor(.secondary)
            }
        }
        .padding()
    }
}

// Connection status indicator
struct ConnectionStatusView: View {
    let status: ConnectionStatus

    var body: some View {
        HStack {
            Circle()
                .fill(statusColor)
                .frame(width: 12, height: 12)
            Text(statusText)
                .font(.caption)
        }
    }

    private var statusColor: Color {
        switch status {
        case .connected: return .green
        case .connecting, .reconnecting: return .yellow
        case .disconnected: return .gray
        case .failed: return .red
        }
    }

    private var statusText: String {
        switch status {
        case .connected: return "Connected"
        case .connecting: return "Connecting..."
        case .reconnecting: return "Reconnecting..."
        case .disconnected: return "Disconnected"
        case .failed(let error): return "Error: \(error.localizedDescription)"
        }
    }
}
```

### Combine Publishers

```swift
import Combine

extension RemBrailleConnection {
    // Publisher for key events
    public var keyEventPublisher: AnyPublisher<KeyEvent, Never> {
        keyEventSubject.eraseToAnyPublisher()
    }

    // Publisher for connection state changes
    public var connectionStatePublisher: AnyPublisher<ConnectionStatus, Never> {
        $connectionStatus.eraseToAnyPublisher()
    }

    // Publisher for braille cell updates
    public var cellUpdatePublisher: AnyPublisher<[UInt8], Never> {
        cellUpdateSubject.eraseToAnyPublisher()
    }
}

public struct KeyEvent {
    public let keyID: UInt32
    public let isPressed: Bool
    public let timestamp: Date
}
```

## Package Structure

```
swift/
├── Package.swift                    # Swift Package Manager manifest
├── README.md                       # This file
├── Sources/
│   └── RemBraille/
│       ├── RemBrailleConnection.swift    # Main connection class
│       ├── Protocol/
│       │   ├── Message.swift            # Protocol message types
│       │   ├── MessageType.swift        # Message type definitions
│       │   └── ProtocolEncoder.swift    # Message encoding/decoding
│       ├── Network/
│       │   ├── TCPConnection.swift      # TCP network handling
│       │   └── NetworkMonitor.swift     # Network state monitoring
│       ├── SwiftUI/
│       │   ├── ConnectionView.swift     # SwiftUI connection UI
│       │   ├── StatusView.swift         # Status indicator views
│       │   └── BrailleDisplayView.swift # Braille display simulator
│       └── Utils/
│           ├── BrailleUtils.swift       # Braille encoding utilities
│           └── Logger.swift             # Logging utilities
├── Tests/
│   └── RemBrailleTests/
│       ├── ConnectionTests.swift        # Connection unit tests
│       ├── ProtocolTests.swift          # Protocol tests
│       └── MockServer.swift             # Test server implementation
├── Examples/
│   ├── macOS-Example/                   # macOS example app
│   │   ├── ContentView.swift
│   │   └── App.swift
│   └── iOS-Example/                     # iOS example app
│       ├── ContentView.swift
│       └── App.swift
└── Documentation/
    ├── API.md                          # Generated API docs
    └── Integration.md                  # Integration guide
```

## Swift Package Manager

### Package.swift

```swift
// swift-tools-version: 5.7
import PackageDescription

let package = Package(
    name: "RemBraille",
    platforms: [
        .macOS(.v10_15),
        .iOS(.v13),
        .iPadOS(.v13),
        .watchOS(.v6)
    ],
    products: [
        .library(
            name: "RemBraille",
            targets: ["RemBraille"]
        ),
    ],
    dependencies: [
        // No external dependencies - pure Swift implementation
    ],
    targets: [
        .target(
            name: "RemBraille",
            dependencies: []
        ),
        .testTarget(
            name: "RemBrailleTests",
            dependencies: ["RemBraille"]
        ),
    ]
)
```

### Installation

```swift
// Add to Package.swift dependencies
.package(url: "https://github.com/slohmaier/RemBrailleComLib.git", from: "1.0.0")

// Add to target dependencies
.target(
    name: "YourTarget",
    dependencies: [
        .product(name: "RemBraille", package: "RemBrailleComLib")
    ]
)
```

## Example Usage

### Basic Connection (macOS)

```swift
import RemBraille
import SwiftUI

@main
struct RemBrailleApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    @StateObject private var connection = RemBrailleConnection()

    var body: some View {
        VStack {
            RemBrailleConnectionView()

            if connection.isConnected {
                BrailleTestView(connection: connection)
            }
        }
        .padding()
    }
}

struct BrailleTestView: View {
    let connection: RemBrailleConnection
    @State private var message = "Hello World"

    var body: some View {
        VStack {
            TextField("Message", text: $message)
                .textFieldStyle(RoundedBorderTextFieldStyle())

            Button("Send to Braille") {
                Task {
                    let cells = BrailleUtils.textToBraille(message)
                    try await connection.displayCells(cells)
                }
            }
        }
    }
}
```

### Key Event Handling

```swift
class BrailleKeyHandler: KeyEventHandler {
    func keyPressed(_ keyID: UInt32) {
        print("Braille key \(keyID) pressed")
        // Handle key press
    }

    func keyReleased(_ keyID: UInt32) {
        print("Braille key \(keyID) released")
        // Handle key release
    }
}

// Usage
let keyHandler = BrailleKeyHandler()
let connection = RemBrailleConnection(keyEventHandler: keyHandler)
```

### Combine Integration

```swift
import Combine

class BrailleViewModel: ObservableObject {
    @Published var connectionStatus: ConnectionStatus = .disconnected
    @Published var lastKeyEvent: KeyEvent?

    private var cancellables = Set<AnyCancellable>()
    private let connection = RemBrailleConnection()

    init() {
        // Subscribe to connection status
        connection.connectionStatePublisher
            .assign(to: \.connectionStatus, on: self)
            .store(in: &cancellables)

        // Subscribe to key events
        connection.keyEventPublisher
            .assign(to: \.lastKeyEvent, on: self)
            .store(in: &cancellables)
    }
}
```

## iOS Integration

### VoiceOver Integration

```swift
import UIKit
import AccessibilityKit

class BrailleAccessibilityManager: NSObject {
    private let connection = RemBrailleConnection()

    func setupAccessibilityIntegration() {
        // Monitor VoiceOver braille output
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(brailleOutputChanged),
            name: UIAccessibility.announcementDidFinishNotification,
            object: nil
        )
    }

    @objc private func brailleOutputChanged(_ notification: Notification) {
        // Convert VoiceOver braille to RemBraille format
        Task {
            if let brailleText = extractBrailleText(from: notification) {
                let cells = BrailleUtils.textToBraille(brailleText)
                try await connection.displayCells(cells)
            }
        }
    }
}
```

## Testing

### Unit Tests

```swift
import XCTest
@testable import RemBraille

final class RemBrailleTests: XCTestCase {
    func testConnectionCreation() {
        let connection = RemBrailleConnection()
        XCTAssertFalse(connection.isConnected)
        XCTAssertEqual(connection.cellCount, 0)
    }

    func testProtocolEncoding() async {
        let message = HandshakeMessage(clientInfo: "Test_Client")
        let encoded = try ProtocolEncoder.encode(message)
        XCTAssertGreaterThan(encoded.count, 4)
    }

    func testMockConnection() async {
        let mockServer = MockRemBrailleServer()
        await mockServer.start()

        let connection = RemBrailleConnection()
        try await connection.connect(to: "localhost", port: mockServer.port)

        XCTAssertTrue(connection.isConnected)

        await mockServer.stop()
    }
}
```

## Performance Considerations

### Memory Management
- Use weak references to prevent retain cycles
- Implement efficient buffer management for large displays
- Minimize object allocations in hot paths

### Network Optimization
- Use Network framework for optimal performance
- Implement adaptive timeouts based on network conditions
- Support background processing for iOS apps

### Battery Efficiency
- Use timer coalescing for periodic operations
- Implement intelligent connection management
- Optimize for iOS background execution

## Integration Examples

### macOS Menu Bar App

```swift
import SwiftUI
import AppKit

@main
struct MenuBarApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        Settings {
            SettingsView()
        }
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem?
    private let connection = RemBrailleConnection()

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupMenuBar()
    }

    private func setupMenuBar() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem?.button?.title = "RemBraille"

        let menu = NSMenu()
        menu.addItem(NSMenuItem(title: "Connect", action: #selector(connect), keyEquivalent: ""))
        menu.addItem(NSMenuItem(title: "Disconnect", action: #selector(disconnect), keyEquivalent: ""))
        statusItem?.menu = menu
    }

    @objc private func connect() {
        Task {
            try await connection.connect(to: "localhost")
        }
    }

    @objc private func disconnect() {
        Task {
            await connection.disconnect()
        }
    }
}
```

## Future Enhancements

- **Accessibility Inspector Integration**: Deep VoiceOver integration
- **Braille Translation**: Full UEB (Unified English Braille) support
- **Multiple Displays**: Support for multiple braille displays
- **iCloud Sync**: Sync settings across devices
- **Shortcuts Integration**: Siri Shortcuts for common actions
- **Widget Support**: iOS/macOS widgets for status monitoring

## Contributing

1. **Swift Style**: Follow Swift API Design Guidelines
2. **Documentation**: Use DocC for documentation
3. **Testing**: Maintain high test coverage
4. **Accessibility**: Ensure full VoiceOver compatibility
5. **Performance**: Profile and optimize for mobile usage

## License

Licensed under GNU General Public License v2.0 or later.

---

**Implementation Status**: Planned
**Target Date**: Q3 2025
**Platform Priority**: macOS first, then iOS
**Contact**: Stefan Lohmaier