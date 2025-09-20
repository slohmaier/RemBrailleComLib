# RemBraille Examples

Example implementations and usage demonstrations for the RemBraille communication library.

## Directory Structure

```
examples/
├── README.md                    # This file
├── python/
│   ├── basic_client.py         # Basic Python client example
│   ├── key_handler.py          # Key event handling example
│   └── performance_test.py     # Performance benchmarking
├── c/                          # C examples (planned)
│   ├── simple_client.c
│   ├── multi_threaded.c
│   └── performance_benchmark.c
└── swift/                      # Swift examples (planned)
    ├── macOS-Example/
    ├── iOS-Example/
    └── CLI-Example/
```

## Python Examples

### basic_client.py

Demonstrates fundamental RemBraille usage:
- Connection establishment and management
- Braille cell display operations
- Key event handling
- Error handling and cleanup

**Usage:**
```bash
cd examples/python
python basic_client.py [HOST_IP] [PORT]

# Examples:
python basic_client.py                    # Connect to localhost:17635
python basic_client.py 192.168.1.100     # Connect to specific host
python basic_client.py localhost 12345   # Connect to custom port
```

**Features:**
- Automatic braille text conversion
- Real-time key event logging
- Connection health monitoring
- Graceful error handling

### key_handler.py (planned)

Advanced key event handling example:
- Custom key mapping
- Multi-key combinations
- Key event filtering
- Input validation

### performance_test.py (planned)

Performance benchmarking utility:
- Connection latency measurement
- Throughput testing for large displays
- Memory usage monitoring
- Stress testing with multiple connections

## C Examples (Planned)

### simple_client.c

Basic C implementation demonstrating:
- C API usage patterns
- Memory management
- Error handling
- Cross-platform compatibility

### multi_threaded.c

Advanced threading example:
- Producer-consumer patterns
- Thread-safe operations
- Concurrent connections
- Resource management

### performance_benchmark.c

High-performance implementation:
- Optimized message handling
- Zero-copy operations
- Latency optimization
- Profiling integration

## Swift Examples (Planned)

### macOS-Example

Complete macOS application with:
- SwiftUI interface
- Menu bar integration
- System settings integration
- Accessibility features

### iOS-Example

iOS application demonstrating:
- VoiceOver integration
- Background processing
- Network state handling
- Battery optimization

### CLI-Example

Command-line Swift tool:
- Argument parsing
- Progress indicators
- Scripting integration
- Pipeline compatibility

## Testing with Examples

### 1. Start the Test Server

```bash
# From the tools directory
cd ../tools
python rembraille_server.py --verbose

# Or with custom settings
python rembraille_server.py --port 12345 --cells 80 --verbose
```

### 2. Run Example Client

```bash
# From the examples directory
cd python
python basic_client.py localhost 17635
```

### 3. Observe Output

**Test Server Output:**
```
+=======================================================================+
|              RemBraille Test Server - Live Monitor                   |
+=======================================================================+

Recent Messages:
------------------------------------------------------------------------
[14:32:15] Server started on port 17635
[14:32:22] 127.0.0.1:52341 -> HANDSHAKE
  Handshake: RemBraille_Guest
[14:32:22] 127.0.0.1:52341 -> DISPLAY_CELLS
  Display: 40 cells

+============================= STATISTICS ==============================+
| Port: 17635  | Cells: 40  | Uptime: 00:02:15 | Clients: 1     |
| Connections: 1    | Messages: 15     | Cells Displayed: 1240     |
+----------------------------------------------------------------------+
|                        CURRENT BRAILLE DISPLAY                       |
+----------------------------------------------------------------------+
| Braille: ⠓⠑⠇⠇⠕⠀⠺⠕⠗⠇⠙                                        |
| ASCII:   hello world                                                  |
+=======================================================================+
```

**Client Output:**
```
2025-01-20 14:32:22 - INFO - 🚀 RemBraille Python Client Example
2025-01-20 14:32:22 - INFO - 📡 Connecting to localhost:17635
2025-01-20 14:32:22 - INFO - ✅ Connected successfully!
2025-01-20 14:32:22 - INFO - 📏 Display has 40 braille cells
2025-01-20 14:32:22 - INFO - 🔗 Connection test passed
2025-01-20 14:32:22 - INFO - 📝 Displaying: 'hello world'
2025-01-20 14:32:22 - INFO - ✅ Successfully sent 40 cells
```

