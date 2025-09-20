# RemBraille C Implementation

High-performance C implementation of the RemBraille communication library for native applications.

## Status

🚧 **Planned Implementation** - This C library is planned for future development.

## Target Platforms

- Windows (MSVC, MinGW)
- macOS (Clang)
- Linux (GCC)
- FreeBSD, OpenBSD

## Design Goals

### Performance
- Zero-copy message handling where possible
- Efficient memory management
- Minimal CPU overhead
- Lock-free data structures for high throughput

### Portability
- Standard C99 compliance
- Cross-platform socket abstraction
- Minimal external dependencies
- CMake-based build system

### Integration
- Simple C API for easy integration
- Thread-safe operations
- Callback-based event handling
- Optional C++ wrapper classes

## Planned API

### Core Functions

```c
// Library initialization
int rembraille_init(void);
void rembraille_cleanup(void);

// Connection management
typedef struct rembraille_connection rembraille_connection_t;

rembraille_connection_t* rembraille_connect(
    const char* host_ip,
    uint16_t port,
    uint32_t timeout_ms
);

void rembraille_disconnect(rembraille_connection_t* conn);
int rembraille_is_connected(rembraille_connection_t* conn);

// Display operations
int rembraille_get_cell_count(rembraille_connection_t* conn);
int rembraille_display_cells(
    rembraille_connection_t* conn,
    const uint8_t* cells,
    size_t cell_count
);

// Key event handling
typedef void (*rembraille_key_callback_t)(
    uint32_t key_id,
    int is_pressed,
    void* user_data
);

int rembraille_set_key_callback(
    rembraille_connection_t* conn,
    rembraille_key_callback_t callback,
    void* user_data
);

// Connection testing
int rembraille_test_connection(
    rembraille_connection_t* conn,
    uint32_t timeout_ms
);
```

### Error Handling

```c
typedef enum {
    REMBRAILLE_OK = 0,
    REMBRAILLE_ERROR_INVALID_PARAM = -1,
    REMBRAILLE_ERROR_NETWORK = -2,
    REMBRAILLE_ERROR_PROTOCOL = -3,
    REMBRAILLE_ERROR_TIMEOUT = -4,
    REMBRAILLE_ERROR_MEMORY = -5,
    REMBRAILLE_ERROR_NOT_CONNECTED = -6
} rembraille_error_t;

const char* rembraille_error_string(rembraille_error_t error);
```

## Build System

### CMake Configuration

```cmake
# Minimum CMake version
cmake_minimum_required(VERSION 3.10)

project(rembraille-c VERSION 1.0.0)

# Options
option(REMBRAILLE_BUILD_TESTS "Build unit tests" ON)
option(REMBRAILLE_BUILD_EXAMPLES "Build example programs" ON)
option(REMBRAILLE_ENABLE_LOGGING "Enable debug logging" OFF)

# Find dependencies
find_package(Threads REQUIRED)

# Library target
add_library(rembraille
    src/rembraille.c
    src/protocol.c
    src/network.c
    src/utils.c
)

target_include_directories(rembraille PUBLIC include)
target_link_libraries(rembraille Threads::Threads)
```

### Dependencies

**Required:**
- Standard C library
- POSIX threads (pthreads) or Windows threads
- Socket libraries (Winsock2 on Windows)

**Optional:**
- OpenSSL (for future TLS support)
- Valgrind (for memory debugging)
- CUnit or Unity (for unit testing)

## Directory Structure

```
c/
├── CMakeLists.txt          # Build configuration
├── README.md               # This file
├── include/
│   └── rembraille/
│       ├── rembraille.h    # Main API header
│       ├── protocol.h      # Protocol definitions
│       └── types.h         # Common types
├── src/
│   ├── rembraille.c        # Main implementation
│   ├── protocol.c          # Protocol handling
│   ├── network.c           # Network operations
│   ├── platform/
│   │   ├── windows.c       # Windows-specific code
│   │   ├── posix.c         # POSIX-specific code
│   │   └── macos.c         # macOS-specific code
│   └── utils.c             # Utility functions
├── tests/
│   ├── test_protocol.c     # Protocol tests
│   ├── test_network.c      # Network tests
│   └── test_integration.c  # Integration tests
├── examples/
│   ├── simple_client.c     # Basic usage example
│   ├── key_handler.c       # Key event example
│   └── performance_test.c  # Performance benchmark
└── docs/
    ├── API.md              # Detailed API documentation
    └── PORTING.md          # Porting guide
```

