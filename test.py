import cv2

def test_camera(camera_index=0):
    """
    Tests a camera connected to the system.

    Args:
        camera_index (int): The index of the camera to test (e.g., 0 for default).
    """
    cap = cv2.VideoCapture(camera_index, apiPreference=cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1440)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
    cap.set(cv2.CAP_PROP_FPS, 30)

    cap2 = cv2.VideoCapture(camera_index, apiPreference=cv2.CAP_V4L2)
    cap2.set(cv2.CAP_PROP_FRAME_WIDTH, 1440)
    cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
    cap2.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        print(f"Error: Could not open camera with index {camera_index}.")
        return

    if not cap2.isOpened():
        print(f"Error: Could not open camera with index {camera_index}.")
        return

    print("Camera opened successfully. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        ret2, frame2 = cap2.read()

        if not ret:
            print("Error: Failed to grab frame.")
            break

        cv2.imshow('Camera Feed', frame)
        cv2.imshow('Camera 2 Feed', frame2)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cap2.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # You can change the camera_index if you have multiple cameras
    test_camera(2)