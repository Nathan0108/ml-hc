import cv2
import numpy as np
import time

# Camera resolution
CAMERA_WIDTH = 1440
CAMERA_HEIGHT = 960

def main():
    print("Initializing cameras with OpenCV...")

    # Initialize left camera (Camera 0) with V4L2
    cap1 = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap1.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap1.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap1.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap1.set(cv2.CAP_PROP_FPS, 30)
    cap1.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    time.sleep(0.5)

    if not cap1.isOpened():
        print("Error: Could not open camera 0 (Left)")
        return

    # Small delay to prevent first camera freeze
    time.sleep(0.5)

    # Initialize right camera (Camera 2) with V4L2
    cap2 = cv2.VideoCapture(2, cv2.CAP_V4L2)
    cap2.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap2.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap2.set(cv2.CAP_PROP_FPS, 30)
    cap2.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    time.sleep(0.5)

    if not cap2.isOpened():
        print("Error: Could not open camera 2 (Right)")
        cap1.release()
        return
    time.sleep(0.5)

    # Get actual camera properties
    width1 = int(cap1.get(cv2.CAP_PROP_FRAME_WIDTH))
    height1 = int(cap1.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps1 = int(cap1.get(cv2.CAP_PROP_FPS))

    width2 = int(cap2.get(cv2.CAP_PROP_FRAME_WIDTH))
    height2 = int(cap2.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps2 = int(cap2.get(cv2.CAP_PROP_FPS))

    print(f"Camera 0 (Left): {width1}x{height1} @ {fps1}fps")
    print(f"Camera 2 (Right): {width2}x{height2} @ {fps2}fps")
    print("Displaying camera feeds... Press 'q' or ESC to exit")

    # Create named windows
    cv2.namedWindow('Left Camera', cv2.WINDOW_NORMAL)
    cv2.namedWindow('Right Camera', cv2.WINDOW_NORMAL)
    cv2.namedWindow('Combined View', cv2.WINDOW_NORMAL)

    frame_count = 0
    start_time = time.time()

    try:
        while True:
            # Read from both cameras
            ret1, frame1 = cap1.read()
            ret2, frame2 = cap2.read()

            if not ret1:
                print("Warning: Failed to grab frame from camera 0")
                frame1 = np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8)
                cv2.putText(frame1, "Camera 0 Error", (50, CAMERA_HEIGHT//2),
                           cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)

            if not ret2:
                print("Warning: Failed to grab frame from camera 2")
                frame2 = np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8)
                cv2.putText(frame2, "Camera 2 Error", (50, CAMERA_HEIGHT//2),
                           cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)

            # Add labels to frames
            cv2.putText(frame1, "Left Camera", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame2, "Right Camera", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Add FPS counter
            frame_count += 1
            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
                print(f"FPS: {fps:.2f}")

            # Display individual camera windows
            cv2.imshow('Left Camera', frame1)
            cv2.imshow('Right Camera', frame2)

            # Combine frames side by side
            combined = np.hstack([frame1, frame2])
            cv2.imshow('Combined View', combined)

            # Check for quit keys
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 'q' or ESC
                print("Quit signal received")
                break

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Cleanup
        elapsed = time.time() - start_time
        print(f"\nTotal frames: {frame_count}")
        print(f"Total time: {elapsed:.2f}s")
        print(f"Average FPS: {frame_count/elapsed:.2f}" if elapsed > 0 else "N/A")

        print("Cleaning up...")
        cap1.release()
        cap2.release()
        cv2.destroyAllWindows()
        print("Done!")

if __name__ == "__main__":
    main()
