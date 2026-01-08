import threading
import cv2
import time

from video_input.video_stream import VideoInput
from detection.fire_detector import FireDetector
from ui.dashboard import FireDetectionDashboard


class FireDetectionController:
    """
    Orchestrates VideoInput, FireDetector, and Dashboard
    """

    def __init__(self, dashboard: FireDetectionDashboard):
        self.dashboard = dashboard
        self.video_input = None
        self.detector = FireDetector()
        self.running = False
        self.worker = None

    # ---------------------------------------------
    # START STREAM
    # ---------------------------------------------
    def start_stream(self, source_type, source_value):
        self.stop_stream()

        try:
            self.video_input = VideoInput(source_type, source_value)
            self.video_input.start()
        except Exception as e:
            self.dashboard.log_event(f" Stream error: {e}")
            return

        self.running = True
        self.worker = threading.Thread(target=self._processing_loop, daemon=True)
        self.worker.start()

        self.dashboard.log_event(f"▶ Stream started ({source_type})")

    # ---------------------------------------------
    # MAIN LOOP
    # ---------------------------------------------
    def _processing_loop(self):
        while self.running:
            frame, timestamp = self.video_input.read()

            if frame is None:
                break

            fire, confidence, boxes = self.detector.process_frame(frame, timestamp)

            for (x, y, w, h) in boxes:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

            if fire:
                cv2.putText(
                    frame,
                    f" FIRE ({confidence:.2f})",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )
                self.dashboard.trigger_fire_from_thread(confidence)

            self.dashboard.update_frame_from_thread(frame)
            time.sleep(0.03)

        self.stop_stream()

    # ---------------------------------------------
    # STOP STREAM
    # ---------------------------------------------
    def stop_stream(self):
        self.running = False

        if self.video_input:
            self.video_input.stop()
            self.video_input = None

        self.detector.reset()

    def deactivate_buzzer(self):
        self.detector.reset()
        self.dashboard.deactivate_buzzer()


# ---------------------------------------------
# APPLICATION ENTRY POINT
# ---------------------------------------------
def main():
    dashboard = FireDetectionDashboard()
    controller = FireDetectionController(dashboard)

    dashboard.on_start_stream = controller.start_stream
    dashboard.stop_system = controller.stop_stream
    dashboard.deactivate_buzzer = controller.deactivate_buzzer

    dashboard.mainloop()


if __name__ == "__main__":
    main()
