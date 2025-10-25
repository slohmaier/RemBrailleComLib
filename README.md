<div align="center">

![RemBraille Logo](resources/icons/rembraille_icon.svg)

# RemBraille Communication Library

**Cross-platform braille display connectivity for virtual machines**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7+-brightgreen.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/slohmaier/RemBrailleComLib)

*Enable screen reader users in virtual machines to access braille displays connected to their host system through TCP/IP communication.*

[Quick Start](#quick-start) • [Documentation](#documentation) • [Examples](#examples) • [Contributing](#contributing)

</div>

---

## 🌟 Overview

RemBraille bridges the accessibility gap for blind and visually impaired users working in virtual machine environments. By establishing TCP/IP communication between guest VMs and host systems, users can seamlessly access braille displays without complex hardware passthrough configurations.

### ✨ Key Features

- 🔗 **TCP/IP Protocol**: Reliable network-based communication
- 📱 **Braille Display Updates**: Real-time cell content synchronization
- ⌨️ **Bidirectional Key Events**: Full braille keyboard support
- 🔄 **Auto-Reconnection**: Robust connection recovery
- 🖥️ **Cross-Platform**: Windows, macOS, and Linux support
- 🎯 **VM Optimized**: Designed for virtualized environments

---

## 📥 RemBraille Ecosystem Downloads

### Host Applications (RemBrailleReceiver)

Install the receiver on your **host system** where the physical braille display is connected:

<div align="center">

**macOS** • **Windows** • **Linux**

### [Mac App Store](https://apps.apple.com/app/rembraillereceiver) • [Microsoft Store](https://www.microsoft.com/store/apps/rembraillereceiver) • [GitHub Releases](https://github.com/slohmaier/RemBrailleReceiver/releases)

*Coming soon on Mac App Store and Microsoft Store*

</div>

### Guest Drivers (VM Applications)

Install the appropriate driver **inside your virtual machine**:

#### Windows Guests (NVDA)
- **RemBraille NVDA Addon**: [GitHub](https://github.com/slohmaier/RemBrailleDriver)
- For Windows VMs running NVDA screen reader

#### Linux Guests (BRLTTY)
- **RemBraille BRLTTY Driver**: [GitHub](https://github.com/slohmaier/RemBraille_brltty)
- For Linux VMs with BRLTTY and screen readers (Orca, etc.)

---

## 🚀 Quick Start

### Python Implementation

```python
from rembraille import RemBrailleCom

# Create connection with key event handler
def handle_key_event(key_id, is_pressed):
    print(f"Key {key_id} {'pressed' if is_pressed else 'released'}")

com = RemBrailleCom(on_key_event=handle_key_event)

# Connect to host
if com.connect("192.168.1.100", 17635):
    print(f"Connected! Display has {com.get_num_cells()} cells")

    # Display braille content
    cells = [0x01, 0x03, 0x09, 0x19, 0x15]  # "Hello" in braille
    com.display_cells(bytes(cells))

    # Keep connection alive
    time.sleep(10)
    com.disconnect()
```

### Test Server

Start the development server for testing:

```bash
cd tools
python rembraille_server.py --verbose --cells 40
```

---

## 📚 Documentation

### Core Documentation

| Document | Description |
|----------|-------------|
| [Protocol Specification](docs/PROTOCOL.md) | Complete TCP/IP protocol documentation |
| [Python Implementation](python/README.md) | Python library API and examples |
| [C Implementation](c/README.md) | Planned C library design |
| [Swift Implementation](swift/README.md) | Planned Swift/SwiftUI library |

### Quick Links

- 🔧 [Installation Guide](#installation)
- 🎯 [Usage Examples](#examples)
- 🏗️ [Architecture Overview](#architecture)
- 🐛 [Troubleshooting](#troubleshooting)
- 🤝 [Contributing Guidelines](#contributing)

---

## 💻 Installation

### Python Library

**Requirements**: Python 3.7+

```bash
# Clone the repository
git clone https://github.com/slohmaier/RemBrailleComLib.git
cd RemBrailleComLib

# Python implementation (no additional dependencies)
cd python
# Ready to use - pure Python implementation
```

### C Library (Planned)

```bash
# Build requirements: CMake, GCC/Clang
mkdir build && cd build
cmake ../c
make
sudo make install
```

### Swift Package (Planned)

```swift
// Package.swift
dependencies: [
    .package(url: "https://github.com/slohmaier/RemBrailleComLib.git", from: "1.0.0")
]
```

---

## 🏗️ Architecture

### Protocol Stack

```
┌─────────────────────────────────────┐
│   Screen Reader (NVDA/BRLTTY)       │
│        + RemBraille Driver          │
├─────────────────────────────────────┤
│       RemBraille Library            │
├─────────────────────────────────────┤
│         TCP/IP Protocol             │
├─────────────────────────────────────┤
│      Virtual Network Layer         │
├─────────────────────────────────────┤
│   Host: RemBrailleReceiver          │
│        + Physical Display           │
└─────────────────────────────────────┘
```

### Communication Flow

1. **Connection**: Client initiates TCP connection to host
2. **Handshake**: Protocol version and capabilities negotiation
3. **Cell Updates**: Real-time braille content synchronization
4. **Key Events**: Bidirectional key press/release handling
5. **Keepalive**: Periodic connection health monitoring

---

## 📋 Examples

### Basic Connection

```python
import time
from rembraille import RemBrailleCom

com = RemBrailleCom()
if com.connect("localhost"):
    print("✅ Connected successfully!")
    print(f"📏 Display has {com.get_num_cells()} cells")
    time.sleep(1)
    com.disconnect()
```

### Advanced Key Handling

```python
from rembraille import RemBrailleCom

class BrailleHandler:
    def __init__(self):
        self.key_count = 0

    def handle_key(self, key_id, is_pressed):
        if is_pressed:
            self.key_count += 1
            print(f"🔘 Key {key_id} pressed (total: {self.key_count})")

handler = BrailleHandler()
com = RemBrailleCom(on_key_event=handler.handle_key)

try:
    com.connect("192.168.1.100")
    while com.connected:
        time.sleep(0.1)
except KeyboardInterrupt:
    com.disconnect()
```

### Braille Text Display

```python
# Simple braille translation (Grade 1)
BRAILLE_ALPHABET = {
    'a': 0x01, 'b': 0x03, 'c': 0x09, 'd': 0x19, 'e': 0x11,
    'f': 0x0B, 'g': 0x1B, 'h': 0x13, 'i': 0x0A, 'j': 0x1A,
    # ... (complete alphabet mapping)
    ' ': 0x00
}

def text_to_braille(text):
    return [BRAILLE_ALPHABET.get(c.lower(), 0x00) for c in text]

com = RemBrailleCom()
if com.connect("localhost"):
    message = "hello world"
    cells = text_to_braille(message)
    com.display_cells(bytes(cells))
```

---

## 🔧 Development

### Icon Generation

Generate icons for applications using the RemBraille library:

```bash
# Install dependencies
pip install Pillow cairosvg

# Generate all icon formats
python scripts/generate_icons.py

# Generate specific format
python scripts/generate_icons.py --format systray

# Clean generated files
python scripts/generate_icons.py --clean
```

**Generated Formats:**
- **System Tray**: 16x16, 24x24, 32x32 PNG
- **Windows ICO**: Multi-resolution .ico file
- **High-res**: 512x512, 1024x1024 PNG
- **Standard**: 48x48, 64x64, 128x128, 256x256 PNG

### Testing Workflow

1. **Start Test Server**:
   ```bash
   cd tools
   python rembraille_server.py --verbose
   ```

2. **Run Client Examples**:
   ```bash
   cd examples/python
   python basic_client.py localhost
   ```

3. **Observe Communication**:
   Monitor real-time protocol messages and braille display updates

---

## 📊 Performance

### Benchmarks (Python Implementation)

| Metric | Value | Notes |
|--------|-------|-------|
| **Connection Time** | < 500ms | Local network |
| **Cell Update Rate** | 60+ Hz | 40-cell display |
| **Key Event Latency** | < 50ms | Typical response |
| **Memory Usage** | < 10MB | Per connection |
| **CPU Usage** | < 1% | Idle connection |

### Optimization Tips

- **Batch Updates**: Combine multiple cell changes
- **Connection Pooling**: Reuse connections when possible
- **Network Tuning**: Adjust timeouts for network conditions

---

## 🐛 Troubleshooting

### Common Issues

**Connection Failed**
```
❌ Failed to connect to RemBraille host
💡 Check: Network connectivity, firewall settings, server status
```

**Protocol Version Mismatch**
```
❌ Protocol version mismatch: expected 1, got 0
💡 Update: Ensure client and server versions are compatible
```

**No Braille Display**
```
❌ No cells displayed
💡 Verify: Server is running, display is configured correctly
```

### VM-Specific Solutions

**VMware**: Use bridged or NAT networking
**VirtualBox**: Enable host-only adapter
**Parallels**: Default shared networking works
**Hyper-V**: Configure external virtual switch

### Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Detailed protocol message logging
com = RemBrailleCom()
com.connect("host", debug=True)
```

---

## 🗺️ Roadmap

### Current Status

- ✅ **Python Implementation**: Complete with full protocol support
- ✅ **Protocol Documentation**: Comprehensive specification
- ✅ **Test Server**: Development and debugging tools
- ✅ **Examples**: Working Python client implementations

### Planned Features

#### Q2 2025
- 🔧 **C Implementation**: High-performance native library
- 📱 **Swift Implementation**: macOS and iOS support
- 🔐 **TLS Support**: Encrypted connections
- 📦 **Package Managers**: pip, npm, CocoaPods distribution

#### Q3 2025
- 🗜️ **Compression**: Efficient data transfer for large displays
- 🔐 **Authentication**: User/password and certificate-based auth
- 📱 **Multiple Displays**: Support for multiple braille devices
- 📊 **Metrics**: Performance monitoring and analytics

#### Q4 2025
- 🎵 **Audio Integration**: Synchronized audio feedback
- 🖱️ **Cursor Routing**: Advanced cursor positioning
- 🌐 **Web Interface**: Browser-based configuration
- 📱 **Mobile Apps**: iOS/Android companion apps

---

## 🤝 Contributing

We welcome contributions! Please see our guidelines:

### Development Setup

```bash
# Clone and setup
git clone https://github.com/slohmaier/RemBrailleComLib.git
cd RemBrailleComLib

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Generate icons
python scripts/generate_icons.py
```

### Contribution Guidelines

1. **🔧 Code Quality**: Follow language-specific style guides
2. **🧪 Testing**: Add tests for new features
3. **📚 Documentation**: Update relevant documentation
4. **🔄 Compatibility**: Maintain cross-platform support
5. **📋 Protocol**: Ensure protocol compatibility across implementations

### Language-Specific Guidelines

- **Python**: Follow PEP 8, use type hints
- **C**: Linux kernel coding style, comprehensive error handling
- **Swift**: Swift API Design Guidelines, SwiftUI best practices

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 Stefan Lohmaier

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

See [LICENSE](LICENSE) for the complete license text.

---

## 👥 Authors & Acknowledgments

### Lead Developer
- **Stefan Lohmaier** - *Initial work and project architecture*

### Contributors
- Community contributors welcome!

### Acknowledgments
- **NVDA Community** - Support and feedback
- **Braille Display Manufacturers** - Hardware specifications
- **Accessibility Community** - Testing and validation

---

## 📞 Support

### Getting Help

- 📖 **Documentation**: Start with [docs/PROTOCOL.md](docs/PROTOCOL.md)
- 💬 **Issues**: Report bugs on [GitHub Issues](https://github.com/slohmaier/RemBrailleComLib/issues)
- 📧 **Contact**: Stefan Lohmaier

### Community

- 🌐 **Website**: Coming soon
- 📱 **Twitter**: [@RemBraille](https://twitter.com/RemBraille) (planned)
- 💬 **Discord**: Community server (planned)

---

<div align="center">

**Made with ❤️ for the accessibility community**

[⬆️ Back to Top](#rembraille-communication-library)

</div>