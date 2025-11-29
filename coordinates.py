import math
from utils import Point2D, Point3D
from utils import Calculate
import detectors
import stream
from threading import Thread
import cv2
import time

FPS_MS = 0.033

WRIST = 0
HAND_INDEX = 4
HAND_THUMB = 8
RIGHT_EYE = 0
LEFT_EYE = 1

BASELINE_DISTANCE=0.30

HAND_FILTER = [WRIST, HAND_INDEX, HAND_THUMB]
FACE_FILTER = [RIGHT_EYE, LEFT_EYE]

MAX_FACE_DIST = 1.2

MONITOR_WIDTH = 1920

class Coordinates:
    def __init__(self, left_detector, right_detector, image_width, image_height, calibration_file,
                 camera_x_offset, camera_y_offset, camera_z_offset,
                 physical_width, physical_height, pixel_width, pixel_height):
        self.left_detector = left_detector
        self.right_detector = right_detector
        self.image_width = image_width
        self.image_height = image_height

        self.left_results = None
        self.right_results = None

        self.hand_coords_3d = None
        self.face_coords_3d = None

        self.camera_x_offset = camera_x_offset
        self.camera_y_offset = camera_y_offset
        self.camera_z_offset = camera_z_offset
        self.physical_width = physical_width
        self.physical_height = physical_height
        self.pixel_width = pixel_width
        self.pixel_height = pixel_height


        camera_matrix_left, _ = self.load_coefficients(calibration_file)
        fx = camera_matrix_left[0, 0]
        fy = camera_matrix_left[1, 1]
        cx = camera_matrix_left[0, 2]
        cy = camera_matrix_left[1, 2]

        self.calc =  Calculate(
            focal_length_x=fx,
            focal_length_y=fy,
            baseline_distance=BASELINE_DISTANCE,
            c_x=cx,
            c_y=cy
        )

        self.running = True
        Thread(target=self.update, args=(), daemon=True).start()

    def load_coefficients(self, calibration_file):
        cv_file = cv2.FileStorage(calibration_file, cv2.FILE_STORAGE_READ)
        camera_matrix = cv_file.getNode("K").mat()
        dist_matrix = cv_file.getNode("D").mat()
        cv_file.release()
        return [camera_matrix, dist_matrix]

    def update(self):
        while self.running:
            time.sleep(FPS_MS)
            self.left_results = self.left_detector.get_results().copy()
            self.right_results = self.right_detector.get_results().copy()
            self.process_stereo_detections()
            #print(self.get3DCoordinates())

    def sort_hands(self, hands):
        if not hands:
            return []
        return sorted(hands, key=lambda hand: hand.landmark[WRIST].x)

    def sort_face(self, faces):
        if not faces:
            return []
        return sorted(faces, key=lambda face: face.location_data.relative_keypoints[LEFT_EYE].x)

    def calculate_hand_3d_coordinates(self, hand_left, hand_right):
        coords_3d = {}
        landmark_names = {
            0: 'wrist',
            4: 'thumb_tip',
            8: 'index_tip'
        }

        for idx in HAND_FILTER:
            left_lm = hand_left.landmark[idx]
            right_lm = hand_right.landmark[idx]

            p_left = Point2D(left_lm.x * self.image_width, left_lm.y * self.image_height)
            p_right = Point2D(right_lm.x * self.image_width, right_lm.y * self.image_height)

            point_3d = self.calc.getCoordinatesFrom(p_left, p_right)
            coords_3d[landmark_names[idx]] = point_3d
        return coords_3d

    def extract_eye_positions(self, faces):
        if not faces:
            return None, None
        keypoints = faces.location_data.relative_keypoints

        if len(keypoints) >= 2:
            right_eye = Point2D(
                keypoints[0].x * self.image_width,
                keypoints[0].y * self.image_height
            )
            left_eye = Point2D(
                keypoints[1].x * self.image_width,
                keypoints[1].y * self.image_height
            )
            return left_eye, right_eye

        return None, None

    def calculate_eye_midpoint_3d(self, face_left, face_right):
        if not face_left or not face_right:
            return None

        left_eye_L, right_eye_L = self.extract_eye_positions(face_left)
        left_eye_R, right_eye_R = self.extract_eye_positions(face_right)

        if not all([left_eye_L, right_eye_L, left_eye_R, right_eye_R]):
            return None

        midpoint_left = Point2D(
            (left_eye_L.x + right_eye_L.x) / 2,
            (left_eye_L.y + right_eye_L.y) / 2
        )
        midpoint_right = Point2D(
            (left_eye_R.x + right_eye_R.x) / 2,
            (left_eye_R.y + right_eye_R.y) / 2
        )

        return self.calc.getCoordinatesFrom(p1=midpoint_left, p2=midpoint_right)

    def process_stereo_detections(self):

        hand_coords_3d = {}
        face_coords_3d = {}
        left_hands = self.sort_hands(self.left_results['hands'])
        left_faces = self.sort_face(self.left_results['faces'])
        right_hands = self.sort_hands(self.right_results['hands'])
        right_faces = self.sort_face(self.right_results['faces'])

        if left_hands and right_hands:
            length = min(len(left_hands), len(right_hands))
            for idx in range(length):
                hand_3d = self.calculate_hand_3d_coordinates(left_hands[idx], right_hands[idx])
                hand_coords_3d[f'Hand {idx}'] = hand_3d

        if left_faces and right_faces:
            length = min(len(left_faces), len(right_faces))
            for idx in range(length):
                face_3d = self.calculate_eye_midpoint_3d(left_faces[idx], right_faces[idx])
                face_coords_3d[f'Face {idx}'] = face_3d


        self.hand_coords_3d = hand_coords_3d
        self.face_coords_3d = face_coords_3d

    def get3DCoordinates(self):
        return self.hand_coords_3d, self.face_coords_3d

    def getNearestFace(self, hand_point, face_coords_3d):
        shortest_distance = float('inf')
        best_face = None
        for _, face in face_coords_3d.items():
            dist = hand_point.distance_to(face)
            if dist < shortest_distance and dist < MAX_FACE_DIST:
                shortest_distance = dist
                best_face = face
        return best_face


    def getOnScrenPixels(self):
        points = []
        hand_coords_3d, face_coords_3d = self.get3DCoordinates()
        if not hand_coords_3d or not face_coords_3d:
            return points

        screen_width_m = self.physical_width * 0.0254
        screen_height_m = self.physical_height * 0.0254
        for _, hand in hand_coords_3d.items():

            hand_point = self.calc.getMiddlePoint(hand['thumb_tip'], hand['index_tip'])
            face_point = self.getNearestFace(hand_point, face_coords_3d)
            pinch_dist = self.calc.getEuclideanDistance(hand['thumb_tip'], hand['index_tip'])
            if not face_point:
                continue
            print(f'hand {hand_point} face: {face_point}')


            hand_screen = Point3D(
                hand_point.x - self.camera_x_offset,
                hand_point.y - self.camera_y_offset,
                hand_point.z - self.camera_z_offset
            )
            face_screen = Point3D(
                face_point.x - self.camera_x_offset,
                face_point.y - self.camera_y_offset,
                face_point.z - self.camera_z_offset
            )

            intersection = self.calc.getXYIntersection(face_screen, hand_screen)

            pixel_x = (intersection.x / screen_width_m) * self.pixel_width
            pixel_y = (intersection.y / screen_height_m) * self.pixel_height

            print(Point2D(pixel_x, pixel_y))
            points.append({'position': Point2D(pixel_x, pixel_y), 'pinch_distance': pinch_dist})

        return points
