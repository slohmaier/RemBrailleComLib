# RemBraille Test Suite

Comprehensive testing framework for the RemBraille communication protocol, server implementation, and client functionality.

## Overview

This test suite provides complete coverage for the RemBraille ecosystem:

- **Unit Tests**: Protocol message encoding/decoding
- **Integration Tests**: Server-client communication, receiver testing, driver testing
- **Test Fixtures**: Reusable test server and client implementations

## Directory Structure

```
tests/
├── README.md                          # This file
├── run_tests.py                       # Test runner script
├── __init__.py                        # Test package init
│
├── unit/                              # Unit tests
│   ├── __init__.py
│   └── test_protocol.py              # Protocol message tests
│
├── integration/                       # Integration tests
│   ├── __init__.py
│   ├── test_server_client.py         # Server-client tests
│   ├── test_receiver.py              # Receiver (macOS) tests
│   └── test_driver.py                # Driver (NVDA) tests
│
└── fixtures/                          # Test fixtures
    ├── __init__.py
    ├── test_server.py                # Test server implementation
    └── test_client.py                # Test client implementation
```

## Quick Start

### Running All Tests

```bash
cd RemBrailleComLib/tests
python3 run_tests.py
```

### Running Specific Test Types

```bash
# Unit tests only
python3 run_tests.py --type unit

# Integration tests only
python3 run_tests.py --type integration

# Server-client tests
python3 run_tests.py --type server-client

# Receiver tests (requires RemBrailleReceiver running)
python3 run_tests.py --type receiver

# Driver tests (requires NVDA with RemBraille Driver)
python3 run_tests.py --type driver
```

### Running with Verbose Output

```bash
# Verbose
python3 run_tests.py -v

# Extra verbose
python3 run_tests.py -vv
```

## Test Categories

### 1. Unit Tests

**Location**: `unit/test_protocol.py`

**Purpose**: Test protocol message encoding and decoding

**Coverage**:
- Message serialization and deserialization
- All protocol message types (handshake, display cells, key events, ping/pong, errors)
- Braille encoding patterns (6-dot and 8-dot)
- Error handling (insufficient data, protocol version mismatches)

**Run**:
```bash
python3 run_tests.py --type unit
```

**No Prerequisites**: These tests are self-contained and require no external services.

### 2. Server-Client Integration Tests

**Location**: `integration/test_server_client.py`

**Purpose**: Test full protocol flow between server and client

**Coverage**:
- Connection and handshake
- Braille cell transmission
- Key event handling
- Multiple cell updates
- Ping/pong mechanism
- Concurrent operations
- Reconnection handling
- Error scenarios

**Run**:
```bash
python3 run_tests.py --type server-client
```

**No Prerequisites**: Uses test fixtures for both server and client.

### 3. Receiver Integration Tests

**Location**: `integration/test_receiver.py`

**Purpose**: Test the RemBrailleReceiver macOS application

**Coverage**:
- Connection to receiver
- Handshake with receiver
- Sending braille cells to receiver
- Multiple connections
- Cell count queries
- Sustained connections
- Rapid updates
- Error handling

**Prerequisites**:
1. Build and start the RemBrailleReceiver:
   ```bash
   cd /Users/stefan/git/RemBrailleReceiver/macos
   swift build -c release
   ./.build/release/RemBrailleReceiver
   ```

2. Run the tests:
   ```bash
   cd RemBrailleComLib/tests
   python3 run_tests.py --type receiver
   ```

**Note**: The receiver must be running on localhost:17635 before running these tests.

### 4. Driver Integration Tests

**Location**: `integration/test_driver.py`

**Purpose**: Test the RemBraille NVDA driver add-on

**Coverage**:
- Driver connection to server
- Driver handshake
- Driver sending braille output
- Multiple cell updates from driver
- Key event handling
- Protocol compliance

**Prerequisites**:
1. **Windows OS** with NVDA installed
2. **RemBraille Driver** add-on installed in NVDA
3. Configure the driver to connect to `localhost:17635`

