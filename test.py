import cv2

def test_camera(camera_index=0):
    """
    Tests a camera connected to the system.

    Args:
        camera_index (int): The index of the camera to test (e.g., 0 for default).
    """
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"Error: Could not open camera with index {camera_index}.")
        return

    print("Camera opened successfully. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error: Failed to grab frame.")
            break

        cv2.imshow('Camera Feed', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # You can change the camera_index if you have multiple cameras
    test_camera(0)