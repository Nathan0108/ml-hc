import cv2
import numpy as np
import math
import stream
import detectors
from coordinates import Coordinates
from cursor import Cursor
from threading import Thread
import colorsys

# Screen/Monitor settings
MONITOR_WIDTH = 1920
MONITOR_HEIGHT = 1080
DIAGONAL_INCHES = 27
ASPECT_RATIO = (16, 9)

# Camera offsets (in meters)
CAMERA_X_OFFSET = -0.29  # 28cm from top-left
CAMERA_Y_OFFSET = 0.03  # Adjust based on your setup (negative = above screen)
CAMERA_Z_OFFSET = -0.015  # 3cm in front of screen

# Camera resolution
CAMERA_WIDTH = 1440
CAMERA_HEIGHT = 960

# Cursor tracking parameters
MICE_COUNT = 4  # Maximum number of mice to track
MAX_X_DIST = 700  # Maximum x distance (pixels) for hand tracking continuity
MAX_Y_DIST = 500  # Maximum y distance (pixels) for hand tracking continuity
TIMEOUT = 2.0  # Seconds before a mouse is freed if no hand nearby

# Pinch parameters
PRESS_THRESHOLD = 0.02  # Distance in meters to trigger press (3cm)
UNPRESS_THRESHOLD = 0.03  # Distance in meters to start unpress counter (5cm)
UNPRESS_FRAMES = 3  # Number of frames above threshold before unpressing


def get_monitor_dimensions(diagonal_length, ar1, ar2):
    """Calculate monitor physical dimensions in inches from diagonal and aspect ratio"""
    k = diagonal_length / math.sqrt(ar1 ** 2 + ar2 ** 2)
    return ar1 * k, ar2 * k


def generate_unique_colors(n):
    """Generate n visually distinct colors using HSV color space"""
    colors = []
    for i in range(n):
        hue = i / n  # Distribute hues evenly across color wheel
        saturation = 0.8  # High saturation for vibrant colors
        value = 0.9  # High value for bright colors

        # Convert HSV to RGB (0-1 range)
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)

        # Convert to BGR (0-255 range) for OpenCV
        bgr = (int(rgb[2] * 255), int(rgb[1] * 255), int(rgb[0] * 255))
        colors.append(bgr)

    return colors


