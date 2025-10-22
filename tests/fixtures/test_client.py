"""
Test RemBraille Client Implementation

A minimal, testable client implementation for unit and integration testing.
"""

import socket
import struct
import threading
import time
from typing import Optional, Callable, List, Tuple


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


class TestRemBrailleClient:
    """
    Test client implementation for RemBraille protocol

    Features:
    - Connects to RemBraille server
    - Handles protocol messages correctly
    - Thread-safe
    - Controllable for testing
    - Can simulate various scenarios
    """

    def __init__(self, client_id: str = "TestClient"):
        self.client_id = client_id
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.running = False
        self.receive_thread: Optional[threading.Thread] = None

        # State tracking
        self.server_cell_count: Optional[int] = None
        self.server_name: Optional[str] = None
        self.received_key_events: List[Tuple[int, bool]] = []
        self.received_messages: List[tuple] = []
        self.last_error: Optional[str] = None

        # Callbacks for testing
        self.on_connected: Optional[Callable] = None
        self.on_handshake_response: Optional[Callable[[int, str], None]] = None
        self.on_key_event: Optional[Callable[[int, bool], None]] = None
        self.on_message_received: Optional[Callable[[int, bytes], None]] = None
        self.on_disconnected: Optional[Callable] = None
        self.on_error: Optional[Callable[[str], None]] = None

        # Test controls
        self.simulate_delay = 0.0

    def connect(self, host: str = "127.0.0.1", port: int = 17635, timeout: float = 5.0) -> bool:
        """Connect to RemBraille server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((host, port))
            self.socket.settimeout(None)  # Remove timeout after connection

            self.connected = True
            self.running = True

            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()

            if self.on_connected:
                self.on_connected()

            return True

        except Exception as e:
            self.last_error = f"Connection failed: {e}"
            if self.on_error:
                self.on_error(self.last_error)
            return False

    def disconnect(self):
        """Disconnect from server"""
        self.running = False
        self.connected = False

        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)

        if self.on_disconnected:
            self.on_disconnected()

    def send_handshake(self) -> bool:
        """Send handshake message to server"""
        if not self.connected:
            return False

        try:
            data = self.client_id.encode('utf-8')
            message = self._create_message(MSG_HANDSHAKE, data)
            self.socket.sendall(message)
            return True
        except Exception as e:
            self.last_error = f"Failed to send handshake: {e}"
            if self.on_error:
                self.on_error(self.last_error)
            return False

    def send_display_cells(self, cells: bytes) -> bool:
        """Send braille cell data to server"""
        if not self.connected:
            return False

        try:
            message = self._create_message(MSG_DISPLAY_CELLS, cells)
            self.socket.sendall(message)
            return True
        except Exception as e:
            self.last_error = f"Failed to send display cells: {e}"
            if self.on_error:
                self.on_error(self.last_error)
            return False

    def request_cell_count(self) -> bool:
        """Request cell count from server"""
        if not self.connected:
            return False

        try:
            message = self._create_message(MSG_NUM_CELLS_REQ)
            self.socket.sendall(message)
            return True
        except Exception as e:
            self.last_error = f"Failed to request cell count: {e}"
            if self.on_error:
                self.on_error(self.last_error)
            return False

    def send_ping(self, timestamp: Optional[int] = None) -> bool:
        """Send ping message to server"""
        if not self.connected:
            return False

        try:
            if timestamp is None:
                timestamp = int(time.time() * 1000)
            data = struct.pack("!Q", timestamp)
            message = self._create_message(MSG_PING, data)
            self.socket.sendall(message)
            return True
        except Exception as e:
            self.last_error = f"Failed to send ping: {e}"
            if self.on_error:
                self.on_error(self.last_error)
            return False

    def _receive_loop(self):
        """Receive loop for handling incoming messages"""
        try:
            while self.running and self.connected:
                # Receive message header
                header = self._recv_exact(4)
                if not header:
                    break

                # Add simulated delay if configured
                if self.simulate_delay > 0:
                    time.sleep(self.simulate_delay)

                version, msg_type, length = struct.unpack("!BBH", header)

                # Validate version
                if version != PROTOCOL_VERSION:
                    error_msg = f"Protocol version mismatch: {version}"
                    self.last_error = error_msg
                    if self.on_error:
                        self.on_error(error_msg)
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
                error_msg = f"Receive error: {e}"
                self.last_error = error_msg
                if self.on_error:
                    self.on_error(error_msg)
        finally:
            self.connected = False
            if self.on_disconnected:
                self.on_disconnected()

    def _process_message(self, msg_type: int, payload: bytes):
        """Process received message"""
        if msg_type == MSG_HANDSHAKE_RESP:
            # Extract cell count and server name
            if len(payload) >= 2:
                self.server_cell_count = struct.unpack("!H", payload[:2])[0]
                self.server_name = payload[2:].decode('utf-8', errors='ignore')

                if self.on_handshake_response:
                    self.on_handshake_response(self.server_cell_count, self.server_name)

        elif msg_type == MSG_NUM_CELLS_RESP:
            # Cell count response
            if len(payload) >= 2:
                self.server_cell_count = struct.unpack("!H", payload)[0]

        elif msg_type == MSG_KEY_EVENT:
            # Key event from server
            if len(payload) >= 5:
                key_id, event_type = struct.unpack("!IB", payload)
                is_pressed = (event_type == KEY_DOWN)
                self.received_key_events.append((key_id, is_pressed))

                if self.on_key_event:
                    self.on_key_event(key_id, is_pressed)

        elif msg_type == MSG_PONG:
            # Pong response (for timing measurements)
            pass

        elif msg_type == MSG_PING:
            # Server initiated ping - respond with pong
            try:
                pong = self._create_message(MSG_PONG, payload)
                self.socket.sendall(pong)
            except:
                pass

        elif msg_type == MSG_ERROR:
            # Error message from server
            error_text = payload.decode('utf-8', errors='ignore')
            self.last_error = error_text
            if self.on_error:
                self.on_error(error_text)

    def _recv_exact(self, num_bytes: int) -> Optional[bytes]:
        """Receive exact number of bytes"""
        data = b""
        while len(data) < num_bytes:
            chunk = self.socket.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _create_message(self, msg_type: int, data: bytes = b"") -> bytes:
        """Create a protocol message"""
        header = struct.pack("!BBH", PROTOCOL_VERSION, msg_type, len(data))
        return header + data

    def wait_for_handshake_response(self, timeout: float = 5.0) -> bool:
        """Wait for handshake response from server"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.server_cell_count is not None:
                return True
            time.sleep(0.1)
        return False

    def wait_for_key_event(self, timeout: float = 5.0) -> Optional[Tuple[int, bool]]:
        """Wait for a key event from server"""
        initial_count = len(self.received_key_events)
        start_time = time.time()
        while time.time() - start_time < timeout:
            if len(self.received_key_events) > initial_count:
                return self.received_key_events[-1]
            time.sleep(0.1)
        return None

    def get_received_message_count(self, msg_type: Optional[int] = None) -> int:
        """Get count of received messages of a specific type"""
        if msg_type is None:
            return len(self.received_messages)
        return sum(1 for mt, _ in self.received_messages if mt == msg_type)

    def clear_state(self):
        """Clear all state (for reuse in tests)"""
        self.server_cell_count = None
        self.server_name = None
        self.received_key_events.clear()
        self.received_messages.clear()
        self.last_error = None


if __name__ == '__main__':
    # Simple test
    client = TestRemBrailleClient(client_id="RemBraille_Guest")

    def on_handshake(cell_count, server_name):
        print(f"Connected to {server_name} with {cell_count} cells")

    def on_key_event(key_id, is_pressed):
        print(f"Key event: {key_id} {'pressed' if is_pressed else 'released'}")

    client.on_handshake_response = on_handshake
    client.on_key_event = on_key_event

    if client.connect('127.0.0.1', 17635):
        print("Connected to server")

        # Send handshake
        client.send_handshake()

        # Wait for handshake response
        if client.wait_for_handshake_response():
            print(f"Server has {client.server_cell_count} cells")

            # Send some braille cells
            cells = bytes([0x01, 0x03, 0x09, 0x19, 0x15])  # "Hello" in braille
            client.send_display_cells(cells)
            print(f"Sent {len(cells)} braille cells")

            # Keep running for key events
            try:
                print("Press Ctrl+C to stop...")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping...")
        else:
            print("No handshake response received")

        client.disconnect()
    else:
        print(f"Failed to connect: {client.last_error}")
