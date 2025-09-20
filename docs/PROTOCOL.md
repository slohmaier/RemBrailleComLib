# RemBraille Communication Protocol

Version 1.0 - Last Updated: January 2025

## Overview

The RemBraille protocol enables TCP/IP communication between braille display clients (typically running in virtual machines) and host systems that control physical braille displays. This protocol allows NVDA screen reader users in VMs to access braille displays connected to their host system.

## Protocol Design

### Transport Layer

- **Protocol**: TCP/IP
- **Default Port**: 17635
- **Connection Model**: Client-server with persistent connections
- **Encoding**: Binary protocol with network byte order (big-endian)

### Message Format

All messages follow a consistent 4-byte header format:

```
+--------+--------+--------+--------+--------//--------+
| VER(1) | TYPE(1)| LENGTH(2)      | DATA(variable)   |
+--------+--------+--------+--------+--------//--------+
 0        1        2        4        4+LENGTH
```

#### Header Fields

- **VER (1 byte)**: Protocol version (currently 1)
- **TYPE (1 byte)**: Message type identifier
- **LENGTH (2 bytes)**: Length of data payload in bytes (network byte order)
- **DATA (variable)**: Message payload (LENGTH bytes)

### Message Types

| Type | Value | Name | Direction | Description |
|------|-------|------|-----------|-------------|
| 0x01 | MSG_HANDSHAKE | Handshake | Client → Server | Initial connection negotiation |
| 0x02 | MSG_HANDSHAKE_RESP | Handshake Response | Server → Client | Connection acknowledgment |
| 0x10 | MSG_DISPLAY_CELLS | Display Cells | Client → Server | Braille cell data for display |
| 0x20 | MSG_KEY_EVENT | Key Event | Server → Client | Physical key press/release |
| 0x30 | MSG_NUM_CELLS_REQ | Cell Count Request | Client → Server | Request display cell count |
| 0x31 | MSG_NUM_CELLS_RESP | Cell Count Response | Server → Client | Display cell count |
| 0x40 | MSG_PING | Ping | Bidirectional | Keepalive/connectivity test |
| 0x41 | MSG_PONG | Pong | Bidirectional | Ping response |
| 0xFF | MSG_ERROR | Error | Bidirectional | Error message |

## Connection Establishment

### 1. TCP Connection

The client initiates a TCP connection to the server on port 17635 (or configured port).

### 2. Handshake Sequence

```
Client                                Server
  |                                     |
  | MSG_HANDSHAKE                      |
  |   "RemBraille_Guest"               |
  |------------------------------------>|
  |                                     |
  |              MSG_HANDSHAKE_RESP     |
  |              + cell_count (2 bytes) |
  |<------------------------------------|
  |                                     |
```

#### MSG_HANDSHAKE (0x01)

**Direction**: Client → Server
**Data**: UTF-8 string identifying the client (e.g., "RemBraille_Guest")

#### MSG_HANDSHAKE_RESP (0x02)

**Direction**: Server → Client
**Data**:
- Server identification string (variable length)
- **Optional**: 2-byte cell count (network byte order) at the beginning

If the response contains 2 or more bytes, the first 2 bytes are interpreted as the number of available braille cells.

## Core Operations

### Cell Count Query

```
Client                                Server
  |                                     |
  | MSG_NUM_CELLS_REQ                  |
  |------------------------------------>|
  |                                     |
  |              MSG_NUM_CELLS_RESP     |
  |              cell_count (2 bytes)   |
  |<------------------------------------|
  |                                     |
```

#### MSG_NUM_CELLS_REQ (0x30)

**Direction**: Client → Server
**Data**: Empty (LENGTH = 0)

#### MSG_NUM_CELLS_RESP (0x31)

**Direction**: Server → Client
**Data**: 2-byte unsigned integer (network byte order) representing the number of braille cells

### Braille Display Update

#### MSG_DISPLAY_CELLS (0x10)

**Direction**: Client → Server
**Data**: Array of braille cell values (1 byte per cell)

Each byte represents one braille cell using the standard 8-dot braille pattern:

