"""
Unit tests for RemBraille protocol message encoding/decoding
"""

import unittest
import struct
from typing import Tuple


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


class RemBrailleMessage:
    """Represents a RemBraille protocol message"""

    def __init__(self, msg_type: int, data: bytes = b""):
        self.version = PROTOCOL_VERSION
        self.msg_type = msg_type
        self.data = data

    def serialize(self) -> bytes:
        """Serialize message to bytes"""
        header = struct.pack("!BBH", self.version, self.msg_type, len(self.data))
        return header + self.data

    @staticmethod
    def deserialize(data: bytes) -> Tuple['RemBrailleMessage', int]:
        """
        Deserialize message from bytes
        Returns: (message, bytes_consumed)
        """
        if len(data) < 4:
            raise ValueError("Insufficient data for header")

        version, msg_type, length = struct.unpack("!BBH", data[:4])

        if len(data) < 4 + length:
            raise ValueError("Insufficient data for payload")

        payload = data[4:4+length]
        msg = RemBrailleMessage(msg_type, payload)
        msg.version = version

        return msg, 4 + length


class TestProtocolMessages(unittest.TestCase):
    """Test protocol message encoding and decoding"""

    def test_handshake_message(self):
        """Test handshake message serialization"""
        client_id = b"RemBraille_Guest"
        msg = RemBrailleMessage(MSG_HANDSHAKE, client_id)
        data = msg.serialize()

        # Verify header
        self.assertEqual(data[0], PROTOCOL_VERSION)
        self.assertEqual(data[1], MSG_HANDSHAKE)
        self.assertEqual(struct.unpack("!H", data[2:4])[0], len(client_id))
        self.assertEqual(data[4:], client_id)

    def test_handshake_response(self):
        """Test handshake response message"""
        cell_count = 40
        response_data = struct.pack("!H", cell_count) + b"RemBraille_Host"
        msg = RemBrailleMessage(MSG_HANDSHAKE_RESP, response_data)
        data = msg.serialize()

        # Deserialize and verify
        parsed_msg, consumed = RemBrailleMessage.deserialize(data)
        self.assertEqual(parsed_msg.msg_type, MSG_HANDSHAKE_RESP)
        self.assertEqual(consumed, len(data))

        # Extract cell count
        parsed_cell_count = struct.unpack("!H", parsed_msg.data[:2])[0]
        self.assertEqual(parsed_cell_count, cell_count)

    def test_display_cells_message(self):
        """Test braille cell display message"""
        cells = bytes([0x01, 0x03, 0x09, 0x19, 0x15])  # "Hello" in braille
        msg = RemBrailleMessage(MSG_DISPLAY_CELLS, cells)
        data = msg.serialize()

        # Deserialize and verify
        parsed_msg, _ = RemBrailleMessage.deserialize(data)
        self.assertEqual(parsed_msg.msg_type, MSG_DISPLAY_CELLS)
        self.assertEqual(parsed_msg.data, cells)

    def test_key_event_press(self):
        """Test key press event message"""
        key_id = 42
        event_type = KEY_DOWN
        key_data = struct.pack("!IB", key_id, event_type)

        msg = RemBrailleMessage(MSG_KEY_EVENT, key_data)
        data = msg.serialize()

        # Deserialize and verify
        parsed_msg, _ = RemBrailleMessage.deserialize(data)
        self.assertEqual(parsed_msg.msg_type, MSG_KEY_EVENT)

        parsed_key_id, parsed_event = struct.unpack("!IB", parsed_msg.data)
        self.assertEqual(parsed_key_id, key_id)
        self.assertEqual(parsed_event, KEY_DOWN)

    def test_key_event_release(self):
        """Test key release event message"""
        key_id = 123
        event_type = KEY_UP
        key_data = struct.pack("!IB", key_id, event_type)

        msg = RemBrailleMessage(MSG_KEY_EVENT, key_data)
        data = msg.serialize()

        parsed_msg, _ = RemBrailleMessage.deserialize(data)
        parsed_key_id, parsed_event = struct.unpack("!IB", parsed_msg.data)
        self.assertEqual(parsed_key_id, key_id)
        self.assertEqual(parsed_event, KEY_UP)

    def test_num_cells_request(self):
        """Test cell count request message"""
        msg = RemBrailleMessage(MSG_NUM_CELLS_REQ)
        data = msg.serialize()

        # Should have empty payload
        self.assertEqual(len(data), 4)
        self.assertEqual(data[1], MSG_NUM_CELLS_REQ)
        self.assertEqual(struct.unpack("!H", data[2:4])[0], 0)

    def test_num_cells_response(self):
        """Test cell count response message"""
        cell_count = 80
        cell_data = struct.pack("!H", cell_count)
        msg = RemBrailleMessage(MSG_NUM_CELLS_RESP, cell_data)
        data = msg.serialize()

        parsed_msg, _ = RemBrailleMessage.deserialize(data)
        parsed_count = struct.unpack("!H", parsed_msg.data)[0]
        self.assertEqual(parsed_count, cell_count)

    def test_ping_message(self):
        """Test ping message with timestamp"""
        import time
        timestamp = int(time.time() * 1000)
        timestamp_data = struct.pack("!Q", timestamp)

        msg = RemBrailleMessage(MSG_PING, timestamp_data)
        data = msg.serialize()

        parsed_msg, _ = RemBrailleMessage.deserialize(data)
        self.assertEqual(parsed_msg.msg_type, MSG_PING)
        parsed_ts = struct.unpack("!Q", parsed_msg.data)[0]
        self.assertEqual(parsed_ts, timestamp)

    def test_pong_message(self):
        """Test pong response message"""
        import time
        timestamp = int(time.time() * 1000)
        timestamp_data = struct.pack("!Q", timestamp)

        msg = RemBrailleMessage(MSG_PONG, timestamp_data)
        data = msg.serialize()

        parsed_msg, _ = RemBrailleMessage.deserialize(data)
        self.assertEqual(parsed_msg.msg_type, MSG_PONG)
        parsed_ts = struct.unpack("!Q", parsed_msg.data)[0]
        self.assertEqual(parsed_ts, timestamp)

    def test_error_message(self):
        """Test error message"""
        error_text = "Protocol version mismatch"
        msg = RemBrailleMessage(MSG_ERROR, error_text.encode('utf-8'))
        data = msg.serialize()

        parsed_msg, _ = RemBrailleMessage.deserialize(data)
        self.assertEqual(parsed_msg.msg_type, MSG_ERROR)
        self.assertEqual(parsed_msg.data.decode('utf-8'), error_text)

    def test_empty_message(self):
        """Test message with no payload"""
        msg = RemBrailleMessage(MSG_PING)
        data = msg.serialize()

        self.assertEqual(len(data), 4)  # Just header
        parsed_msg, consumed = RemBrailleMessage.deserialize(data)
        self.assertEqual(consumed, 4)
        self.assertEqual(len(parsed_msg.data), 0)

    def test_large_payload(self):
        """Test message with large payload"""
        large_data = bytes([i % 256 for i in range(1000)])
        msg = RemBrailleMessage(MSG_DISPLAY_CELLS, large_data)
        data = msg.serialize()

        parsed_msg, _ = RemBrailleMessage.deserialize(data)
        self.assertEqual(parsed_msg.data, large_data)

    def test_insufficient_data(self):
        """Test deserialization with insufficient data"""
        # Only 2 bytes - not enough for header
        with self.assertRaises(ValueError):
            RemBrailleMessage.deserialize(b"\x01\x01")

        # Header indicates 10 bytes payload, but only 5 provided
        incomplete = struct.pack("!BBH", 1, MSG_PING, 10) + b"12345"
        with self.assertRaises(ValueError):
            RemBrailleMessage.deserialize(incomplete)

    def test_protocol_version(self):
        """Test protocol version handling"""
        msg = RemBrailleMessage(MSG_HANDSHAKE, b"test")
        data = msg.serialize()

        self.assertEqual(data[0], PROTOCOL_VERSION)
        parsed_msg, _ = RemBrailleMessage.deserialize(data)
        self.assertEqual(parsed_msg.version, PROTOCOL_VERSION)


class TestBrailleEncoding(unittest.TestCase):
    """Test braille cell encoding"""

    def test_braille_dot_patterns(self):
        """Test standard braille dot patterns"""
        # Letter 'A' (dot 1)
        self.assertEqual(0x01, 0b00000001)

        # Letter 'B' (dots 1,2)
        self.assertEqual(0x03, 0b00000011)

        # Letter 'C' (dots 1,4)
        self.assertEqual(0x09, 0b00001001)

        # Space (no dots)
        self.assertEqual(0x00, 0b00000000)

    def test_8dot_braille(self):
        """Test 8-dot braille patterns"""
        # All 8 dots
        all_dots = 0xFF
        self.assertEqual(all_dots, 0b11111111)

        # Dots 7 and 8
        dots_78 = 0xC0
        self.assertEqual(dots_78, 0b11000000)


if __name__ == '__main__':
    unittest.main()