def main():
    # Calculate physical screen dimensions
    physical_width, physical_height = get_monitor_dimensions(
        DIAGONAL_INCHES, ASPECT_RATIO[0], ASPECT_RATIO[1]
    )

    print(f"Monitor: {MONITOR_WIDTH}x{MONITOR_HEIGHT} pixels")
    print(f"Physical: {physical_width:.2f}\" x {physical_height:.2f}\"")
    print(f"Camera offset: X={CAMERA_X_OFFSET}m, Y={CAMERA_Y_OFFSET}m, Z={CAMERA_Z_OFFSET}m")

    # Initialize cameras
    print("Initializing cameras...")
    c1 = stream.Camera(src=0, width=CAMERA_WIDTH, height=CAMERA_HEIGHT)
    c1.undistort("calibration_left.yml", 1)

    # Small delay to prevent first camera freeze
    import time
    time.sleep(0.5)

    c2 = stream.Camera(src=1, width=CAMERA_WIDTH, height=CAMERA_HEIGHT)
    c2.undistort("calibration_right.yml", 1)

    # Initialize trackers
    print("Starting detection trackers...")
    t1 = detectors.Tracker(c1)
    t2 = detectors.Tracker(c2)

    # Initialize coordinate calculator
    print("Initializing 3D coordinate system...")
    coords = Coordinates(
        t2, t1, CAMERA_WIDTH, CAMERA_HEIGHT, "../calibration_left.yml",
        CAMERA_X_OFFSET, CAMERA_Y_OFFSET, CAMERA_Z_OFFSET,
        physical_width, physical_height, MONITOR_WIDTH, MONITOR_HEIGHT
    )

    # Give trackers time to warm up
    time.sleep(1.0)

    # Initialize cursor tracker with Hungarian algorithm
    print("Initializing cursor tracker...")
    cursor_tracker = Cursor(
        coordinate=coords,
        mice_count=MICE_COUNT,
        max_x_dist=MAX_X_DIST,
        max_y_dist=MAX_Y_DIST,
        timeout=TIMEOUT,
        press_threshold=PRESS_THRESHOLD,
        unpress_threshold=UNPRESS_THRESHOLD,
        unpress_frames=UNPRESS_FRAMES
    )

    # Start cursor tracking in separate thread
    Thread(target=cursor_tracker.update, daemon=True).start()

    # Generate unique colors for each mouse
    mouse_colors = generate_unique_colors(MICE_COUNT)

    print("Starting tracked cursor demo... Press ESC to exit")

    # Main display loop
    try:
        while c1.running and c2.running:
            # Create white canvas
            canvas = np.ones((MONITOR_HEIGHT, MONITOR_WIDTH, 3), dtype=np.uint8) * 255

            # Get tracked mice data
            mice_data = cursor_tracker.get_mice_data()

            active_count = 0
            # Draw each tracked mouse
            for mouse_id, position in mice_data.items():
                if position is None:
                    continue

                active_count += 1
                mouse_info = cursor_tracker.mice[mouse_id]

                x = int(position.x)
                y = int(position.y)

                # Get unique color for this mouse
                color = mouse_colors[mouse_id]

                # Check if pressed
                is_pressed = mouse_info['pressed']

                # Check if point is within screen bounds
                if 0 <= x < MONITOR_WIDTH and 0 <= y < MONITOR_HEIGHT:
                    # Draw cursor circle with unique color
                    cv2.circle(canvas, (x, y), 20, color, -1)  # Filled circle

                    # Draw border - red if pressed, black otherwise
                    border_color = (0, 0, 255) if is_pressed else (0, 0, 0)  # BGR format
                    border_thickness = 4 if is_pressed else 2
                    cv2.circle(canvas, (x, y), 22, border_color, border_thickness)

                    # Draw crosshair for precision
                    cv2.line(canvas, (x - 10, y), (x + 10, y), (0, 0, 0), 1)
                    cv2.line(canvas, (x, y - 10), (x, y + 10), (0, 0, 0), 1)

                    # Display mouse ID and coordinates
                    text = f"Mouse {mouse_id}: ({x}, {y})"
                    cv2.putText(canvas, text, (x + 25, y - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

                    # Display pinch distance if available
                    if mouse_info['pinch_distance'] is not None:
                        pinch_text = f"{mouse_info['pinch_distance']*100:.1f}cm"
                        cv2.putText(canvas, pinch_text, (x + 25, y + 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)

                    # Display press status
                    if is_pressed:
                        cv2.putText(canvas, "PRESSED", (x - 30, y + 40),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                else:
                    # Point is out of bounds - show warning
                    print(f"Mouse {mouse_id} position out of bounds: ({x}, {y})")

            canvas = cv2.flip(canvas, 1)
            # Add instruction text
            cv2.putText(canvas, "Tracked Hand Cursor Demo - Press ESC to exit",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            cv2.putText(canvas, f"Active mice: {active_count}/{MICE_COUNT}",
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)

            # Display tracking parameters
            cv2.putText(canvas, f"Press: <{PRESS_THRESHOLD*100:.1f}cm | Unpress: >{UNPRESS_THRESHOLD*100:.1f}cm for {UNPRESS_FRAMES} frames",
                       (10, MONITOR_HEIGHT - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)

            # Display the canvas
            cv2.imshow('Tracked Hand Cursor', canvas)

            # Check for ESC key
            if cv2.waitKey(1) & 0xFF == 27:
                break

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Cleanup
        print("Cleaning up...")
        cursor_tracker.running = False
        coords.running = False
        c1.stop()
        c2.stop()
        cv2.destroyAllWindows()
        print("Done!")


if __name__ == "__main__":
    main()
