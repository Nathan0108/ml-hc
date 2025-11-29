import cv2
import numpy as np
import math
import stream
import detectors
from coordinates import Coordinates

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

def get_monitor_dimensions(diagonal_length, ar1, ar2):
    """Calculate monitor physical dimensions in inches from diagonal and aspect ratio"""
    k = diagonal_length / math.sqrt(ar1 ** 2 + ar2 ** 2)
    return ar1 * k, ar2 * k

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
    coords = Coordinates(t2, t1, CAMERA_WIDTH, CAMERA_HEIGHT, "../calibration_left.yml")

    # Give trackers time to warm up
    time.sleep(1.0)

    print("Starting cursor demo... Press ESC to exit")

    # Main display loop
    try:
        while c1.running and c2.running:
            # Create white canvas
            canvas = np.ones((MONITOR_HEIGHT, MONITOR_WIDTH, 3), dtype=np.uint8) * 255

            # Get hand cursors with positions and pinch distances
            hand_cursors = coords.getOnScrenPixels(
                CAMERA_X_OFFSET,
                CAMERA_Y_OFFSET,
                CAMERA_Z_OFFSET,
                physical_width,
                physical_height,
                MONITOR_WIDTH,
                MONITOR_HEIGHT
            )

            # Draw circles at each hand position
            for cursor in hand_cursors:
                point = cursor['position']
                pinch_dist = cursor['pinch_distance']

                x = int(point.x)
                y = int(point.y)

                # Determine if pinched (distance < 0.02 meters = 2cm)
                is_pinched = pinch_dist < 0.04

                # Choose color: red if pinched, blue otherwise
                color = (0, 0, 255) if is_pinched else (255, 0, 0)  # BGR format

                # Check if point is within screen bounds
                if 0 <= x < MONITOR_WIDTH and 0 <= y < MONITOR_HEIGHT:
                    # Draw cursor circle
                    cv2.circle(canvas, (x, y), 20, color, -1)  # Filled circle
                    cv2.circle(canvas, (x, y), 22, (0, 0, 0), 2)  # Black outline

                    # Draw crosshair for precision
                    cv2.line(canvas, (x - 10, y), (x + 10, y), (0, 0, 0), 1)
                    cv2.line(canvas, (x, y - 10), (x, y + 10), (0, 0, 0), 1)

                    # Display coordinates and pinch distance
                    text = f"({x}, {y}) {pinch_dist*100:.1f}cm"
                    cv2.putText(canvas, text, (x + 25, y - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

                    # Display pinch status
                    if is_pinched:
                        cv2.putText(canvas, "PINCHED", (x - 30, y + 40),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                else:
                    # Point is out of bounds - show warning
                    print(f"Hand position out of bounds: ({x}, {y})")
            canvas = cv2.flip(canvas, 1)
            # Add instruction text
            cv2.putText(canvas, "Hand Cursor Demo - Press ESC to exit",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            cv2.putText(canvas, f"Hands detected: {len(hand_cursors)}",
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)

            # Display the canvas
            cv2.imshow('Hand Cursor', canvas)

            # Check for ESC key
            if cv2.waitKey(1) & 0xFF == 27:
                break

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Cleanup
        print("Cleaning up...")
        coords.running = False
        c1.stop()
        c2.stop()
        cv2.destroyAllWindows()
        print("Done!")

if __name__ == "__main__":
    main()
