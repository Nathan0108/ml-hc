import cv2
import numpy as np

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

for i in range(10):  # Skip first few frames
    cap.read()

ret, frame = cap.read()
print(f"Read success: {ret}")
print(f"Frame shape: {frame.shape if ret else 'None'}")
print(f"Frame dtype: {frame.dtype if ret else 'None'}")

if ret and frame is not None:
    # Check if frame is valid (not all zeros or corrupted)
    if np.any(frame):
        cv2.imwrite('test_frame.png', frame)
        print("✓ Frame saved successfully")
        print(f"Min/Max pixel values: {frame.min()}/{frame.max()}")
    else:
        print("✗ Frame is all zeros (corrupted)")
else:
    print("✗ Failed to read frame")

cap.release()