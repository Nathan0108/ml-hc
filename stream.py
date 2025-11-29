import cv2
import numpy as np
from threading import Thread, Lock, Event
import time
import sys

class Camera:
    def __init__(self, src, width, height):
        if sys.platform.startswith("linux"):
            backend = cv2.CAP_V4L2
        elif sys.platform == "darwin":
            backend = cv2.CAP_AVFOUNDATION
        else:
            backend = cv2.CAP_ANY

        self.width = width
        self.height = height
        self.cap = cv2.VideoCapture(src, apiPreference=backend)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        if not self.cap.isOpened():
            raise RuntimeError(f'Camera {src} could not be opened.')

        self.running = True
        self.image = None
        self.success = False
        self.lock = Lock()
        self.new_frame = Event()

        Thread(target=self.update, args=(), daemon=True).start()

    def undistort(self, calibration_file, alpha):
        w = self.width
        h = self.height
        mtx, dist = self.load_coefficients(calibration_file)
        self.newcameramtx, self.roi = cv2.getOptimalNewCameraMatrix(
            mtx, dist, (w, h), alpha, (w, h))
        self.mapx, self.mapy = cv2.initUndistortRectifyMap(
            mtx, dist, None, self.newcameramtx, (w, h), cv2.CV_32FC1)
        print('Undistorted camera matrix and distortion coefficients')

    def load_coefficients(self, calibration_file):
        cv_file = cv2.FileStorage(calibration_file, cv2.FILE_STORAGE_READ)
        camera_matrix = cv_file.getNode("K").mat()
        dist_matrix = cv_file.getNode("D").mat()
        cv_file.release()
        return [camera_matrix, dist_matrix]

    def update(self):
        while self.running:
            success, image = self.cap.read()
            if not success:
                continue
            with self.lock:
                self.image = image
                self.success = success
            self.new_frame.set()
            time.sleep(0.01)
            self.new_frame.clear()

    def read(self):
        with self.lock:
            return self.success, self.image

    def stop(self):
        self.running = False