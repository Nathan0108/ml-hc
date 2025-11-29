import coordinates
import time
import numpy as np
from scipy.optimize import linear_sum_assignment

from coordinates import Coordinates


class Cursor:
    def __init__(self, coordinate, mice_count, max_x_dist, max_y_dist, timeout,
                 press_threshold, unpress_threshold, unpress_frames):

        self.mice_count = mice_count
        self.max_x_dist = max_x_dist
        self.max_y_dist = max_y_dist
        self.timeout = timeout
        self.press_threshold = press_threshold
        self.unpress_threshold = unpress_threshold
        self.unpress_frames = unpress_frames

        self.coordinate = coordinate

        self.mice = {i: {'position': None, 'pressed': False, 'time': None,
                         'unpress_counter': 0, 'pinch_distance': None}
                     for i in range(mice_count)}

        self.running = True

    def update(self):
        while self.running:
            time.sleep(0.01)
            self.free_mice()

            coords = self.coordinate.getOnScrenPixels()
            if not coords:
                continue

            free_mice = [label for label, data in self.mice.items()
                         if data['position'] is None]

            active_mice = [label for label, data in self.mice.items()
                           if data['position'] is not None]

            assigned_hands = set()

            # Active mice move to nearest hand within range
            for mouse_label in active_mice:
                mouse_pos = self.mice[mouse_label]['position']
                closest_hand_idx = None
                closest_distance = float('inf')

                for hand_idx, hand_data in enumerate(coords):
                    hand_pos = hand_data['position']
                    distance = mouse_pos.distance_to(hand_pos)

                    x_diff = abs(mouse_pos.x - hand_pos.x)
                    y_diff = abs(mouse_pos.y - hand_pos.y)

                    # Only consider hands within threshold
                    if x_diff <= self.max_x_dist and y_diff <= self.max_y_dist:
                        if distance < closest_distance:
                            closest_distance = distance
                            closest_hand_idx = hand_idx

                # Update position only if hand found within range
                if closest_hand_idx is not None:
                    self.mice[mouse_label]['position'] = coords[closest_hand_idx]['position']
                    self.mice[mouse_label]['pinch_distance'] = coords[closest_hand_idx]['pinch_distance']
                    self.mice[mouse_label]['time'] = time.time()
                    assigned_hands.add(closest_hand_idx)
                # If no hand in range, mouse stays still (no action)

            # Step 2: Free mice teleport to nearest unused hand
            for mouse_label in free_mice:
                closest_hand_idx = None
                closest_distance = float('inf')

                # Find nearest hand that hasn't been assigned to an active mouse
                for hand_idx, hand_data in enumerate(coords):
                    if hand_idx in assigned_hands:
                        continue
                    closest_hand_idx = hand_idx
                    break

                # Assign to unused hand if available
                if closest_hand_idx is not None:
                    self.mice[mouse_label]['position'] = coords[closest_hand_idx]['position']
                    self.mice[mouse_label]['pinch_distance'] = coords[closest_hand_idx]['pinch_distance']
                    self.mice[mouse_label]['time'] = time.time()
                    assigned_hands.add(closest_hand_idx)
                # If no hands left, free mouse doesn't move

            self.update_pressed()

    def update_pressed(self):
        for label, data in self.mice.items():
            if data['pinch_distance'] is None:
                continue

            pinch_dist = data['pinch_distance']

            if pinch_dist < self.press_threshold:
                data['pressed'] = True
                data['unpress_counter'] = 0

            elif pinch_dist >= self.unpress_threshold:
                data['unpress_counter'] += 1

                if data['unpress_counter'] >= self.unpress_frames:
                    data['pressed'] = False
                    data['unpress_counter'] = 0

            else:
                data['unpress_counter'] = 0

    def free_mice(self):
        for label, data in self.mice.items():
            if data['position'] is None and data['time'] is None:
                continue
            if time.time() - data['time'] > self.timeout:
                data['position'] = None
                data['pressed'] = False
                data['time'] = time.time()

    def get_mice_data(self):
        return {label: data['position'] for label, data in self.mice.items()}