```
Dot positions:     Bit positions:
  1 • • 4            0 • • 3
  2 • • 5            1 • • 4
  3 • • 6            2 • • 5
  7 • • 8            6 • • 7
```

**Example**: The letter 'A' (dots 1) = 0x01

### Key Events

#### MSG_KEY_EVENT (0x20)

**Direction**: Server → Client
**Data**:
- **key_id** (4 bytes): Key identifier (network byte order)
- **event_type** (1 byte): Event type (1 = press, 2 = release)

Key Event Types:
- `KEY_DOWN = 0x01`: Key press
- `KEY_UP = 0x02`: Key release

**Key ID Mapping**: Key identifiers are implementation-specific and should be documented by the braille display driver.

## Keepalive and Health Monitoring

### Ping/Pong Mechanism

```
Sender                               Receiver
  |                                     |
  | MSG_PING                           |
  |   timestamp (8 bytes, optional)    |
  |------------------------------------>|
  |                                     |
  |                        MSG_PONG     |
  |        timestamp (8 bytes, optional)|
  |<------------------------------------|
  |                                     |
```

#### MSG_PING (0x40)

**Direction**: Bidirectional
**Data**: Optional 8-byte timestamp (milliseconds since Unix epoch, network byte order)

#### MSG_PONG (0x41)

**Direction**: Response to MSG_PING
**Data**: Echo of the ping timestamp (if provided)

### Recommended Keepalive Behavior

- Send ping every 10-30 seconds during idle periods
- Timeout connection if no pong received within 5-10 seconds
- Implement exponential backoff for reconnection attempts

## Error Handling

### MSG_ERROR (0xFF)

**Direction**: Bidirectional
**Data**: UTF-8 error message string

**Common Error Conditions**:
- Protocol version mismatch
- Malformed message
- Unsupported message type
- Connection timeout
- Hardware failure

### Connection Recovery

Clients should implement automatic reconnection with:
- Initial retry after 1-3 seconds
- Exponential backoff (max 60 seconds)
- Full handshake on reconnection
- Re-query cell count after reconnection

## Implementation Guidelines

### Threading Considerations

Implementations should use separate threads for:
- Message receiving (blocking reads)
- Message sending (with queue)
- Periodic ping transmission
- UI updates (if applicable)

### Buffer Management

- Implement proper message framing
- Handle partial message receives
- Validate message length before processing
- Implement reasonable message size limits (e.g., 64KB)

### Security Considerations

- Validate all incoming data lengths
- Sanitize text data for display
- Implement connection timeouts
- Consider authentication for production use

### Performance Optimization

- Batch braille cell updates when possible
- Implement delta compression for large displays
- Use efficient serialization
- Monitor network latency and adapt ping frequency

## Protocol Extensions

Future protocol versions may include:

- **Authentication**: User/password or certificate-based auth
- **Compression**: Gzip or custom compression for large displays
- **Multiple Displays**: Support for multiple braille displays
- **Audio Feedback**: Synchronized audio cues
- **Cursor Routing**: Advanced cursor positioning

## Example Implementation

### Python Client Example

```python
import socket
import struct

def send_handshake(sock):
    # Send handshake
    data = b"RemBraille_Guest"
    header = struct.pack("!BBH", 1, 0x01, len(data))
    sock.sendall(header + data)

    # Receive response
    header = sock.recv(4)
    version, msg_type, length = struct.unpack("!BBH", header)
    response_data = sock.recv(length) if length > 0 else b""

    if msg_type == 0x02:  # MSG_HANDSHAKE_RESP
        if len(response_data) >= 2:
            cell_count = struct.unpack("!H", response_data[:2])[0]
            return cell_count
    return None

def display_cells(sock, cells):
    data = bytes(cells)
    header = struct.pack("!BBH", 1, 0x10, len(data))
    sock.sendall(header + data)
```

## References

- [Unicode Braille Patterns](https://en.wikipedia.org/wiki/Braille_Patterns)
- [NVDA Braille Display Framework](https://github.com/nvaccess/nvda)
- [TCP Socket Programming Best Practices](https://tools.ietf.org/html/rfc793)

---

**Document Version**: 1.0
**Protocol Version**: 1
**Last Updated**: January 2025
**Authors**: Stefan Lohmaier