## Example Usage

### Basic Client

```c
#include <rembraille/rembraille.h>
#include <stdio.h>
#include <unistd.h>

void key_event_handler(uint32_t key_id, int is_pressed, void* user_data) {
    printf("Key %u %s\n", key_id, is_pressed ? "pressed" : "released");
}

int main() {
    // Initialize library
    if (rembraille_init() != REMBRAILLE_OK) {
        fprintf(stderr, "Failed to initialize RemBraille\n");
        return 1;
    }

    // Connect to host
    rembraille_connection_t* conn = rembraille_connect("192.168.1.100", 17635, 5000);
    if (!conn) {
        fprintf(stderr, "Connection failed\n");
        rembraille_cleanup();
        return 1;
    }

    // Set up key event handler
    rembraille_set_key_callback(conn, key_event_handler, NULL);

    // Get display information
    int cell_count = rembraille_get_cell_count(conn);
    printf("Connected to display with %d cells\n", cell_count);

    // Display some braille
    uint8_t cells[] = {0x01, 0x03, 0x09, 0x19, 0x15}; // "Hello"
    rembraille_display_cells(conn, cells, sizeof(cells));

    // Keep running
    sleep(10);

    // Cleanup
    rembraille_disconnect(conn);
    rembraille_cleanup();
    return 0;
}
```

### Build and Run

```bash
mkdir build
cd build
cmake ..
make
./examples/simple_client
```

## Implementation Priority

1. **Core Protocol** - Message serialization/deserialization
2. **Network Layer** - Cross-platform socket abstraction
3. **Connection Management** - Connect, disconnect, reconnect logic
4. **Threading** - Background message handling
5. **API Layer** - Public C interface
6. **Error Handling** - Comprehensive error reporting
7. **Testing** - Unit and integration tests
8. **Documentation** - API docs and examples
9. **Performance Optimization** - Memory pools, zero-copy
10. **Platform Support** - Windows, macOS, Linux testing

## Integration Examples

### NVDA Addon (C Extension)

```c
// Python C extension wrapper
PyObject* py_rembraille_connect(PyObject* self, PyObject* args) {
    const char* host_ip;
    int port = 17635;

    if (!PyArg_ParseTuple(args, "s|i", &host_ip, &port)) {
        return NULL;
    }

    rembraille_connection_t* conn = rembraille_connect(host_ip, port, 5000);
    return PyCapsule_New(conn, "rembraille_connection", NULL);
}
```

### Windows Application

```c
// Windows GUI application
DWORD WINAPI message_thread(LPVOID param) {
    rembraille_connection_t* conn = (rembraille_connection_t*)param;

    while (rembraille_is_connected(conn)) {
        // Process messages
        Sleep(10);
    }

    return 0;
}
```

## Future Enhancements

- **TLS Support**: Encrypted connections
- **Compression**: Zlib compression for large displays
- **Authentication**: User/password authentication
- **Multiple Displays**: Support for multiple braille displays
- **Hot Reload**: Dynamic library reloading
- **Metrics**: Performance and usage metrics

## Contributing

Contributions are welcome! Please ensure:

1. **Code Style**: Follow Linux kernel coding style
2. **Testing**: Add unit tests for new features
3. **Documentation**: Update API documentation
4. **Portability**: Test on multiple platforms
5. **Memory Safety**: Use Valgrind for memory checking

## License

Licensed under GNU General Public License v2.0 or later.

---

**Implementation Status**: Planned
**Target Date**: Q2 2025
**Contact**: Stefan Lohmaier