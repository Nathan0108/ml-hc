import cv2
import numpy as np
import stream
import detectors
import time

# Camera resolution
CAMERA_WIDTH = 1440
CAMERA_HEIGHT = 960

def main():
    print("Initializing cameras...")

    # Initialize left camera
    c1 = stream.Camera(src=0, width=CAMERA_WIDTH, height=CAMERA_HEIGHT)
    c1.undistort("calibration_left.yml", 1)

    # Small delay to prevent first camera freeze
    time.sleep(0.5)

    # Initialize right camera
    c2 = stream.Camera(src=2, width=CAMERA_WIDTH, height=CAMERA_HEIGHT)
    c2.undistort("calibration_right.yml", 1)

    print("Starting detection trackers...")
    t1 = detectors.Tracker(c1)
    t2 = detectors.Tracker(c2)

    # Give trackers time to warm up
    time.sleep(1.0)

    print("Displaying camera feeds... Press ESC to exit")

    try:
        while c1.running and c2.running:
            frames = []

            # Process both cameras
            for idx, (camera, tracker) in enumerate([(c1, t1), (c2, t2)]):
                camera.new_frame.wait(timeout=0.01)
                success, img = camera.read()

                if not success:
                    # Create blank frame if camera read fails
                    img = np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8)
                else:
                    img = img.copy()
                    img.flags.writeable = True

                    # Draw hand landmarks
                    results = tracker.get_results()
                    if results['hands'] is not None:
                        for detection in results['hands']:
                            detectors.mp_drawing.draw_landmarks(
                                img,
                                detection,
                                detectors.mp_hands.HAND_CONNECTIONS,
                                detectors.mp_drawing_styles.get_default_hand_landmarks_style(),
                                detectors.mp_drawing_styles.get_default_hand_connections_style())

                    # Draw face detections
                    if results['faces'] is not None:
                        for detection in results['faces']:
                            detectors.mp_drawing.draw_detection(img, detection)

                    # Add camera label
                    label = "Left Camera" if idx == 0 else "Right Camera"
                    cv2.putText(img, label, (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Flip horizontally for mirror view
                img = cv2.flip(img, 1)
                frames.append(img)

            # Combine frames side by side
            combined = np.hstack(frames)

            # Display combined frame
            cv2.imshow('Camera Test - Left | Right', combined)

            # Check for ESC key
            if cv2.waitKey(1) & 0xFF == 27:
                break

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Cleanup
        print("Cleaning up...")
        t1.stop()
        t2.stop()
        c1.stop()
        c2.stop()
        cv2.destroyAllWindows()
        print("Done!")

if __name__ == "__main__":
    main()
