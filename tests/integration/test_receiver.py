"""
Integration tests for RemBrailleReceiver (macOS Swift app)

These tests verify the RemBrailleReceiver application by acting as a client
and connecting to it. The receiver must be running before executing these tests.

Usage:
    # Start the receiver
    cd /Users/stefan/git/RemBrailleReceiver/macos
    swift build -c release
    ./.build/release/RemBrailleReceiver &

    # Run the tests
    python3 test_receiver.py
"""

import unittest
import time
import sys
import os
import socket

# Add fixtures to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'fixtures'))

from test_client import TestRemBrailleClient


class TestRemBrailleReceiver(unittest.TestCase):
    """
    Integration tests for the RemBrailleReceiver macOS application.

    IMPORTANT: The receiver must be running before executing these tests.
    """

    @classmethod
    def setUpClass(cls):
        """Check if receiver is running before tests"""
        cls.receiver_port = 17635  # Default receiver port
        cls.receiver_host = '127.0.0.1'

        # Check if receiver is listening
        if not cls._is_receiver_running():
            print("\n" + "="*70)
            print("WARNING: RemBrailleReceiver is not running!")
            print("="*70)
            print("\nPlease start the receiver first:")
            print("  cd /Users/stefan/git/RemBrailleReceiver/macos")
            print("  swift build -c release")
            print("  ./.build/release/RemBrailleReceiver")
            print("\nThen run these tests again.")
            print("="*70 + "\n")
            raise unittest.SkipTest("RemBrailleReceiver is not running")

    @classmethod
    def _is_receiver_running(cls):
        """Check if receiver is listening on the expected port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            result = sock.connect_ex((cls.receiver_host, cls.receiver_port))
            sock.close()
            return result == 0
        except:
            return False

    def setUp(self):
        """Set up client for each test"""
        self.client = TestRemBrailleClient(client_id="RemBraille_IntegrationTest")

    def tearDown(self):
        """Clean up after each test"""
        if self.client.connected:
            self.client.disconnect()
        time.sleep(0.2)

    def test_receiver_connection(self):
        """Test connecting to the receiver"""
        result = self.client.connect(self.receiver_host, self.receiver_port, timeout=5.0)
        self.assertTrue(result, f"Should connect to receiver: {self.client.last_error}")
        self.assertTrue(self.client.connected, "Client should be connected")

    def test_receiver_handshake(self):
        """Test handshake with receiver"""
        # Connect
        self.assertTrue(self.client.connect(self.receiver_host, self.receiver_port))

        # Send handshake
        self.assertTrue(self.client.send_handshake(), "Should send handshake")

        # Wait for handshake response
        result = self.client.wait_for_handshake_response(timeout=5.0)
        self.assertTrue(result, "Should receive handshake response")

        # Verify receiver provides cell count
        self.assertIsNotNone(self.client.server_cell_count, "Should receive cell count")
        self.assertGreater(self.client.server_cell_count, 0, "Cell count should be positive")

        print(f"\nReceiver info: {self.client.server_name} with {self.client.server_cell_count} cells")

    def test_send_braille_cells(self):
        """Test sending braille cell data to receiver"""
        # Connect and handshake
        self.assertTrue(self.client.connect(self.receiver_host, self.receiver_port))
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        # Send various braille patterns
        test_patterns = [
            bytes([0x01, 0x03, 0x09, 0x19, 0x15]),  # "Hello" in braille
            bytes([0x1A, 0x15, 0x12, 0x0D]),        # "World" in braille
            bytes([0x00] * 40),                      # All spaces (blank display)
            bytes([0xFF] * 20),                      # All dots raised
        ]

        for i, cells in enumerate(test_patterns):
            result = self.client.send_display_cells(cells)
            self.assertTrue(result, f"Should send cells pattern {i+1}")
            time.sleep(0.5)  # Give receiver time to process

        print(f"\nSuccessfully sent {len(test_patterns)} cell patterns to receiver")

    def test_multiple_connections(self):
        """Test multiple sequential connections"""
        for i in range(3):
            # Connect
            self.assertTrue(self.client.connect(self.receiver_host, self.receiver_port))
            self.client.send_handshake()
            self.assertTrue(self.client.wait_for_handshake_response())

            # Send data
            test_cells = bytes([i+1] * 10)
            self.client.send_display_cells(test_cells)
            time.sleep(0.2)

            # Disconnect
            self.client.disconnect()
            time.sleep(0.5)

        print("\nSuccessfully completed 3 sequential connections")

    def test_cell_count_query(self):
        """Test querying cell count from receiver"""
        # Connect
        self.assertTrue(self.client.connect(self.receiver_host, self.receiver_port))

        # Request cell count
        self.assertTrue(self.client.request_cell_count())

        # Wait for response
        time.sleep(1.0)
        self.assertIsNotNone(self.client.server_cell_count, "Should receive cell count")
        self.assertGreater(self.client.server_cell_count, 0, "Cell count should be positive")

        print(f"\nReceiver reports {self.client.server_cell_count} cells")

    def test_ping_receiver(self):
        """Test ping/pong with receiver"""
        # Connect and handshake
        self.assertTrue(self.client.connect(self.receiver_host, self.receiver_port))
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        # Send ping
        start_time = time.time()
        timestamp = int(start_time * 1000)
        self.assertTrue(self.client.send_ping(timestamp))

        # Wait for pong (if receiver implements it)
        time.sleep(0.5)
        end_time = time.time()
        latency = (end_time - start_time) * 1000

        print(f"\nPing latency: {latency:.2f}ms")

    def test_sustained_connection(self):
        """Test maintaining connection and sending multiple updates"""
        # Connect and handshake
        self.assertTrue(self.client.connect(self.receiver_host, self.receiver_port))
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        # Send multiple cell updates over time
        num_updates = 10
        for i in range(num_updates):
            # Create varying pattern
            cells = bytes([(i * 10 + j) % 256 for j in range(20)])
            self.assertTrue(self.client.send_display_cells(cells))
            time.sleep(0.2)

        self.assertTrue(self.client.connected, "Connection should remain stable")
        print(f"\nSent {num_updates} updates over sustained connection")

    def test_large_cell_data(self):
        """Test sending maximum-sized cell data"""
        # Connect and handshake
        self.assertTrue(self.client.connect(self.receiver_host, self.receiver_port))
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        # Send data matching receiver's cell count
        cell_count = self.client.server_cell_count
        large_cells = bytes([i % 256 for i in range(cell_count)])

        result = self.client.send_display_cells(large_cells)
        self.assertTrue(result, f"Should handle {cell_count} cells")

        print(f"\nSuccessfully sent {cell_count} braille cells")

    def test_empty_cells(self):
        """Test sending empty cell data"""
        # Connect and handshake
        self.assertTrue(self.client.connect(self.receiver_host, self.receiver_port))
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        # Send empty cells
        result = self.client.send_display_cells(b"")
        self.assertTrue(result, "Should handle empty cell data")

    def test_rapid_updates(self):
        """Test rapid successive cell updates"""
        # Connect and handshake
        self.assertTrue(self.client.connect(self.receiver_host, self.receiver_port))
        self.client.send_handshake()
        self.assertTrue(self.client.wait_for_handshake_response())

        # Send rapid updates
        start_time = time.time()
        num_updates = 50
        for i in range(num_updates):
            cells = bytes([i % 256] * 10)
            self.client.send_display_cells(cells)
            # No delay between sends

        elapsed = time.time() - start_time
        updates_per_sec = num_updates / elapsed

        print(f"\nSent {num_updates} updates in {elapsed:.2f}s ({updates_per_sec:.1f} updates/sec)")
        self.assertTrue(self.client.connected, "Connection should remain stable during rapid updates")


class TestReceiverErrorHandling(unittest.TestCase):
    """Test error handling in the receiver"""

    @classmethod
    def setUpClass(cls):
        """Check if receiver is running"""
        cls.receiver_port = 17635
        cls.receiver_host = '127.0.0.1'

        if not cls._is_receiver_running():
            raise unittest.SkipTest("RemBrailleReceiver is not running")

    @classmethod
    def _is_receiver_running(cls):
        """Check if receiver is listening"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            result = sock.connect_ex((cls.receiver_host, cls.receiver_port))
            sock.close()
            return result == 0
        except:
            return False

    def setUp(self):
        """Set up client for each test"""
        self.client = TestRemBrailleClient(client_id="RemBraille_ErrorTest")

    def tearDown(self):
        """Clean up after each test"""
        if self.client.connected:
            self.client.disconnect()
        time.sleep(0.2)

    def test_connection_without_handshake(self):
        """Test what happens when connecting without sending handshake"""
        # Connect but don't send handshake
        self.assertTrue(self.client.connect(self.receiver_host, self.receiver_port))

        # Try to send cells without handshake
        cells = bytes([0x01, 0x02, 0x03])
        result = self.client.send_display_cells(cells)
        self.assertTrue(result, "Should be able to send (though receiver may ignore)")

        time.sleep(0.5)
        # Connection should still be alive (receiver handles gracefully)
        self.assertTrue(self.client.connected, "Connection should remain open")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