4. Run the tests:
   ```bash
   cd RemBrailleComLib\tests
   python test_driver.py
   ```

**Note**: These tests act as a server and wait for the NVDA driver to connect. Some tests require manual interaction with NVDA.

**Standalone Tests**: The driver tests also include standalone tests that verify the test server functionality without requiring NVDA.

## Test Fixtures

### Test Server (`fixtures/test_server.py`)

A complete, controllable RemBraille server implementation for testing.

**Features**:
- Full protocol implementation
- Thread-safe operation
- Callbacks for test verification (`on_cells_received`, `on_client_connected`, etc.)
- Test controls (simulate delays, protocol errors)
- State tracking (received messages, current cells)
- Helper methods (`wait_for_connection`, `wait_for_cells`, `send_key_event`)

**Usage**:
```python
from fixtures.test_server import TestRemBrailleServer

server = TestRemBrailleServer(cell_count=40, port=17635)
server.on_cells_received = lambda cells: print(f"Received: {cells.hex()}")

server.start()
# ... run tests ...
server.stop()
```

**Standalone Mode**:
```bash
python3 -m tests.fixtures.test_server
```

### Test Client (`fixtures/test_client.py`)

A complete, controllable RemBraille client implementation for testing.

**Features**:
- Full protocol implementation
- Thread-safe operation
- Callbacks for test verification (`on_handshake_response`, `on_key_event`, etc.)
- State tracking (received messages, key events)
- Helper methods (`wait_for_handshake_response`, `wait_for_key_event`)

**Usage**:
```python
from fixtures.test_client import TestRemBrailleClient

client = TestRemBrailleClient(client_id="RemBraille_Test")
client.on_handshake_response = lambda count, name: print(f"Connected to {name}")

client.connect('127.0.0.1', 17635)
client.send_handshake()
client.send_display_cells(b"\x01\x02\x03")
client.disconnect()
```

**Standalone Mode**:
```bash
python3 -m tests.fixtures.test_client
```

## Test Runner Options

```bash
python3 run_tests.py [OPTIONS]

Options:
  --type, -t TYPE       Test type: unit, integration, server-client,
                        receiver, driver, all (default: all)
  --pattern, -p PATTERN Test file pattern (default: test*.py)
  --verbose, -v         Verbose output (use -vv for extra verbose)
  --failfast, -f        Stop on first failure
  --no-color            Disable colored output
  --help, -h            Show help message
```

### Examples

```bash
# Run all tests with verbose output
python3 run_tests.py -v

# Run only protocol tests
python3 run_tests.py --pattern test_protocol.py

# Run server-client tests, stop on first failure
python3 run_tests.py --type server-client --failfast

# Run receiver tests with extra verbose output
python3 run_tests.py --type receiver -vv
```

## Protocol Overview

The RemBraille protocol is a binary TCP/IP protocol for transmitting braille display data between VMs and host systems.

### Message Format

All messages follow this format:

```
┌─────────┬─────────┬─────────┬──────────────┐
│ Version │  Type   │ Length  │   Payload    │
│ (1 byte)│(1 byte) │(2 bytes)│ (N bytes)    │
└─────────┴─────────┴─────────┴──────────────┘
```

- **Version**: Protocol version (currently 1)
- **Type**: Message type (see below)
- **Length**: Payload length in bytes (network byte order)
- **Payload**: Message-specific data

### Message Types

| Type | Value | Direction | Description |
|------|-------|-----------|-------------|
| `MSG_HANDSHAKE` | 0x01 | Client → Server | Initial handshake with client ID |
| `MSG_HANDSHAKE_RESP` | 0x02 | Server → Client | Handshake response with cell count and server name |
| `MSG_DISPLAY_CELLS` | 0x10 | Client → Server | Braille cell data to display |
| `MSG_KEY_EVENT` | 0x20 | Server → Client | Braille display key press/release |
| `MSG_NUM_CELLS_REQ` | 0x30 | Client → Server | Request cell count |
| `MSG_NUM_CELLS_RESP` | 0x31 | Server → Client | Cell count response |
| `MSG_PING` | 0x40 | Bidirectional | Ping message (with optional timestamp) |
| `MSG_PONG` | 0x41 | Bidirectional | Pong response |
| `MSG_ERROR` | 0xFF | Server → Client | Error message with text |

