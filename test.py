import cv2
import os
import time
from datetime import datetime
import argparse

def test_camera(headless=True, record=True, duration=None, output_dir="./recordings"):
    """
    Tests cameras connected to the Linux system with optimization and video compression.

    Args:
        headless (bool): Run without displaying video (optimal for VM)
        record (bool): Record video with H.264 compression
        duration (int): Recording duration in seconds (None for continuous)
        output_dir (str): Directory to save recordings
    """
    # Create output directory if recording
    if record:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Camera 1 setup with V4L2 optimization
    cap = cv2.VideoCapture(0, apiPreference=cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1440)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer for lower latency

    # Camera 2 setup with V4L2 optimization
    cap2 = cv2.VideoCapture(2, apiPreference=cv2.CAP_V4L2)
    cap2.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap2.set(cv2.CAP_PROP_FRAME_WIDTH, 1440)
    cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
    cap2.set(cv2.CAP_PROP_FPS, 30)
    cap2.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print(f"Error: Could not open camera with index 0.")
        return

    if not cap2.isOpened():
        print(f"Error: Could not open camera with index 2.")
        cap.release()
        return

    # Get actual camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    print(f"Camera 1 opened: {width}x{height} @ {fps}fps")
    print(f"Camera 2 opened: {width}x{height} @ {fps}fps")

    # Setup video writers with H.264 compression
    video_writer = None
    video_writer2 = None

    if record:
        # H.264 codec with optimized settings for VM
        fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264
        output_path = os.path.join(output_dir, f"camera1_{timestamp}.mp4")
        output_path2 = os.path.join(output_dir, f"camera2_{timestamp}.mp4")

        video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        video_writer2 = cv2.VideoWriter(output_path2, fourcc, fps, (width, height))

        if not video_writer.isOpened() or not video_writer2.isOpened():
            print("Warning: Could not initialize H.264 encoder, trying XVID...")
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            video_writer2 = cv2.VideoWriter(output_path2, fourcc, fps, (width, height))

        print(f"Recording to: {output_path}")
        print(f"Recording to: {output_path2}")

    print(f"Running in {'headless' if headless else 'display'} mode")
    if duration:
        print(f"Recording for {duration} seconds. Press Ctrl+C to stop early.")
    else:
        print("Recording continuously. Press Ctrl+C to stop.")

    start_time = time.time()
    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()
            ret2, frame2 = cap2.read()

            if not ret or not ret2:
                print("Error: Failed to grab frame.")
                break

            # Record frames
            if record and video_writer and video_writer2:
                video_writer.write(frame)
                video_writer2.write(frame2)

            # Display if not headless
            if not headless:
                cv2.imshow('Camera 1 Feed', frame)
                cv2.imshow('Camera 2 Feed', frame2)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Quit signal received.")
                    break

            frame_count += 1

            # Progress indicator for headless mode
            if headless and frame_count % 30 == 0:
                elapsed = time.time() - start_time
                print(f"Frames: {frame_count}, Elapsed: {elapsed:.1f}s, FPS: {frame_count/elapsed:.1f}")

            # Check duration limit
            if duration and (time.time() - start_time) >= duration:
                print(f"Duration limit of {duration}s reached.")
                break

    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    finally:
        # Cleanup
        elapsed = time.time() - start_time
        print(f"\nTotal frames: {frame_count}")
        print(f"Total time: {elapsed:.2f}s")
        print(f"Average FPS: {frame_count/elapsed:.2f}")

        cap.release()
        cap2.release()

        if video_writer:
            video_writer.release()
        if video_writer2:
            video_writer2.release()

        if not headless:
            cv2.destroyAllWindows()

        print("Cameras released successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test cameras on Linux VM with video compression')
    parser.add_argument('--display', action='store_true', help='Display video (not headless)')
    parser.add_argument('--no-record', action='store_true', help='Disable recording')
    parser.add_argument('--duration', type=int, default=None, help='Recording duration in seconds')
    parser.add_argument('--output-dir', type=str, default='./recordings', help='Output directory for recordings')

    args = parser.parse_args()

    test_camera(
        headless=not args.display,
        record=not args.no_record,
        duration=args.duration,
        output_dir=args.output_dir
    )