"""
Integration tests for RemBraille server and client communication

Tests the full protocol flow between server and client.
"""

import unittest
import time
import sys
import os

# Add fixtures to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'fixtures'))

from test_server import TestRemBrailleServer
from test_client import TestRemBrailleClient


class TestServerClientIntegration(unittest.TestCase):
    """Test server-client communication"""

    def setUp(self):
        """Set up server and client for each test"""
        self.server = TestRemBrailleServer(cell_count=40, port=17636)  # Use different port for testing
        self.client = TestRemBrailleClient(client_id="RemBraille_Test")

        # Start server
        self.assertTrue(self.server.start(), "Server should start successfully")
        time.sleep(0.2)  # Give server time to start

    def tearDown(self):
        """Clean up after each test"""
        if self.client.connected:
            self.client.disconnect()
        self.server.stop()
        time.sleep(0.2)  # Give server time to stop

    def test_connection_and_handshake(self):
        """Test basic connection and handshake"""
        # Connect client
        self.assertTrue(self.client.connect('127.0.0.1', 17636), "Client should connect")

        # Wait for server to accept connection
        self.assertTrue(self.server.wait_for_connection(), "Server should accept connection")

        # Send handshake
        self.assertTrue(self.client.send_handshake(), "Handshake should be sent")

        # Wait for handshake response
        self.assertTrue(self.client.wait_for_handshake_response(), "Should receive handshake response")

        # Verify handshake data
        self.assertEqual(self.client.server_cell_count, 40, "Should receive correct cell count")
        self.assertEqual(self.client.server_name, "TestServer", "Should receive server name")

    def test_display_cells_transmission(self):
        """Test sending braille cell data"""
        # Track received cells on server
        received_cells = []
        def on_cells(cells):
            received_cells.append(cells)

        self.server.on_cells_received = on_cells

        # Connect and handshake
        self.assertTrue(self.client.connect('127.0.0.1', 17636))
        self.assertTrue(self.server.wait_for_connection())
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        # Send braille cells
        test_cells = bytes([0x01, 0x03, 0x09, 0x19, 0x15])  # "Hello" in braille
        self.assertTrue(self.client.send_display_cells(test_cells))

        # Wait for server to receive
        cells = self.server.wait_for_cells(timeout=2.0)
        self.assertIsNotNone(cells, "Server should receive cells")
        self.assertEqual(cells, test_cells, "Received cells should match sent cells")

        # Verify callback was called
        self.assertEqual(len(received_cells), 1, "Callback should be called once")
        self.assertEqual(received_cells[0], test_cells)

    def test_key_event_from_server(self):
        """Test receiving key events from server"""
        # Connect and handshake
        self.assertTrue(self.client.connect('127.0.0.1', 17636))
        self.assertTrue(self.server.wait_for_connection())
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        # Server sends key press
        key_id = 42
        self.assertTrue(self.server.send_key_event(key_id, is_pressed=True))

        # Client should receive key event
        key_event = self.client.wait_for_key_event(timeout=2.0)
        self.assertIsNotNone(key_event, "Should receive key event")

        received_key_id, is_pressed = key_event
        self.assertEqual(received_key_id, key_id, "Key ID should match")
        self.assertTrue(is_pressed, "Should be key press event")

        # Server sends key release
        self.assertTrue(self.server.send_key_event(key_id, is_pressed=False))

        # Wait for release event
        time.sleep(0.1)
        self.assertEqual(len(self.client.received_key_events), 2, "Should have two key events")

        received_key_id, is_pressed = self.client.received_key_events[1]
        self.assertEqual(received_key_id, key_id)
        self.assertFalse(is_pressed, "Should be key release event")

    def test_multiple_cell_updates(self):
        """Test multiple braille cell updates"""
        # Connect and handshake
        self.assertTrue(self.client.connect('127.0.0.1', 17636))
        self.assertTrue(self.server.wait_for_connection())
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        # Send multiple cell updates
        updates = [
            bytes([0x01, 0x03, 0x09]),      # "Hello"
            bytes([0x1A, 0x15, 0x12, 0x0D]), # "World"
            bytes([0x00] * 40),              # All spaces
        ]

        for cells in updates:
            self.server.clear_state()  # Clear previous cells
            self.assertTrue(self.client.send_display_cells(cells))
            received = self.server.wait_for_cells(timeout=1.0)
            self.assertIsNotNone(received, f"Should receive cells: {cells.hex()}")
            self.assertEqual(received, cells, "Cells should match")

    def test_cell_count_request(self):
        """Test requesting cell count"""
        # Connect and handshake
        self.assertTrue(self.client.connect('127.0.0.1', 17636))
        self.assertTrue(self.server.wait_for_connection())

        # Request cell count
        self.client.clear_state()
        self.assertTrue(self.client.request_cell_count())

        # Wait for response
        time.sleep(0.2)
        self.assertIsNotNone(self.client.server_cell_count, "Should receive cell count")
        self.assertEqual(self.client.server_cell_count, 40)

    def test_ping_pong(self):
        """Test ping-pong mechanism"""
        # Connect and handshake
        self.assertTrue(self.client.connect('127.0.0.1', 17636))
        self.assertTrue(self.server.wait_for_connection())
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        # Clear message counts
        self.server.clear_state()
        self.client.clear_state()

        # Send ping from client
        timestamp = int(time.time() * 1000)
        self.assertTrue(self.client.send_ping(timestamp))

        # Server should respond with pong
        time.sleep(0.2)
        pong_count = self.server.get_received_message_count(0x40)  # MSG_PING
        self.assertGreaterEqual(pong_count, 1, "Server should receive ping")

    def test_concurrent_operations(self):
        """Test concurrent cell updates and key events"""
        # Connect and handshake
        self.assertTrue(self.client.connect('127.0.0.1', 17636))
        self.assertTrue(self.server.wait_for_connection())
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        # Send cells from client while server sends key events
        test_cells = bytes([0x01, 0x02, 0x03, 0x04, 0x05])
        self.client.send_display_cells(test_cells)
        time.sleep(0.1)  # Small delay to ensure cell send completes
        self.server.send_key_event(100, True)

        # Wait and verify both operations
        received_cells = self.server.wait_for_cells(timeout=1.0)
        key_event = self.client.wait_for_key_event(timeout=2.0)  # Increased timeout

        self.assertIsNotNone(received_cells, "Server should receive cells")
        self.assertIsNotNone(key_event, "Client should receive key event")
        self.assertEqual(received_cells, test_cells)
        self.assertEqual(key_event[0], 100)

    def test_reconnection(self):
        """Test client reconnection"""
        # First connection
        self.assertTrue(self.client.connect('127.0.0.1', 17636))
        self.assertTrue(self.server.wait_for_connection())
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        # Disconnect
        self.client.disconnect()
        time.sleep(0.5)

        # Reconnect
        self.assertTrue(self.client.connect('127.0.0.1', 17636))
        self.assertTrue(self.server.wait_for_connection(timeout=2.0))
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        # Verify new connection works
        test_cells = bytes([0xFF, 0xEE, 0xDD])
        self.server.clear_state()
        self.client.send_display_cells(test_cells)
        received = self.server.wait_for_cells(timeout=1.0)
        self.assertEqual(received, test_cells)

    def test_large_cell_count(self):
        """Test with large braille display"""
        # Stop default server
        self.server.stop()
        time.sleep(0.2)

        # Create server with 80 cells
        self.server = TestRemBrailleServer(cell_count=80, port=17636)
        self.assertTrue(self.server.start())
        time.sleep(0.2)

        # Connect and verify
        self.assertTrue(self.client.connect('127.0.0.1', 17636))
        self.assertTrue(self.server.wait_for_connection())
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        self.assertEqual(self.client.server_cell_count, 80, "Should receive 80 cell count")

        # Send full line of cells
        test_cells = bytes([i % 256 for i in range(80)])
        self.client.send_display_cells(test_cells)
        received = self.server.wait_for_cells(timeout=1.0)
        self.assertEqual(received, test_cells, "Should handle 80 cells")

    def test_empty_cell_data(self):
        """Test sending empty cell data"""
        # Connect and handshake
        self.assertTrue(self.client.connect('127.0.0.1', 17636))
        self.assertTrue(self.server.wait_for_connection())
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        # Send empty cells
        self.server.clear_state()
        self.assertTrue(self.client.send_display_cells(b""))

        # Server should receive empty data
        received = self.server.wait_for_cells(timeout=1.0)
        self.assertIsNotNone(received, "Should receive empty cells")
        self.assertEqual(len(received), 0, "Should be empty")


