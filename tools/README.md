# RemBraille Tools

Development and testing tools for the RemBraille communication library.

## rembraille_server.py

A test server for RemBraille development that simulates a braille display host.

### Features

- **Cross-platform**: Works on Windows, macOS, and Linux
- **Real-time display**: Shows braille cells sent from NVDA in both Unicode braille and ASCII
- **Interactive commands**: Control server during runtime
- **Connection monitoring**: Tracks client connections and message statistics
- **Unicode fallback**: Displays ASCII alternatives if Unicode isn't supported

### Usage

```bash
# Start with defaults (port 17635, 40 cells)
python3 rembraille_server.py

# Custom port and cell count
python3 rembraille_server.py --port 12345 --cells 80

# Verbose mode for detailed output
python3 rembraille_server.py --verbose
```

### Interactive Commands

While the server is running, you can use these commands:

- `s` + Enter: Refresh statistics display
- `k` + Enter: Send test key event to connected clients
- `q` + Enter: Quit server
- `h` + Enter: Show help

### Testing with NVDA

1. Start the test server on your host system
2. Configure NVDA to connect to your host IP and port 17635
3. Select "RemBraille (VM Host Connection)" as braille display in NVDA
4. Observe braille output in the server console as you navigate in NVDA

### Protocol Support

The server implements the complete RemBraille protocol:

- Handshake negotiation
- Cell count queries
- Braille cell display updates
- Key event simulation
- Ping/pong keepalive
- Error handling

### Output Example

```
+=======================================================================+
|              RemBraille Test Server - Live Monitor                   |
+=======================================================================+

Recent Messages:
------------------------------------------------------------------------
[14:32:15] Server started on port 17635
[14:32:22] 192.168.1.100:52341 -> HANDSHAKE
  Handshake: RemBraille_Guest
[14:32:22] 192.168.1.100:52341 -> NUM_CELLS_REQ
  Sent cell count: 40
[14:32:23] 192.168.1.100:52341 -> DISPLAY_CELLS
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

Commands: [s]tats [k]ey test [q]uit [h]elp
```