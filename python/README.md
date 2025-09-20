# RemBraille Python Implementation

Cross-platform Python implementation of the RemBraille communication library.

## Requirements

- Python 3.7 or higher
- No external dependencies (uses only standard library)

## Installation

```bash
# Clone the repository
git clone git@github.com:slohmaier/RemBrailleComLib.git
cd RemBrailleComLib/python

# No additional installation required - pure Python implementation
```

## Quick Start

```python
from rembraille import RemBrailleCom

# Create connection with key event handler
def handle_key_event(key_id, is_pressed):
    print(f"Key {key_id} {'pressed' if is_pressed else 'released'}")

com = RemBrailleCom(on_key_event=handle_key_event)

# Connect to host
if com.connect("192.168.1.100", 17635):
    print(f"Connected! Display has {com.get_num_cells()} cells")

    # Display some braille cells
    cells = [0x01, 0x03, 0x09, 0x19, 0x15]  # "Hello" in braille
    com.display_cells(bytes(cells))

    # Keep connection alive
    time.sleep(10)

    # Disconnect
    com.disconnect()
else:
    print("Connection failed")
```

## API Reference

### RemBrailleCom Class

#### Constructor

```python
RemBrailleCom(on_key_event=None)
```

**Parameters:**
- `on_key_event`: Callback function for key events: `(key_id: int, is_pressed: bool) -> None`

#### Methods

##### connect(host_ip, port=17635, timeout=5.0)

Connect to RemBraille host.

**Parameters:**
- `host_ip` (str): IP address of the host
- `port` (int): TCP port number (default: 17635)
- `timeout` (float): Connection timeout in seconds (default: 5.0)

**Returns:** `bool` - True if connection successful

##### disconnect()

Disconnect from RemBraille host and clean up resources.

##### display_cells(cells)

Send braille cells to display.

**Parameters:**
- `cells` (bytes): Braille cell data as bytes

**Returns:** `bool` - True if sent successfully

##### get_num_cells()

Get number of braille cells available.

**Returns:** `int` - Number of cells (0 if not connected)

##### test_connection(timeout=2.0)

Test if connection is alive by sending ping.

**Parameters:**
- `timeout` (float): Timeout for ping response (default: 2.0)

**Returns:** `bool` - True if connection is alive

#### Properties

- `connected` (bool): Current connection status
- `num_cells` (int): Number of available braille cells

## Braille Cell Encoding

Braille cells are encoded as single bytes using the standard 8-dot pattern:

```
Dot positions:     Bit positions:
  1 • • 4            0 • • 3
  2 • • 5            1 • • 4
  3 • • 6            2 • • 5
  7 • • 8            6 • • 7
```

### Common Characters

| Character | Dots | Byte Value |
|-----------|------|------------|
| A | 1 | 0x01 |
| B | 1,2 | 0x03 |
| C | 1,4 | 0x09 |
| Space | (none) | 0x00 |

## Error Handling

The library uses Python's standard logging module. Enable debug logging to see detailed protocol messages:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Common error scenarios:
- **Connection refused**: Host not reachable or server not running
- **Protocol version mismatch**: Incompatible server version
- **Network timeout**: Poor network connectivity
- **Socket errors**: Network interface issues

## Threading

The library automatically manages background threads for:
- Message receiving
- Periodic ping transmission
- Connection health monitoring

All public methods are thread-safe.

## Examples

### Basic Connection Test

```python
import time
from rembraille import RemBrailleCom

com = RemBrailleCom()
if com.connect("localhost"):
    print("Connected successfully!")
    print(f"Display has {com.get_num_cells()} cells")
    time.sleep(1)
    com.disconnect()
```

### Key Event Handling

```python
from rembraille import RemBrailleCom

def key_handler(key_id, is_pressed):
    action = "pressed" if is_pressed else "released"
    print(f"Braille key {key_id} {action}")

com = RemBrailleCom(on_key_event=key_handler)
com.connect("192.168.1.100")

# Keep running to receive key events
try:
    while com.connected:
        time.sleep(1)
except KeyboardInterrupt:
    com.disconnect()
```

### Braille Text Display

```python
from rembraille import RemBrailleCom

# Braille translation table (simplified example)
BRAILLE_MAP = {
    'a': 0x01, 'b': 0x03, 'c': 0x09, 'd': 0x19, 'e': 0x11,
    'f': 0x0B, 'g': 0x1B, 'h': 0x13, 'i': 0x0A, 'j': 0x1A,
    'k': 0x05, 'l': 0x07, 'm': 0x0D, 'n': 0x1D, 'o': 0x15,
    'p': 0x0F, 'q': 0x1F, 'r': 0x17, 's': 0x0E, 't': 0x1E,
    'u': 0x25, 'v': 0x27, 'w': 0x3A, 'x': 0x2D, 'y': 0x3D,
    'z': 0x35, ' ': 0x00
}

def text_to_braille(text):
    """Convert text to braille cell values"""
    return [BRAILLE_MAP.get(c.lower(), 0x00) for c in text]

com = RemBrailleCom()
if com.connect("192.168.1.100"):
    message = "hello world"
    cells = text_to_braille(message)
    com.display_cells(bytes(cells))
    time.sleep(5)
    com.disconnect()
```

## Testing

Use the test server to verify your implementation:

```bash
# Start test server
cd ../tools
python3 rembraille_server.py

# Run your client code to connect to localhost:17635
```

## Performance Considerations

- **Cell Updates**: Batch multiple cell updates when possible
- **Connection Pooling**: Reuse connections for multiple operations
- **Network Optimization**: Consider network latency in VM environments

## Platform-Specific Notes

### Windows

- Works with all Python versions 3.7+
- No special requirements

### macOS

- Compatible with system Python and Homebrew Python
- Test with both Intel and Apple Silicon Macs

### Linux

- Works with all major distributions
- Ensure Python 3.7+ is installed

## License

This implementation is licensed under the GNU General Public License v2.0 or later.

## Contributing

1. Follow PEP 8 coding standards
2. Add type hints for all public methods
3. Include comprehensive docstrings
4. Add unit tests for new features
5. Update this documentation for API changes