class TestErrorHandling(unittest.TestCase):
    """Test error handling in server-client communication"""

    def setUp(self):
        """Set up server and client for each test"""
        self.server = TestRemBrailleServer(cell_count=40, port=17637)
        self.client = TestRemBrailleClient(client_id="RemBraille_Test")
        self.assertTrue(self.server.start())
        time.sleep(0.2)

    def tearDown(self):
        """Clean up after each test"""
        if self.client.connected:
            self.client.disconnect()
        self.server.stop()
        time.sleep(0.2)

    def test_connection_refused(self):
        """Test connection to non-existent server"""
        # Stop server
        self.server.stop()
        time.sleep(0.2)

        # Try to connect
        result = self.client.connect('127.0.0.1', 17637, timeout=1.0)
        self.assertFalse(result, "Connection should fail")
        self.assertIsNotNone(self.client.last_error, "Should have error message")

    def test_client_disconnect_detection(self):
        """Test server detects client disconnect"""
        # Connect
        self.assertTrue(self.client.connect('127.0.0.1', 17637))
        self.assertTrue(self.server.wait_for_connection())

        # Client disconnects abruptly
        self.client.disconnect()
        time.sleep(0.5)

        # Server should detect disconnect
        self.assertIsNone(self.server.client_socket, "Server should clear client socket")


if __name__ == '__main__':
    unittest.main()
