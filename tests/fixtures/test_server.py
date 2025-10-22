"""
Test RemBraille Server Implementation

A minimal, testable server implementation for unit and integration testing.
"""

import socket
import struct
import threading
import time
from typing import Optional, Callable, List


# Protocol constants
PROTOCOL_VERSION = 1
MSG_HANDSHAKE = 0x01
MSG_HANDSHAKE_RESP = 0x02
MSG_DISPLAY_CELLS = 0x10
MSG_KEY_EVENT = 0x20
MSG_NUM_CELLS_REQ = 0x30
MSG_NUM_CELLS_RESP = 0x31
MSG_PING = 0x40
MSG_PONG = 0x41
MSG_ERROR = 0xFF

KEY_DOWN = 0x01
KEY_UP = 0x02


class TestRemBrailleServer:
    """
    Test server implementation for RemBraille protocol

    Features:
    - Handles protocol messages correctly
    - Thread-safe
    - Controllable for testing
    - Can simulate various scenarios (errors, delays, etc.)
    """

    def __init__(self, cell_count: int = 40, port: int = 17635):
        self.cell_count = cell_count
        self.port = port
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.server_thread: Optional[threading.Thread] = None

        # State tracking
        self.current_cells: Optional[bytes] = None
        self.received_messages: List[tuple] = []
        self.connected_client: Optional[str] = None

        # Callbacks for testing
        self.on_client_connected: Optional[Callable] = None
        self.on_cells_received: Optional[Callable[[bytes], None]] = None
        self.on_message_received: Optional[Callable[[int, bytes], None]] = None

        # Test controls
        self.simulate_delay = 0.0
        self.simulate_protocol_error = False

    def start(self) -> bool:
        """Start the test server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('127.0.0.1', self.port))
            self.server_socket.listen(1)
            self.server_socket.settimeout(0.5)  # For responsive shutdown

            self.running = True
            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()

            return True
        except Exception as e:
            print(f"Failed to start server: {e}")
            return False

    def stop(self):
        """Stop the test server"""
        self.running = False

        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None

        if self.server_thread:
            self.server_thread.join(timeout=2.0)

    def send_key_event(self, key_id: int, is_pressed: bool) -> bool:
        """Send a key event to the connected client"""
        if not self.client_socket:
            return False

        try:
            event_type = KEY_DOWN if is_pressed else KEY_UP
            data = struct.pack("!IB", key_id, event_type)
            message = self._create_message(MSG_KEY_EVENT, data)
            self.client_socket.sendall(message)
            return True
        except Exception as e:
            print(f"Failed to send key event: {e}")
            return False

    def _server_loop(self):
        """Main server loop"""
        while self.running:
            try:
                # Accept connection
                self.client_socket, addr = self.server_socket.accept()
                self.connected_client = addr[0]

                if self.on_client_connected:
                    self.on_client_connected(addr)

                # Handle client
                self._handle_client()

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Server error: {e}")
                break

    def _handle_client(self):
        """Handle a connected client"""
        try:
            while self.running and self.client_socket:
                # Receive message header
                header = self._recv_exact(4)
                if not header:
                    break

                # Add simulated delay if configured
                if self.simulate_delay > 0:
                    time.sleep(self.simulate_delay)

                version, msg_type, length = struct.unpack("!BBH", header)

                # Validate version
                if version != PROTOCOL_VERSION and not self.simulate_protocol_error:
                    error_msg = f"Protocol version mismatch: {version}"
                    self._send_error(error_msg)
                    continue

                # Receive payload
                payload = self._recv_exact(length) if length > 0 else b""

                # Track received message
                self.received_messages.append((msg_type, payload))

                if self.on_message_received:
                    self.on_message_received(msg_type, payload)

                # Process message
                self._process_message(msg_type, payload)

        except Exception as e:
            if self.running:
                print(f"Client handler error: {e}")

        finally:
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
            self.connected_client = None

    def _process_message(self, msg_type: int, payload: bytes):
        """Process received message"""
        if msg_type == MSG_HANDSHAKE:
            # Send handshake response with cell count
            client_id = payload.decode('utf-8', errors='ignore')
            response_data = struct.pack("!H", self.cell_count) + b"TestServer"
            response = self._create_message(MSG_HANDSHAKE_RESP, response_data)
            self.client_socket.sendall(response)

        elif msg_type == MSG_NUM_CELLS_REQ:
            # Send cell count
            cell_data = struct.pack("!H", self.cell_count)
            response = self._create_message(MSG_NUM_CELLS_RESP, cell_data)
            self.client_socket.sendall(response)

        elif msg_type == MSG_DISPLAY_CELLS:
            # Store received cells
            self.current_cells = payload

            if self.on_cells_received:
                self.on_cells_received(payload)

        elif msg_type == MSG_PING:
            # Echo ping as pong
            response = self._create_message(MSG_PONG, payload)
            self.client_socket.sendall(response)

        elif msg_type == MSG_PONG:
            # Pong received (for server-initiated pings)
            pass

        else:
            # Unknown message type
            error_msg = f"Unknown message type: 0x{msg_type:02X}"
            self._send_error(error_msg)

    def _recv_exact(self, num_bytes: int) -> Optional[bytes]:
        """Receive exact number of bytes"""
        data = b""
        while len(data) < num_bytes:
            chunk = self.client_socket.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _create_message(self, msg_type: int, data: bytes = b"") -> bytes:
        """Create a protocol message"""
        header = struct.pack("!BBH", PROTOCOL_VERSION, msg_type, len(data))
        return header + data

    def _send_error(self, error_text: str):
        """Send error message"""
        try:
            error_data = error_text.encode('utf-8')
            message = self._create_message(MSG_ERROR, error_data)
            self.client_socket.sendall(message)
        except:
            pass

    def wait_for_connection(self, timeout: float = 5.0) -> bool:
        """Wait for a client to connect"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.connected_client:
                return True
            time.sleep(0.1)
        return False

    def wait_for_cells(self, timeout: float = 5.0) -> Optional[bytes]:
        """Wait for braille cells to be received"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.current_cells is not None:
                return self.current_cells
            time.sleep(0.1)
        return None

    def get_received_message_count(self, msg_type: Optional[int] = None) -> int:
        """Get count of received messages of a specific type"""
        if msg_type is None:
            return len(self.received_messages)
        return sum(1 for mt, _ in self.received_messages if mt == msg_type)

    def clear_state(self):
        """Clear all state (for reuse in tests)"""
        self.current_cells = None
        self.received_messages.clear()


if __name__ == '__main__':
    # Simple test
    server = TestRemBrailleServer(cell_count=40, port=17635)

    def on_cells(cells):
        print(f"Received {len(cells)} cells: {cells.hex()}")

    server.on_cells_received = on_cells

    if server.start():
        print("Test server started on port 17635")
        print("Press Ctrl+C to stop...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            server.stop()
