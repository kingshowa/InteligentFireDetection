import cv2
import numpy as np
import time
from collections import deque


class FireDetector:
    """
    Robust fire detector with:
    - Color segmentation
    - Motion verification
    - Shape analysis
    - Temporal smoothing
    - False-positive suppression
    """

    def __init__(self,
                 min_fire_duration=1.0,
                 min_fire_area=500,
                 confidence_threshold=0.6,
                 smoothing_window=10,
                 persistence_ratio=0.7,
                 hsv_lower=(0, 120, 70),
                 hsv_upper=(35, 255, 255)):

        # Parameters
        self.min_fire_duration = min_fire_duration
        self.min_fire_area = min_fire_area
        self.confidence_threshold = confidence_threshold
        self.persistence_ratio = persistence_ratio

        self.hsv_lower = np.array(hsv_lower)
        self.hsv_upper = np.array(hsv_upper)

        # Temporal buffers
        self.confidence_buffer = deque(maxlen=smoothing_window)
        self.fire_presence_buffer = deque(maxlen=smoothing_window)

        # State
        self.fire_start_time = None
        self.alert_sent = False

        # Motion detector
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True
        )

    # -------------------------------------------------
    # MAIN PIPELINE
    # -------------------------------------------------
    def process_frame(self, frame, timestamp):

        fire_mask = self._detect_fire_color(frame)
        motion_mask = self._detect_motion(frame)

        combined = cv2.bitwise_and(fire_mask, motion_mask)
        boxes, total_area = self._extract_regions(combined)

        raw_confidence = min(1.0, total_area / (self.min_fire_area * 3))
        fire_present = total_area >= self.min_fire_area

        # Update temporal buffers
        self.confidence_buffer.append(raw_confidence)
        self.fire_presence_buffer.append(1 if fire_present else 0)

        smoothed_confidence = np.mean(self.confidence_buffer)
        persistence = np.mean(self.fire_presence_buffer)

        # Reset if fire disappears
        if not fire_present:
            self.fire_start_time = None
            self.alert_sent = False
            return False, smoothed_confidence, []

        # Temporal consistency
        if not self._check_temporal_consistency(timestamp):
            return False, smoothed_confidence, boxes

        # Final decision gate
        if (persistence >= self.persistence_ratio and
                smoothed_confidence >= self.confidence_threshold):

            return True, smoothed_confidence, boxes

        return False, smoothed_confidence, boxes

    # -------------------------------------------------
    # INTERNAL STAGES
    # -------------------------------------------------
    def _detect_fire_color(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        return cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)

    def _detect_motion(self, frame):
        fg = self.bg_subtractor.apply(frame)
        _, fg = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        return fg

    def _extract_regions(self, mask):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        boxes = []
        total_area = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.min_fire_area:
                continue

            # Shape filtering (false-positive suppression)
            hull = cv2.convexHull(cnt)
            solidity = area / (cv2.contourArea(hull) + 1e-5)

            if solidity > 0.9:
                continue  # Likely solid object, not fire

            x, y, w, h = cv2.boundingRect(cnt)
            boxes.append((x, y, w, h))
            total_area += area

        return boxes, total_area

    def _check_temporal_consistency(self, timestamp):
        if self.fire_start_time is None:
            self.fire_start_time = timestamp
            return False

        return (timestamp - self.fire_start_time) >= self.min_fire_duration

    # -------------------------------------------------
    # RESET
    # -------------------------------------------------
    def reset(self):
        self.fire_start_time = None
        self.alert_sent = False
        self.confidence_buffer.clear()
        self.fire_presence_buffer.clear()
