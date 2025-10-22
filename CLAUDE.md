# CLAUDE.md - RemBrailleComLib

This file provides guidance to Claude Code when working with the RemBrailleComLib test suite.

## Overview

RemBrailleComLib contains the RemBraille protocol specification and a comprehensive test suite for validating both the protocol implementation and the RemBraille ecosystem components.

## Test Suite

### Location
`tests/` directory contains the complete test infrastructure.

### Structure
```
tests/
├── README.md                  # Comprehensive test documentation
├── run_tests.py              # Test runner with colored output
├── unit/                     # Protocol unit tests
│   └── test_protocol.py      # Message encoding/decoding tests
├── integration/              # Integration tests
│   ├── test_server_client.py    # Server-client communication tests
│   ├── test_receiver.py         # RemBrailleReceiver (macOS) tests
│   └── test_driver.py           # RemBrailleDriver (NVDA) tests
└── fixtures/                 # Test fixtures
    ├── test_server.py        # Controllable test server
    └── test_client.py        # Controllable test client
```

### Running Tests

#### Quick Start
```bash
cd tests
python3 run_tests.py              # Run all tests
python3 run_tests.py --type unit  # Unit tests only
python3 run_tests.py -v           # Verbose output
```

#### Test Types
- **unit**: Protocol message encoding/decoding tests (16 tests)
- **integration**: All integration tests
- **server-client**: Server-client communication tests (12 tests)
- **receiver**: RemBrailleReceiver macOS app tests (11 tests, requires app running)
- **driver**: RemBrailleDriver NVDA tests (requires Windows/NVDA)

#### Testing RemBrailleReceiver

To test the macOS receiver application:

```bash
# Terminal 1: Start the receiver
cd /Users/stefan/git/RemBrailleReceiver/macos
./.build/release/RemBrailleReceiver

# Terminal 2: Run receiver tests
cd /Users/stefan/git/RemBrailleReceiver/RemBrailleComLib/tests
python3 run_tests.py --type receiver -v
```

Expected results:
- 11/11 tests passing
- Validates protocol compliance
- Tests connection, handshake, cell transmission
- Performance: ~187K+ updates/second

#### Testing RemBrailleDriver

To test the NVDA driver (Windows only):

```bash
# Start test server (acts as RemBrailleReceiver)
cd RemBrailleComLib/tests
python3 -m fixtures.test_server

# In NVDA: Enable RemBraille driver, connect to localhost:17635
# Then run driver tests
python3 run_tests.py --type driver
```

### Test Fixtures

#### TestRemBrailleServer
A controllable server implementation for testing clients.

**Usage:**
```python
from fixtures.test_server import TestRemBrailleServer

server = TestRemBrailleServer(cell_count=40, port=17635)
server.on_cells_received = lambda cells: print(f"Received: {cells.hex()}")
server.start()

# Run tests...

server.stop()
```

**Features:**
- Full protocol implementation
- Callbacks for test verification
- State tracking (received messages, current cells)
- Helper methods (wait_for_connection, wait_for_cells)
- Can simulate delays and errors

#### TestRemBrailleClient
A controllable client implementation for testing servers.

**Usage:**
```python
from fixtures.test_client import TestRemBrailleClient

client = TestRemBrailleClient(client_id="TestClient")
client.on_handshake_response = lambda count, name: print(f"Connected to {name}")

client.connect('127.0.0.1', 17635)
client.send_handshake()
client.send_display_cells(b"\x01\x02\x03")
client.disconnect()
```

**Features:**
- Full protocol implementation
- Callbacks for test verification
- State tracking (received key events, messages)
- Helper methods (wait_for_handshake_response, wait_for_key_event)

### Protocol Specification

#### Message Format
All messages use this header format:
```
[version:1][type:1][length:2][data:variable]
```

- **version**: Protocol version (currently 1)
- **type**: Message type (see below)
- **length**: Payload length in bytes (big-endian)
- **data**: Message-specific payload

