import time

import cv2
import mediapipe as mp
import stream
from threading import Thread
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands
mp_face_detection = mp.solutions.face_detection


class Tracker:
    def __init__(self, camera):
        self.camera = camera
        self.running = True
        self.results = {'hands': None, 'faces': None}

        Thread(target=self.hand_update, args=(), daemon=True).start()
        Thread(target=self.face_update, args=(), daemon=True).start()
    def hand_update(self):
        with mp_hands.Hands(
                max_num_hands=4,
                model_complexity=0,
                min_detection_confidence=0.3,
                min_tracking_confidence=0.5) as hands:
            while self.running:
                self.camera.new_frame.wait(timeout=0.01)
                success, image = self.camera.read()
                if not success:
                    continue
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self.results['hands'] = hands.process(image).multi_hand_landmarks

    def face_update(self):
        with mp_face_detection.FaceDetection(
                model_selection=1, min_detection_confidence=0.5) as face:
            while self.running:
                self.camera.new_frame.wait(timeout=0.01)
                success, image = self.camera.read()
                if not success:
                    continue
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self.results['faces'] = face.process(image).detections
    def get_results(self):
        return self.results

    def stop(self):
        self.running = False

def view(c1, t1, c2, t2):
    while c1.running and c2.running:
        for idx, (c, t) in enumerate([(c1, t1), (c2, t2)]):
            c.new_frame.wait(timeout=0.01)
            success, img = c.read()
            if not success:
                continue
            img = img.copy()
            img.flags.writeable = True

            results = t.get_results()
            if results['hands'] is not None:
                for detection in results['hands']:
                    mp_drawing.draw_landmarks(
                        img,
                        detection,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style())

            if results['faces'] is not None:
                for detection in results['faces']:
                    mp_drawing.draw_detection(img, detection)
            cv2.imshow(f'{idx}', cv2.flip(img, 1))

        if cv2.waitKey(5) & 0xFF == 27:
            break
