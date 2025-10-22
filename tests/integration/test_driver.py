"""
Integration tests for RemBraille NVDA Driver

These tests verify the RemBraille driver add-on for NVDA by acting as a server
and verifying the driver connects and sends braille data correctly.

The driver tests use the test server to simulate a RemBrailleReceiver host.

Requirements:
    - Windows OS
    - NVDA screen reader installed
    - RemBraille Driver add-on installed in NVDA
    - Driver configured to connect to localhost:17635

Usage:
    # Start the test server
    python3 -m tests.fixtures.test_server

    # Configure NVDA RemBraille driver to connect to localhost
    # Then run these tests
    python3 test_driver.py

Note: These tests can also be run independently of NVDA to test the protocol
      from the server side.
"""

import unittest
import time
import sys
import os
import platform

# Add fixtures to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'fixtures'))

from test_server import TestRemBrailleServer


class TestRemBrailleDriver(unittest.TestCase):
    """
    Integration tests for the RemBraille NVDA driver.

    These tests act as a server and verify that the NVDA driver
    connects and communicates correctly.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test server for driver tests"""
        cls.server = TestRemBrailleServer(cell_count=40, port=17635)

        if not cls.server.start():
            raise unittest.SkipTest("Failed to start test server")

        print("\n" + "="*70)
        print("Test server is running on port 17635")
        print("="*70)
        print("\nPlease configure NVDA RemBraille driver to connect to:")
        print("  Host: localhost (127.0.0.1)")
        print("  Port: 17635")
        print("\nThen enable the RemBraille driver in NVDA.")
        print("="*70 + "\n")

    @classmethod
    def tearDownClass(cls):
        """Stop test server"""
        cls.server.stop()

    def setUp(self):
        """Clear state before each test"""
        self.server.clear_state()

    def test_driver_connection(self):
        """Test that driver connects to server"""
        print("\nWaiting for NVDA driver to connect (30 seconds)...")

        result = self.server.wait_for_connection(timeout=30.0)

        if not result:
            self.skipTest("NVDA driver did not connect. Make sure NVDA is running with RemBraille driver enabled.")

        self.assertTrue(result, "Driver should connect to server")
        print(f"Driver connected from: {self.server.connected_client}")

    def test_driver_handshake(self):
        """Test that driver sends handshake"""
        print("\nWaiting for driver connection...")

        if not self.server.wait_for_connection(timeout=30.0):
            self.skipTest("NVDA driver did not connect")

        # Wait for handshake message
        time.sleep(1.0)

        handshake_count = self.server.get_received_message_count(0x01)  # MSG_HANDSHAKE
        self.assertGreater(handshake_count, 0, "Driver should send handshake")

        print(f"Received handshake from driver")

    def test_driver_sends_braille_output(self):
        """Test that driver sends braille display data"""
        print("\nWaiting for driver connection...")

        if not self.server.wait_for_connection(timeout=30.0):
            self.skipTest("NVDA driver did not connect")

        print("\nNow navigate in NVDA to generate braille output...")
        print("Press Enter when ready, or wait for timeout...")

        # Wait for braille cells
        cells = self.server.wait_for_cells(timeout=30.0)

        if cells is None:
            print("\nNo braille output received. Make sure you're navigating in NVDA.")
            self.skipTest("No braille output received from driver")

        self.assertIsNotNone(cells, "Should receive braille cells")
        print(f"\nReceived {len(cells)} braille cells: {cells.hex()}")

    def test_driver_cell_updates(self):
        """Test receiving multiple cell updates from driver"""
        print("\nWaiting for driver connection...")

        if not self.server.wait_for_connection(timeout=30.0):
            self.skipTest("NVDA driver did not connect")

        print("\nNavigate around in NVDA to generate multiple braille updates...")
        print("This test will collect updates for 10 seconds...")

        # Track cell updates
        cell_updates = []

        def on_cells(cells):
            cell_updates.append(cells)
            print(f"  Update {len(cell_updates)}: {len(cells)} cells - {cells[:20].hex()}...")

        self.server.on_cells_received = on_cells

        # Wait for updates
        time.sleep(10.0)

        if len(cell_updates) == 0:
            self.skipTest("No cell updates received. Make sure you're actively using NVDA.")

        print(f"\nReceived {len(cell_updates)} cell updates")
        self.assertGreater(len(cell_updates), 0, "Should receive cell updates")

    def test_send_key_event_to_driver(self):
        """Test sending key events to driver"""
        print("\nWaiting for driver connection...")

        if not self.server.wait_for_connection(timeout=30.0):
            self.skipTest("NVDA driver did not connect")

        # Wait for driver to be ready
        time.sleep(1.0)

        # Send simulated key press
        key_id = 100
        print(f"\nSending key press event (key {key_id}) to driver...")

        result = self.server.send_key_event(key_id, is_pressed=True)
        self.assertTrue(result, "Should send key press")

        time.sleep(0.5)

        # Send key release
        result = self.server.send_key_event(key_id, is_pressed=False)
        self.assertTrue(result, "Should send key release")

        print("Key events sent successfully")
        print("(Note: Driver should process these as braille display key inputs)")


