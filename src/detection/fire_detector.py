import cv2
import numpy as np
import time


class FireDetector:
    """
    OpenCV-based fire detection with:
    - Color segmentation
    - Motion verification
    - Temporal confirmation
    """

    def __init__(self,
                 min_fire_duration=1.0,
                 min_fire_area=500,
                 hsv_lower=(0, 120, 70),
                 hsv_upper=(35, 255, 255)):

        # Parameters
        self.min_fire_duration = min_fire_duration
        self.min_fire_area = min_fire_area
        self.hsv_lower = np.array(hsv_lower)
        self.hsv_upper = np.array(hsv_upper)

        # State
        self.fire_start_time = None
        self.alert_sent = False
        self.last_event = None

        # Motion detector
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True
        )

    # ----------------------------
    # MAIN PIPELINE
    # ----------------------------
    def process_frame(self, frame, timestamp):
        """
        Returns:
        - fire_detected (bool)
        - confidence (float)
        - bounding_boxes (list)
        """

        fire_mask = self._detect_fire_color(frame)
        motion_mask = self._detect_motion(frame)

        combined = cv2.bitwise_and(fire_mask, motion_mask)
        boxes, total_area = self._extract_regions(combined)

        if total_area < self.min_fire_area:
            self.fire_start_time = None
            return False, 0.0, []

        confidence = min(1.0, total_area / (self.min_fire_area * 3))

        if self._check_temporal_consistency(timestamp):
            if not self.alert_sent:
                self.alert_sent = True
                self.last_event = {
                    "timestamp": timestamp,
                    "confidence": confidence,
                    "boxes": boxes
                }
            return True, confidence, boxes

        return False, confidence, boxes

    # ----------------------------
    # INTERNAL STAGES
    # ----------------------------
    def _detect_fire_color(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)
        return mask

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

            x, y, w, h = cv2.boundingRect(cnt)
            boxes.append((x, y, w, h))
            total_area += area

        return boxes, total_area

    def _check_temporal_consistency(self, timestamp):
        if self.fire_start_time is None:
            self.fire_start_time = timestamp
            return False

        return (timestamp - self.fire_start_time) >= self.min_fire_duration

    # ----------------------------
    # RESET
    # ----------------------------
    def reset(self):
        self.fire_start_time = None
        self.alert_sent = False
        self.last_event = None