## Development Workflow

### 1. Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/slohmaier/RemBrailleComLib.git
cd RemBrailleComLib

# For Python development
cd python
# No additional setup required

# For C development (planned)
cd c
mkdir build && cd build
cmake .. && make

# For Swift development (planned)
cd swift
swift build
```

### 2. Running Examples

```bash
# Terminal 1: Start test server
cd tools
python rembraille_server.py --verbose

# Terminal 2: Run examples
cd examples/python
python basic_client.py
```

### 3. Modifying Examples

Examples are designed to be educational and easily modifiable:

- **Change connection parameters**: Edit host/port in example files
- **Add custom braille patterns**: Extend the braille_map dictionary
- **Implement new features**: Use examples as starting templates
- **Test error scenarios**: Modify code to test error handling

## Integration Patterns

### NVDA Addon Integration

```python
# Example pattern for NVDA addon
import braille
from .rembraille import RemBrailleCom

class RemBrailleDriver(braille.BrailleDisplayDriver):
    def __init__(self):
        super().__init__()
        self.connection = RemBrailleCom(on_key_event=self._handleKeyEvent)

    def check(self):
        return self.connection.connect(self.host, self.port)

    def display(self, cells):
        self.connection.display_cells(bytes(cells))

    def _handleKeyEvent(self, key_id, is_pressed):
        if is_pressed:
            self._handleKeyPress(key_id)
```

### GUI Application Integration

```python
# Example pattern for GUI applications
import tkinter as tk
from threading import Thread
from rembraille import RemBrailleCom

class BrailleApp:
    def __init__(self):
        self.root = tk.Tk()
        self.connection = RemBrailleCom(on_key_event=self.handle_key)
        self.setup_ui()

    def setup_ui(self):
        # Create GUI elements
        self.connect_button = tk.Button(
            self.root,
            text="Connect",
            command=self.connect
        )
        self.connect_button.pack()

    def connect(self):
        # Run connection in background thread
        Thread(target=self._connect_worker, daemon=True).start()

    def _connect_worker(self):
        if self.connection.connect("localhost"):
            self.update_status("Connected")
```

## Best Practices

### Error Handling

```python
try:
    connection = RemBrailleCom()
    if connection.connect(host, port):
        # Main application logic
        pass
    else:
        # Handle connection failure
        logger.error("Connection failed")
except Exception as e:
    # Handle unexpected errors
    logger.exception("Unexpected error: %s", e)
finally:
    # Always cleanup
    if connection.connected:
        connection.disconnect()
```

### Resource Management

```python
# Use context managers when possible
class RemBrailleContext:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connection = None

    def __enter__(self):
        self.connection = RemBrailleCom()
        if not self.connection.connect(self.host, self.port):
            raise ConnectionError("Failed to connect")
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.disconnect()

# Usage
with RemBrailleContext("localhost", 17635) as conn:
    conn.display_cells(b"Hello World")
```

### Performance Optimization

```python
# Batch updates for better performance
cells_buffer = []
for text_line in large_document:
    cells_buffer.extend(text_to_braille(text_line))

# Send in chunks
chunk_size = connection.get_num_cells()
for i in range(0, len(cells_buffer), chunk_size):
    chunk = cells_buffer[i:i+chunk_size]
    connection.display_cells(bytes(chunk))
    time.sleep(0.1)  # Small delay between updates
```

## Contributing Examples

1. **Follow existing patterns**: Use similar structure and logging
2. **Add comprehensive comments**: Explain complex logic
3. **Include error handling**: Demonstrate robust error management
4. **Test thoroughly**: Verify examples work with test server
5. **Document usage**: Update README with new examples

## License

All examples are licensed under GNU General Public License v2.0 or later.

---

**Example Status**: Python examples implemented, C and Swift planned
**Last Updated**: January 2025
**Contact**: Stefan Lohmaier