class TestDriverProtocolCompliance(unittest.TestCase):
    """Test that driver follows RemBraille protocol correctly"""

    def setUp(self):
        """Set up server for each test"""
        self.server = TestRemBrailleServer(cell_count=40, port=17638)  # Different port
        self.assertTrue(self.server.start())
        time.sleep(0.2)

    def tearDown(self):
        """Stop server after each test"""
        self.server.stop()
        time.sleep(0.2)

    def test_protocol_message_format(self):
        """Test that driver sends correctly formatted messages"""
        print("\nConfigure NVDA driver to connect to port 17638, then press Enter...")
        print("(This is a manual test - will timeout after 30 seconds)")

        if not self.server.wait_for_connection(timeout=30.0):
            self.skipTest("Driver did not connect to test port")

        # Wait for some messages
        time.sleep(2.0)

        # Verify we received valid messages
        self.assertGreater(len(self.server.received_messages), 0, "Should receive messages")

        print(f"\nReceived {len(self.server.received_messages)} protocol messages")
        print("All messages were successfully parsed (protocol compliant)")


class TestDriverStandalone(unittest.TestCase):
    """
    Standalone server tests that can run without NVDA.

    These verify the test server functionality for driver testing.
    """

    def test_server_accepts_connections(self):
        """Test that server can accept connections"""
        server = TestRemBrailleServer(cell_count=40, port=17639)
        self.assertTrue(server.start(), "Server should start")

        time.sleep(0.2)

        # Try to connect with a basic socket
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)

        try:
            sock.connect(('127.0.0.1', 17639))
            self.assertTrue(server.wait_for_connection(timeout=1.0))
            print("\nServer successfully accepted connection")
        finally:
            sock.close()
            server.stop()

    def test_server_handles_handshake(self):
        """Test that server responds to handshake correctly"""
        server = TestRemBrailleServer(cell_count=80, port=17640)
        self.assertTrue(server.start())
        time.sleep(0.2)

        try:
            # Use test client
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'fixtures'))
            from test_client import TestRemBrailleClient

            client = TestRemBrailleClient("TestDriver")
            self.assertTrue(client.connect('127.0.0.1', 17640))

            client.send_handshake()
            self.assertTrue(client.wait_for_handshake_response(timeout=2.0))

            self.assertEqual(client.server_cell_count, 80, "Should receive correct cell count")
            print(f"\nServer correctly responded with cell count: {client.server_cell_count}")

            client.disconnect()

        finally:
            server.stop()

    def test_server_receives_cells(self):
        """Test that server can receive braille cells"""
        server = TestRemBrailleServer(cell_count=40, port=17641)

        received_data = []

        def on_cells(cells):
            received_data.append(cells)

        server.on_cells_received = on_cells
        self.assertTrue(server.start())
        time.sleep(0.2)

        try:
            from test_client import TestRemBrailleClient

            client = TestRemBrailleClient("TestDriver")
            self.assertTrue(client.connect('127.0.0.1', 17641))
            client.send_handshake()
            client.wait_for_handshake_response()

            # Send cells
            test_cells = bytes([0x01, 0x02, 0x03, 0x04])
            client.send_display_cells(test_cells)

            time.sleep(0.2)

            self.assertEqual(len(received_data), 1, "Should receive cell data")
            self.assertEqual(received_data[0], test_cells)
            print(f"\nServer correctly received {len(test_cells)} braille cells")

            client.disconnect()

        finally:
            server.stop()


if __name__ == '__main__':
    # Check platform
    if platform.system() == 'Windows':
        print("\nRunning on Windows - full driver tests available")
    else:
        print("\nNot running on Windows - only standalone server tests will be meaningful")

    # Run tests with verbose output
    unittest.main(verbosity=2)