### Connection Flow

```
Client                                Server
  │                                     │
  ├──── TCP Connect ───────────────────>│
  │                                     │
  ├──── MSG_HANDSHAKE ─────────────────>│
  │     (client_id: "RemBraille_Guest") │
  │                                     │
  │<──── MSG_HANDSHAKE_RESP ────────────┤
  │     (cell_count: 40, name: "Host")  │
  │                                     │
  ├──── MSG_DISPLAY_CELLS ─────────────>│
  │     (cells: [0x01, 0x03, 0x09...])  │
  │                                     │
  │<──── MSG_KEY_EVENT ─────────────────┤
  │     (key_id: 42, pressed: true)     │
  │                                     │
  ├──── MSG_PING ──────────────────────>│
  │                                     │
  │<──── MSG_PONG ──────────────────────┤
  │                                     │
```

## Development

### Adding New Tests

1. **Unit tests**: Add to `unit/test_protocol.py` or create new test file
2. **Integration tests**: Add to appropriate integration test file
3. **New fixtures**: Add to `fixtures/` directory

### Test Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*` (e.g., `TestProtocolMessages`)
- Test methods: `test_*` (e.g., `test_handshake_message`)

### Running Individual Tests

```bash
# Run specific test file
python3 -m unittest unit.test_protocol

# Run specific test class
python3 -m unittest unit.test_protocol.TestProtocolMessages

# Run specific test method
python3 -m unittest unit.test_protocol.TestProtocolMessages.test_handshake_message
```

## Continuous Integration

The test suite is designed to be CI-friendly:

```bash
# CI command (fails on first error, no color output)
python3 run_tests.py --type unit --failfast --no-color
```

For integration tests in CI:
- Server-client tests can run without prerequisites
- Receiver tests require the app to be built and running
- Driver tests require Windows and NVDA setup

## Troubleshooting

### "RemBrailleReceiver is not running"

**Problem**: Receiver integration tests can't connect.

**Solution**: Start the receiver before running tests:
```bash
cd /Users/stefan/git/RemBrailleReceiver/macos
./.build/release/RemBrailleReceiver
```

### "Address already in use"

**Problem**: Test server can't bind to port.

**Solution**:
- Kill any process using the port: `lsof -ti:17635 | xargs kill`
- Or use a different port in the test

### "NVDA driver did not connect"

**Problem**: Driver tests timeout waiting for NVDA.

**Solution**:
- Ensure NVDA is running
- Enable the RemBraille driver in NVDA
- Configure driver to connect to `localhost:17635`
- Check Windows firewall settings

### Import Errors

**Problem**: `ModuleNotFoundError` when running tests.

**Solution**: Run from the `tests/` directory:
```bash
cd RemBrailleComLib/tests
python3 run_tests.py
```

## Performance

Expected test execution times:

- **Unit tests**: < 1 second
- **Server-client tests**: ~10-15 seconds
- **Receiver tests**: ~20-30 seconds (with receiver running)
- **Driver tests**: ~60+ seconds (with manual interaction)

## Coverage

To measure test coverage:

```bash
# Install coverage tool
pip3 install coverage

# Run with coverage
coverage run run_tests.py --type unit
coverage report
coverage html  # Generate HTML report
```

## Contributing

When adding new features to RemBraille:

1. Add unit tests for protocol changes
2. Add integration tests for new functionality
3. Update this README with new test descriptions
4. Run full test suite before committing

## License

This test suite is part of the RemBraille project and follows the same license.

## Support

For issues with the test suite:
- Check this README first
- Review test output and error messages
- Check that prerequisites are met
- Report issues to the RemBraille project repository

---

**Last Updated**: 2025-10-22
**Test Suite Version**: 1.0.0