#### Message Types
| Type | Value | Direction | Description |
|------|-------|-----------|-------------|
| MSG_HANDSHAKE | 0x01 | Client → Server | Initial handshake with client ID |
| MSG_HANDSHAKE_RESP | 0x02 | Server → Client | Response with cell count + server name |
| MSG_DISPLAY_CELLS | 0x10 | Client → Server | Braille cell data to display |
| MSG_KEY_EVENT | 0x20 | Server → Client | Key press/release from braille display |
| MSG_NUM_CELLS_REQ | 0x30 | Client → Server | Request cell count |
| MSG_NUM_CELLS_RESP | 0x31 | Server → Client | Cell count response |
| MSG_PING | 0x40 | Bidirectional | Ping (with optional timestamp) |
| MSG_PONG | 0x41 | Bidirectional | Pong response |
| MSG_ERROR | 0xFF | Server → Client | Error message with text |

#### Handshake Flow
```
Client                          Server
  |                               |
  |─── MSG_HANDSHAKE ────────────>|
  |    (client_id: string)        |
  |                               |
  |<── MSG_HANDSHAKE_RESP ────────|
  |    (cell_count:2 + name)      |
  |                               |
```

### Development Workflow

#### Adding New Tests

1. **Unit tests**: Add to `unit/test_protocol.py`
2. **Integration tests**: Add to appropriate integration file
3. **New fixtures**: Add to `fixtures/` directory

#### Running Specific Tests

```bash
# Run specific test file
python3 -m unittest unit.test_protocol

# Run specific test class
python3 -m unittest unit.test_protocol.TestProtocolMessages

# Run specific test method
python3 -m unittest unit.test_protocol.TestProtocolMessages.test_handshake_message
```

#### Test Coverage

```bash
# Install coverage
pip3 install coverage

# Run with coverage
coverage run run_tests.py --type unit
coverage report
coverage html  # Generate HTML report
```

### Continuous Integration

For CI environments:

```bash
# Run unit tests only (no external dependencies)
python3 run_tests.py --type unit --failfast --no-color

# Run server-client integration tests
python3 run_tests.py --type server-client --no-color
```

### Common Issues

#### "RemBrailleReceiver is not running"
Start the receiver before running receiver tests:
```bash
cd /Users/stefan/git/RemBrailleReceiver/macos
./.build/release/RemBrailleReceiver
```

#### "Address already in use"
Kill process using the port:
```bash
lsof -ti:17635 | xargs kill
```

#### Import Errors
Always run from the `tests/` directory:
```bash
cd RemBrailleComLib/tests
python3 run_tests.py
```

## Protocol Implementation Guidelines

When implementing RemBraille protocol support:

1. **Always include protocol version byte** in message header
2. **Use big-endian byte order** for multi-byte values
3. **Send cell count + server name** in handshake response
4. **Handle all message types** gracefully (unknown types should not crash)
5. **Implement ping/pong** for connection monitoring
6. **Support empty payloads** (length = 0)

## Related Documentation

- **Test Suite README**: `tests/README.md` - Comprehensive test documentation
- **Main Project**: `../CLAUDE.md` - RemBrailleReceiver project guidance
- **Protocol Spec**: See `tests/README.md` Protocol Overview section

## Testing Best Practices

1. **Run tests before committing** protocol changes
2. **Add tests for new message types** or protocol features
3. **Test both success and error cases**
4. **Use test fixtures** for consistent test data
5. **Document test requirements** in docstrings

## Test Results

Expected test results (as of 2025-10-22):
- Unit tests: 16/16 passing
- Server-client tests: 12/12 passing
- Receiver tests: 11/11 passing (with receiver running)
- **Total: 39/39 passing**

## Support

For test-related issues:
1. Check `tests/README.md` first
2. Verify prerequisites are met
3. Review test output for specific errors
4. Check that protocol version matches (currently 1)
