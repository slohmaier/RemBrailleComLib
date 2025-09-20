#!/usr/bin/env python3
"""
RemBraille Python Basic Client Example

Demonstrates basic usage of the RemBraille Python library including:
- Connection establishment
- Braille cell display
- Key event handling
- Connection testing

Usage:
    python basic_client.py [HOST_IP] [PORT]

Copyright (C) 2025 Stefan Lohmaier
Licensed under GNU GPL v2.0 or later
"""

import sys
import time
import logging
from pathlib import Path

# Add the python library to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from rembraille import RemBrailleCom

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def key_event_handler(key_id: int, is_pressed: bool):
    """Handle key events from the braille display"""
    action = "pressed" if is_pressed else "released"
    logger.info(f"🔘 Braille key {key_id} {action}")


def display_demo_text(connection: RemBrailleCom):
    """Display some demo text on the braille display"""
    # Simple braille translation (dots 1-6 only for demonstration)
    braille_map = {
        'a': 0x01, 'b': 0x03, 'c': 0x09, 'd': 0x19, 'e': 0x11,
        'f': 0x0B, 'g': 0x1B, 'h': 0x13, 'i': 0x0A, 'j': 0x1A,
        'k': 0x05, 'l': 0x07, 'm': 0x0D, 'n': 0x1D, 'o': 0x15,
        'p': 0x0F, 'q': 0x1F, 'r': 0x17, 's': 0x0E, 't': 0x1E,
        'u': 0x25, 'v': 0x27, 'w': 0x3A, 'x': 0x2D, 'y': 0x3D,
        'z': 0x35, ' ': 0x00
    }

    messages = [
        "hello world",
        "rembraille test",
        "python example"
    ]

    for message in messages:
        logger.info(f"📝 Displaying: '{message}'")

        # Convert to braille cells
        cells = []
        for char in message.lower():
            cells.append(braille_map.get(char, 0x00))

        # Pad or truncate to display size
        cell_count = connection.get_num_cells()
        if len(cells) > cell_count:
            cells = cells[:cell_count]
        else:
            cells.extend([0x00] * (cell_count - len(cells)))

        # Send to display
        if connection.display_cells(bytes(cells)):
            logger.info(f"✅ Successfully sent {len(cells)} cells")
        else:
            logger.error("❌ Failed to send cells")

        time.sleep(3)


def main():
    """Main function"""
    # Parse command line arguments
    host_ip = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 17635

    logger.info(f"🚀 RemBraille Python Client Example")
    logger.info(f"📡 Connecting to {host_ip}:{port}")

    # Create connection with key event handler
    connection = RemBrailleCom(on_key_event=key_event_handler)

    try:
        # Attempt connection
        if connection.connect(host_ip, port, timeout=10.0):
            logger.info(f"✅ Connected successfully!")
            logger.info(f"📏 Display has {connection.get_num_cells()} braille cells")

            # Test connection
            if connection.test_connection():
                logger.info("🔗 Connection test passed")
            else:
                logger.warning("⚠️ Connection test failed")

            # Display demo content
            display_demo_text(connection)

            # Keep connection alive for key events
            logger.info("⏳ Keeping connection alive for 30 seconds...")
            logger.info("💡 Try pressing keys on the braille display!")

            start_time = time.time()
            while time.time() - start_time < 30:
                if not connection.connected:
                    logger.error("❌ Connection lost!")
                    break
                time.sleep(0.5)

        else:
            logger.error("❌ Failed to connect to RemBraille host")
            logger.info("💡 Make sure the RemBraille server is running:")
            logger.info(f"    python ../tools/rembraille_server.py --port {port}")
            return 1

    except KeyboardInterrupt:
        logger.info("\n⏹️ Interrupted by user")

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1

    finally:
        # Clean disconnect
        if connection.connected:
            logger.info("🔌 Disconnecting...")
            connection.disconnect()
            logger.info("👋 Disconnected successfully")

    return 0


if __name__ == "__main__":
    sys.exit(main())