#!/usr/bin/env python3
"""
Virtual Cursor Control with evdev
==================================

This script demonstrates creating two virtual mouse devices that move
their cursors up and down independently using the evdev library.

Requirements:
    pip install evdev

Prerequisites:
    - Linux system with uinput module loaded
    - Root privileges or proper udev rules
    - X11 or Wayland display server

Usage:
    sudo python3 virtual_cursor_evdev.py

About MPX (Multi-Pointer X):
----------------------------
MPX (Multi-Pointer X) is an X11 extension that allows multiple independent
cursors and keyboards to be used simultaneously on a single X server.

Key MPX Concepts:
- Master Devices: Virtual devices that represent cursors/keyboards in X
- Slave Devices: Physical or virtual input devices attached to masters
- Each master device has its own cursor and focus
- Applications can receive input from multiple pointers independently

To use MPX with this script:
1. Create virtual devices with this script
2. Use xinput to attach them to different master pointers:
   xinput create-master "Pointer2"
   xinput reattach <device-id> "Pointer2 pointer"
3. Each master pointer will have its own cursor

View MPX configuration:
   xinput list

This script creates uinput devices that can be managed by MPX.
"""

import evdev
from evdev import UInput, ecodes as e
import time
import sys
import threading


class VirtualMouse:
    """Create and control a virtual mouse device."""

    def __init__(self, name="Virtual Mouse"):
        """
        Initialize a virtual mouse device.

        Args:
            name: Name for the virtual device
        """
        # Define capabilities for a complete mouse device
        capabilities = {
            e.EV_REL: [
                e.REL_X,  # X-axis movement
                e.REL_Y,  # Y-axis movement
                e.REL_WHEEL,  # Scroll wheel
            ],
            e.EV_KEY: [
                e.BTN_LEFT,  # Left button
                e.BTN_RIGHT,  # Right button
                e.BTN_MIDDLE,  # Middle button
            ],
        }

        try:
            self.device = UInput(capabilities, name=name)
            print(f"✓ Created virtual device: {name}")
            print(f"  Device path: {self.device.device.path}")
            time.sleep(0.5)  # Allow system to recognize device
        except PermissionError:
            print("ERROR: Permission denied. Run with sudo or configure udev rules.")
            sys.exit(1)
        except Exception as ex:
            print(f"ERROR: Failed to create device: {ex}")
            sys.exit(1)

    def move_relative(self, dx, dy):
        """
        Move cursor relative to current position.

        Args:
            dx: X-axis movement (positive=right, negative=left)
            dy: Y-axis movement (positive=down, negative=up)
        """
        if dx != 0:
            self.device.write(e.EV_REL, e.REL_X, dx)
        if dy != 0:
            self.device.write(e.EV_REL, e.REL_Y, dy)
        self.device.syn()

    def click(self, button=e.BTN_LEFT):
        """
        Perform a mouse click.

        Args:
            button: Button to click (BTN_LEFT, BTN_RIGHT, BTN_MIDDLE)
        """
        self.device.write(e.EV_KEY, button, 1)  # Press
        self.device.syn()
        time.sleep(0.01)
        self.device.write(e.EV_KEY, button, 0)  # Release
        self.device.syn()

    def close(self):
        """Clean up the virtual device."""
        self.device.close()
        print(f"✓ Closed device")


def animate_cursor_vertical(mouse, name, direction="up", duration=5, speed=10):
    """
    Animate cursor moving up or down.

    Args:
        mouse: VirtualMouse instance
        name: Name for logging
        direction: "up" or "down"
        duration: How long to animate in seconds
        speed: Pixels per step
    """
    dy = -speed if direction == "up" else speed
    steps = int(duration * 60)  # 60 fps

    print(f"[{name}] Moving {direction} for {duration} seconds...")

    for i in range(steps):
        mouse.move_relative(0, dy)
        time.sleep(1 / 60)  # ~60 fps

    print(f"[{name}] Animation complete")


def run_two_cursor_test():
    """Main test function: creates two cursors moving in opposite directions."""

    print("\n" + "=" * 60)
    print("Virtual Cursor Test with evdev")
    print("=" * 60)
    print("\nThis script creates two virtual mice that move up and down.")
    print("Press Ctrl+C to stop.\n")

    # Create two virtual mouse devices
    mouse1 = VirtualMouse(name="Virtual Mouse 1 - Up")
    mouse2 = VirtualMouse(name="Virtual Mouse 2 - Down")

    print("\n" + "-" * 60)
    print("MPX Configuration (Optional):")
    print("-" * 60)
    print("To see these as separate cursors, configure MPX:")
    print("  1. xinput list")
    print("  2. xinput create-master 'Pointer2'")
    print("  3. Find device IDs and reattach:")
    print("     xinput reattach <device-id> 'Pointer2 pointer'")
    print("-" * 60 + "\n")

    try:
        # Start both animations in separate threads
        print("Starting animation...")
        time.sleep(2)

        thread1 = threading.Thread(
            target=animate_cursor_vertical,
            args=(mouse1, "Mouse 1", "up", 5, 8)
        )
        thread2 = threading.Thread(
            target=animate_cursor_vertical,
            args=(mouse2, "Mouse 2", "down", 5, 8)
        )

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        print("\nTest complete! Moving cursors back to center...")

        # Return cursors to approximate center
        for _ in range(50):
            mouse1.move_relative(0, 8)
            mouse2.move_relative(0, -8)
            time.sleep(0.01)

        print("\n✓ Test finished successfully")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as ex:
        print(f"\nError during test: {ex}")
    finally:
        # Cleanup
        print("\nCleaning up...")
        mouse1.close()
        mouse2.close()


def print_system_info():
    """Print system information and requirements."""
    print("\nSystem Requirements Check:")
    print("-" * 40)

    # Check for uinput module
    try:
        with open('/dev/uinput', 'r'):
            print("✓ /dev/uinput is accessible")
    except PermissionError:
        print("✗ /dev/uinput requires root privileges")
        print("  Run with: sudo python3 script.py")
    except FileNotFoundError:
        print("✗ /dev/uinput not found")
        print("  Load module: sudo modprobe uinput")

    # Check for evdev
    try:
        import evdev
    except ImportError:
        print("✗ evdev not installed")
        print("  Install with: pip install evdev")

    print("-" * 40 + "\n")


if __name__ == "__main__":
    print_system_info()

    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        sys.exit(0)

    run_two_cursor_test()